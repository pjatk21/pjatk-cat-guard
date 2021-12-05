from hikari import User, Role, Embed
from lightbulb import Plugin, commands, implements, command, add_checks, Check, option
from lightbulb.context import Context
from mongoengine import Q
# from gadoneko.util import ColorPalette

from discordcat.embed_factory import embed_success
from gadoneko.checks import staff_only
from shared.colors import RESULT
from shared.documents import TrustedUser, GuildConfiguration, UserIdentity, VerificationMethod
from shared.formatting import code_block

plugin = Plugin('Admin')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.command()
@add_checks(Check(staff_only))
@command('admin', 'Przypisuje numer studenta do twojego konta discord')
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
        'staff': UserIdentity(
            guild_id=ctx.get_guild().id, guild_name=ctx.get_guild().name, user_id=ctx.user.id, user_name=str(ctx.user)
        ),
        'comment': ctx.options.comment
    }
    trust.save()

    embed = embed_success(
        "Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę `/manage self`"
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
    GuildConfiguration.objects(
        guild_id=ctx.guild_id
    ).update_one(
        trusted_role_id=ctx.options.trust.id, upsert=True
    )
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    await ctx.respond(f'Skonfigurowano!\n```json\n{conf.to_json()}```')


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
