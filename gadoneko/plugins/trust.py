import hashlib
import os
import random
from datetime import datetime

from hikari import Guild, User, Embed
from hikari.events import MemberCreateEvent
from lightbulb import command, implements, commands, add_checks, Plugin, Check, guild_only
from lightbulb.context import Context

from gadoneko.checks import untrusted_only, trusted_only, guild_configured
from shared.colors import INFO
from shared.documents import UserIdentity, TrustedUser, GuildConfiguration, VerificationRequest

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
@command('verify', 'Przypisuje numer studenta do twojego konta discord')
@implements(commands.SlashCommand)
async def verify(ctx: Context):
    link = start_verification_flow(ctx.get_guild(), ctx.user)

    await ctx.author.send(f"Link do logowania: {os.getenv('VERIFICATION_URL')}verify/{link.code}")
    await ctx.respond("Wysłano link do logowania na DM.")


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


@plugin.command()
@add_checks(guild_only, Check(guild_configured), Check(trusted_only))
@command('manage', 'Zarządzaj swoim numerem studenta')
@implements(commands.SlashCommandGroup)
async def manage(ctx: Context):
    pass


@manage.child()
@command('sign-out', 'Wypisz swój numer studenta z bazy danych', inherit_checks=True)
@implements(commands.SlashSubCommand)
async def sign_out(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    trust: TrustedUser = TrustedUser.objects(identity__user_id=ctx.user.id).first()
    trust.delete()
    await ctx.member.remove_role(conf.trusted_role_id, reason='User requested sign out.')
    await ctx.respond('Usunąłem twój numer studenta z naszej bazy danych.')
