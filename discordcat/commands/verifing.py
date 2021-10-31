import random
import hashlib
from datetime import datetime

from hikari import User
from hikari.errors import ForbiddenError
from lightbulb import guild_only
from lightbulb.slash_commands import SlashCommand, Option, SlashCommandContext

from discordcat.checks import (
    unverified_only,
    guild_configured,
    operator_only,
)
from discordcat.embed_factory import embed_success, embed_error
from discordcat.services import db, env

verified = db["verified"]
codes = db["codes"]
manual_verification = db["manual_verification"]


class VerifyCommand(SlashCommand):
    name = "verify"
    description = "Weryfikuje twoje konto"

    async def callback(self, context: SlashCommandContext):
        linking_secret_hash = hashlib.sha256()
        linking_secret_hash.update(random.randbytes(512))
        linking_secret = linking_secret_hash.hexdigest()[:4] + "-" + linking_secret_hash.hexdigest()[4:8]

        db["link"].update_one(
            {
                "discord_id": context.author.id,
                "guild_id": context.guild_id,
            },
            {
                "$set": {
                    "secret": linking_secret,
                }
            },
            upsert=True,
        )

        await context.author.send(
            f"Link do logowania: {env.get('VERIFICATION_URL')}oauth/{linking_secret}"
        )

        await context.respond("Wysłano link do logowania na DM.")

    checks = [guild_only, guild_configured, unverified_only]


class VerifyForceCommand(SlashCommand):
    name = "verify-force"
    description = "Wymusza weryfikację użytkownika"

    user: User = Option("Użytkownik")
    s: str = Option("Numer studenta")

    async def callback(self, context: SlashCommandContext):
        user = context.options.user
        s = context.options.s
        when = datetime.now()
        s_mail = f"{s}@pjwstk.edu.pl"

        db["verified"].update_one(
            {"discord_id": user},
            {
                "$set": {
                    "student_mail": s_mail,
                    "discord_id": user,
                    "when": when,
                    "guild_id": context.guild_id,
                    "verified_by": "operator",
                    "operator": {"name": str(context.author), "id": context.author.id},
                }
            },
            upsert=True,
        )

        verfied_role = db["roles"].find_one({"guild_id": context.guild_id})
        try:
            await context.bot.rest.add_role_to_member(
                context.guild_id, user, verfied_role["role_id"]
            )
        except ForbiddenError:
            await context.respond(
                embed=embed_error(
                    "Uprawnienia bota, są poniżej nadawanej rangi! "
                    "Rola bota powinna być nad grupą nadawaną"
                )
            )
            return

        embed = embed_success(
            "Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę `/manage self` "
        )
        embed.add_field("Serwer", context.get_guild().name)
        embed.add_field("Data weryfikacji", when.isoformat())
        embed.add_field("Operator weryfikacji", str(context.author))

        await (await context.bot.rest.fetch_user(user)).send(embed=embed)

        await context.respond("Zweryfikowano użytkownika.")

    checks = [operator_only]
