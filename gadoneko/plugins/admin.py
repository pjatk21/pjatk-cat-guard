import subprocess

from hikari import User, Role, Embed, Member, CommandPermission, CommandPermissionType
from lightbulb import Plugin, commands, implements, command, add_checks, Check, option, BotApp, LightbulbStartedEvent
from lightbulb.checks import guild_only
from lightbulb.context import Context
from mongoengine import Q

from gadoneko.checks import staff_only, bot_owner_only
from gadoneko.util.permissions import update_permissions
from shared.colors import RESULT, OK
from shared.documents import TrustedUser, GuildConfiguration, UserIdentity, VerificationMethod, CronHealthCheck
from shared.formatting import code_block

plugin = Plugin('Admin')


def load(bot: BotApp):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.command()
@add_checks(guild_only, Check(staff_only))
@command('adm', 'Zestaw narzędzi administarcyjnych.')
@implements(commands.SlashCommandGroup)
def admin():
    pass


@admin.child()
@option('comment', 'Dodatkowy komentarz', required=False)
@option('user', 'Docelowy użytkownik', type=User)
@option('ns', 'Numer studenta, podawać wraz z "s"')
@command('verify', 'Wymusza przypisanie numeru studenta do wskazanego użytkownika', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def verify(ctx: Context):
    person: User = ctx.options.user

    guild_conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    await ctx.bot.rest.add_role_to_member(
        ctx.guild_id, person, guild_conf.trusted_role_id
    )

    trust = TrustedUser()
    trust.identity = UserIdentity(
        guild_id=ctx.get_guild().id, guild_name=ctx.get_guild().name, user_id=person.id, user_name=str(person)
    )
    trust.student_number = ctx.options.ns
    trust.verification_method = VerificationMethod.ROLE_ENFORCED
    trust.verification_context = {
        'staff': UserIdentity.from_context(ctx),
        'comment': ctx.options.comment
    }
    trust.save()

    embed = Embed(
        title='Zrobione!',
        description="Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę `/manage sign-out`",
        color=OK
    )
    embed.add_field("Data weryfikacji", trust.when.isoformat())
    embed.add_field("Powiązany numer studenta", trust.student_number)
    embed.add_field("Metoda weryfikacji", "Wymuszona przez wywołanie komendy")
    embed.add_field("Weryfikujacy", str(ctx.user))
    embed.set_footer("W przypadku niezgodności danych, zgłoś się do administracji")

    await person.send(embed=embed)
    await ctx.respond(embed=embed)


@admin.child()
@option('trust', 'Rola dla zaufanych użytkowników', type=Role)
@command('init', 'Dokonuje inicjalizacji', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def init(ctx: Context):
    # Add objects to the db
    GuildConfiguration.objects(
        guild_id=ctx.guild_id
    ).update_one(
        trusted_role_id=ctx.options.trust.id, upsert=True
    )
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    await ctx.respond(f'Zapisano!\n```json\n{conf.to_json()}```')

    await update_permissions(ctx, conf)


@admin.child()
@command('staff', 'zarządza personelem', inherit_checks=True)
@implements(commands.SlashSubGroup)
def staff():
    pass


@staff.child()
@option('member', 'Rola dla zaufanych użytkowników', type=Member, required=False)
@option('role', 'Rola dla zaufanych użytkowników', type=Role, required=False)
@command('add', 'przypisuje grupę lub użytkownika do personelu', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def staff_add(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).get()

    if ctx.options.member:
        conf.additional_staff.append(ctx.options.member.id)
    elif ctx.options.role:
        conf.additional_staff_roles.append(ctx.options.role.id)
    else:
        await ctx.respond('Nie podałeś żadnego argumentu cepie')
        return

    conf.save()
    await update_permissions(ctx, conf)
    await ctx.respond('OK')


@staff.child()
@option('member', 'Rola dla zaufanych użytkowników', type=Member, required=False)
@option('role', 'Rola dla zaufanych użytkowników', type=Role, required=False)
@command('del', 'przypisuje grupę lub użytkownika do personelu', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def staff_remove(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).get()

    if ctx.options.member:
        conf.additional_staff = [m for m in conf.additional_staff if m != ctx.options.member.id]
    elif ctx.options.role:
        conf.additional_staff_roles = [r for r in conf.additional_staff_roles if r != ctx.options.role.id]
    else:
        await ctx.respond('Nie podałeś żadnego argumentu cepie')
        return

    conf.save()
    await update_permissions(ctx, conf)
    await ctx.respond('OK')


@admin.child()
@option('by_user', 'Szukaj według użytkownika', required=False, type=User)
@option('by_ns', 'Szukaj według numeru studenta', required=False)
# @option('after_date', 'Szukaj zweryfikowanych po wskazanej dacie (ISO format)', required=False)
# @option('before_date', 'Szukaj zweryfikowanych przed wskazaną datą (ISO format)', required=False)
@command('query', 'Zapytanie do bazy danych', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def query(ctx: Context):
    qs = Q(identity__guild_id=ctx.guild_id)

    if ctx.options.by_user:
        qs &= Q(identity__user_id=ctx.options.by_user.id)
    if ctx.options.by_ns:
        qs &= Q(student_number=ctx.options.by_ns)

    results = TrustedUser.objects(qs)
    embed = Embed(description=code_block(results.to_json(indent=2)), color=RESULT)
    await ctx.respond(embed=embed)


@admin.child()
@add_checks(Check(bot_owner_only))
@command('pkg', 'Pokazuje paczki bota')
@implements(commands.SlashSubCommand)
async def env_info(ctx: Context):
    em_pkg = Embed(color=RESULT)
    em_pkg.description = code_block(
        subprocess.check_output(
            ['pip', 'list']
        ).decode()[:4000])
    await ctx.respond(embed=em_pkg)


@admin.child()
@add_checks(guild_only, Check(bot_owner_only))
@command('cron-health', 'Ustawia wiadomość z statusem, działania CRON')
@implements(commands.SlashSubCommand)
async def cron_health(ctx: Context):
    widget_like = await ctx.bot.rest.create_message(
        ctx.get_channel().id, "Widget pojawi się tutaj!"
    )
    CronHealthCheck.objects(identity=UserIdentity.from_context(ctx)).update_one(
        upsert=True, widget_message_id=widget_like.id, widget_channel_id=ctx.get_channel().id
    )
    await ctx.respond('Ustawiono widget CRON!')
