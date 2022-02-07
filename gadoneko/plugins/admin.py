import asyncio
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from hikari import User, Role, Embed, Member, ForbiddenError, GuildMessageCreateEvent
from lightbulb import Plugin, commands, implements, command, add_checks, Check, option, BotApp
from lightbulb.checks import guild_only
from lightbulb.context import Context
from mongoengine import Q
from mongoengine.errors import NotUniqueError, DoesNotExist

from gadoneko.checks import staff_only, bot_owner_only
from gadoneko.util.permissions import update_permissions
from shared.colors import RESULT, OK, INFO
from shared.documents import TrustedUser, GuildConfiguration, UserIdentity, VerificationMethod, CronHealthCheck, \
    Reviewer, VerificationRequest
from shared.formatting import code_block
from shared.progressbar import ProgressBar
from shared.util import chunks

plugin = Plugin('Admin')
logger = logging.getLogger('gadoneko.admin')


def load(bot: BotApp):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.command()
@add_checks(guild_only, Check(staff_only))
@command('adm', 'Zestaw narzędzi administracyjnych.')
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
    if ctx.options.member:
        GuildConfiguration.objects(guild_id=ctx.guild_id).update(add_to_set__additional_staff=ctx.options.member.id)
    elif ctx.options.role:
        GuildConfiguration.objects(guild_id=ctx.guild_id).update(add_to_set__additional_staff_roles=ctx.options.role.id)
    else:
        await ctx.respond('Nie podałeś żadnego argumentu cepie')
        return

    await update_permissions(ctx, GuildConfiguration.objects(guild_id=ctx.guild_id).first())
    await ctx.respond('OK')


@staff.child()
@option('member', 'Rola dla zaufanych użytkowników', type=Member, required=False)
@option('role', 'Rola dla zaufanych użytkowników', type=Role, required=False)
@command('del', 'przypisuje grupę lub użytkownika do personelu', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def staff_remove(ctx: Context):
    if ctx.options.member:
        GuildConfiguration.objects(guild_id=ctx.guild_id).update(pull__additional_staff=ctx.options.member.id)
    elif ctx.options.role:
        GuildConfiguration.objects(guild_id=ctx.guild_id).update(pull__additional_staff_roles=ctx.options.role.id)
    else:
        await ctx.respond('Nie podałeś żadnego argumentu cepie')
        return

    await update_permissions(ctx, GuildConfiguration.objects(guild_id=ctx.guild_id).first())
    await ctx.respond('OK')


@staff.child()
@command('ls', 'przypisuje grupę lub użytkownika do personelu', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def staff_ls(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    embed = Embed(title='Uprawnieni do obslugi bot\'a')
    members = [
        f'<@{m}>' for m in conf.additional_staff  # Mention users
    ]
    groups = [
        f'<@&{r}>' for r in conf.additional_staff_roles  # Mention roles
    ]

    if len(members):
        embed.add_field(
            'Użytkownicy', '\n'.join(members), inline=True
        )

    if len(groups):
        embed.add_field(
            'Grupy', '\n'.join(groups), inline=True
        )

    await ctx.respond(embed=embed)


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

    try:
        tu: TrustedUser = TrustedUser.objects(qs).get()
    except DoesNotExist:
        await ctx.respond('Nie ma takiego użytkownika w bazie')
        return

    member = await ctx.bot.rest.fetch_member(ctx.guild_id, tu.identity.user_id)
    embeds = [
        Embed(
            title=f'Użytkownik {member}',
            description=f'{member.mention} był weryfikowany przy użyciu `{tu.verification_method.value}`',
            color=member.accent_color
        ).set_thumbnail(
            member.avatar_url
        ).add_field(
            'Numer studenta', tu.student_number
        ).add_field(
            'Zweryfikowany', tu.when.isoformat()
        )
    ]

    if tu.verification_method == VerificationMethod.REVIEW:
        vr: VerificationRequest = VerificationRequest.objects(trust=tu).get()
        reviewer = await ctx.bot.rest.fetch_user(vr.reviewer.identity.user_id)
        embeds.append(
            Embed(
                color=INFO
            ).add_field(
                'Sprawdzający', reviewer.mention
            ).add_field(
                'Imię i nazwisko', vr.google.name
            ).add_field(
                'Email', vr.google.email
            ).add_field(
                'Forma weryfikacyjna', f'https://free.itny.me/admin/review/{vr.id}'
            ).add_field(
                'Czy sprawdzono dokumenty', 'Tak' if vr.photos.ready else 'Nie'
            )
        )

    await ctx.respond(embeds=embeds)


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


@admin.child()
@option('role', 'Rola użytkowników, którzy mają zostać wyciszeni', type=Role)
@option('length', 'czas w minutach na, który bot ma wyciszyć grupę', type=float)
@command('blackout', 'Dokonuje wyciszenia', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def blackout(ctx: Context):
    role: Role = ctx.options.role
    members = [user for user in await ctx.bot.rest.fetch_members(ctx.guild_id) if role.id in user.role_ids]
    if os.getenv('ENV') == 'dev':
        members_chunks: tuple[tuple[Member]] = tuple(chunks(members, 2))
    else:
        members_chunks: tuple[tuple[Member]] = tuple(chunks(members, 12))
    response = await ctx.respond(f'Rozpoczynam blackout dla {len(members)} użytkowników.')
    blackout_for = datetime.now().astimezone() + timedelta(minutes=ctx.options.length)
    pb = ProgressBar(len(members_chunks))

    async def timeout_member(mem: Member):
        try:
            await mem.edit(
                communication_disabled_until=blackout_for,
                reason=f'Requested blackout for {role.name} by {ctx.author.username}'
            )
        except ForbiddenError:
            logger.warning(f'Insufficient permissions to timeout {mem.username}')

    for i, chunk in enumerate(members_chunks):
        await asyncio.gather(*[
            timeout_member(member) for member in chunk
        ])
        pb.update((i+1)/len(members_chunks))
        await response.edit(str(pb))

    await response.edit(f'Zakończono uciszanie `{role.name}`, cisza potrwa do {blackout_for.isoformat()}')


@admin.child()
@option('action', 'wybierz co zamierzasz zrobić', choices=['download', 'upload'])
@command('static', 'Zapytanie do bazy danych', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def update(ctx: Context):
    match ctx.options.action:
        case 'download':
            await ctx.respond("Podaj nazwę pliku!")
            filename: GuildMessageCreateEvent = await ctx.bot.wait_for(GuildMessageCreateEvent, 30, lambda x: x.channel_id == ctx.channel_id and ctx.author == x.author)
            path_string_safe = re.match(r"^[^/][\w/]+(\.\w+)+$", filename.content)
            if path_string_safe:
                await ctx.bot.rest.create_message(
                    ctx.channel_id,
                    attachment=f'static/{path_string_safe.string}'
                )
        case 'upload':
            await ctx.respond("Wyślij pliki")
            files_message: GuildMessageCreateEvent = await ctx.bot.wait_for(GuildMessageCreateEvent, 30, lambda x: x.channel_id == ctx.channel_id and ctx.author == x.author)
            for att in files_message.message.attachments:
                path_string_safe = re.match(r"^[^/][\w/]+(\.\w+)+$", att.filename)
                if path_string_safe:
                    path = Path(f'static/{path_string_safe.string}')
                    with open(path, 'wb') as f:
                        data = await att.read()
                        f.write(data)
                        await ctx.bot.rest.create_message(
                            ctx.channel_id,
                            f'Wpisano plik {path.absolute()}!'
                        )
        case _:
            await ctx.respond('huh???')


@admin.child()
@add_checks(guild_only, Check(bot_owner_only))
@option('persona', 'Rola użytkowników, którzy mają zostać wyciszeni', type=Member)
@command('reviewer', 'Mianuje na weryfikatora')
@implements(commands.SlashSubCommand)
async def add_reviewer(ctx: Context):
    try:
        r = Reviewer()
        i = UserIdentity()
        i.guild_name = ctx.get_guild().name
        i.guild_id = ctx.guild_id
        i.user_name = str(ctx.options.persona)
        i.user_id = ctx.options.persona.id
        r.identity = i
        r.save()
        await ctx.respond(f'Dodano {ctx.options.persona.mention} jako sprawdzającego!')
    except NotUniqueError:
        await ctx.respond('już jest ale ok')
