import hashlib
import os
import random

from lightbulb.context import Context
from lightbulb import command, implements, commands, add_checks, Plugin, Check
from lightbulb.checks import guild_only

from gadoneko.checks import untrusted_only
from shared.documents import VerificationLink, UserIdentity

plugin = Plugin('Trust')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.command()
@add_checks(Check(untrusted_only), guild_only)
@command('verify', 'Przypisuje numer studenta do twojego konta discord')
@implements(commands.SlashCommand)
async def verify(ctx: Context):
    linking_secret_hash = hashlib.sha256()
    linking_secret_hash.update(random.randbytes(512))
    linking_secret = linking_secret_hash.hexdigest()[:4] + "-" + linking_secret_hash.hexdigest()[4:8]

    link = VerificationLink()
    link.identity = UserIdentity()
    link.identity.guild_id = ctx.get_guild().id
    link.identity.user_id = ctx.user.id
    link.identity.user_name = str(ctx.user)
    link.identity.guild_name = ctx.get_guild().name
    link.secret_code = linking_secret
    link.save()

    await ctx.author.send(f"Link do logowania: {os.getenv('VERIFICATION_URL')}oauth/{linking_secret}")
    await ctx.respond("Wysłano link do logowania na DM.")
