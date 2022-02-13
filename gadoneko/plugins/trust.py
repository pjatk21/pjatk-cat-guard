import hashlib
import os
import random
from datetime import datetime

from hikari import Guild, User, Embed
from hikari.events import MemberCreateEvent, BanCreateEvent, MemberDeleteEvent
from lightbulb import command, implements, commands, add_checks, Plugin, Check, guild_only
from lightbulb.context import Context
from mongoengine import DoesNotExist

from gadoneko.checks import untrusted_only, trusted_only, guild_configured
from shared.colors import INFO
from shared.documents import UserIdentity, TrustedUser, GuildConfiguration, VerificationRequest, VerificationState

plugin = Plugin('Trust')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


def start_verification_flow(guild: Guild, user: User):
    linking_secret_hash = hashlib.sha256()
    linking_secret_hash.update(random.randbytes(512))
    linking_secret = str(guild.id)[:3] + "-" + linking_secret_hash.hexdigest()[:3] + "-" + linking_secret_hash.hexdigest()[3:6] + "-" + linking_secret_hash.hexdigest()[6:9]

    vr = VerificationRequest()
    vr.identity = UserIdentity()
    vr.identity.guild_id = guild.id
    vr.identity.user_id = user.id
    vr.identity.user_name = str(user)
    vr.identity.guild_name = guild.name
    vr.code = linking_secret
    vr.save()

    return vr


@plugin.command()
@add_checks(guild_only, Check(guild_configured), Check(untrusted_only))
@command('verify', 'Przypisuje numer studenta do twojego konta discord', ephemeral=True)
@implements(commands.SlashCommand)
async def verify(ctx: Context):
    link = start_verification_flow(ctx.get_guild(), ctx.user)

    await ctx.respond(f"Link do logowania: {os.getenv('VERIFICATION_URL')}verify/{link.code}")


@plugin.listener(MemberCreateEvent)
async def auto_verify(event: MemberCreateEvent):
    link = start_verification_flow(event.get_guild(), event.user)

    embed = Embed(
        title='Hej 👋',
        description='Na tym serwerze jest wymagane, aby powiązać numer studencki z tożsamością na discordzie. '
                    'Dopóki tego nie dokonasz, część kanałów zostanie przed tobą ukryta. '
                    'Taki proces weryfikacji nie trwa dłużej niż minutę.',
        color=INFO, timestamp=datetime.now().astimezone()
    ).add_field(
        'Twój link do weryfikacji', f"{os.getenv('VERIFICATION_URL')}verify/{link.code}"
    )

    await event.user.send(embed=embed)


@plugin.listener(BanCreateEvent)
async def ban_cleanup(event: BanCreateEvent):
    try:
        tu = TrustedUser.objects.get(identity__user_id=event.user.id, identity__guild_id=event.guild_id)
        vr: VerificationRequest = VerificationRequest.objects.get(trust=tu)
    except DoesNotExist:
        return

    vr.state = VerificationState.BANNED
    vr.save()
    tu.delete()


@plugin.listener(MemberDeleteEvent)
async def kick_leave_cleanup(event: MemberDeleteEvent):
    try:
        tu = TrustedUser.objects.get(identity__user_id=event.user_id, identity__guild_id=event.guild_id)
    except DoesNotExist:
        return

    tu.delete()


@plugin.command()
@add_checks(guild_only, Check(guild_configured), Check(trusted_only))
@command('manage', 'Zarządzaj swoim numerem studenta')
@implements(commands.SlashCommandGroup)
async def manage(ctx: Context):
    pass


@manage.child()
@command('sign-out', 'Wypisz swój numer studenta z bazy danych', inherit_checks=True, ephemeral=True)
@implements(commands.SlashSubCommand)
async def sign_out(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    trust: TrustedUser = TrustedUser.objects(identity__user_id=ctx.user.id).first()
    trust.delete()
    await ctx.member.remove_role(conf.trusted_role_id, reason='User requested sign out.')
    await ctx.respond('Usunąłem twój numer studenta z naszej bazy danych.')
