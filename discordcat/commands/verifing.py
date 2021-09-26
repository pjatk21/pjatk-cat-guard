import re
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from hikari import User
from lightbulb import guild_only
from lightbulb.slash_commands import SlashCommand, Option, SlashCommandContext
from sendgrid import Mail, From

from common.codes import VerificationCode
from discordcat.checks import verified_only, unverified_only, superusers_only, guild_configured, operator_only
from discordcat.embed_factory import embed_info, embed_success
from discordcat.services import db, sg, env

verified = db["verified"]
codes = db["codes"]
manual_verification = db["manual_verification"]


class VerifyCommand(SlashCommand):
    name = "verify"
    description = "Weryfikuje twoje konto"
    s: str = Option("Twój numer studenta (np. s73120)")

    async def callback(self, context: SlashCommandContext):
        match = re.match(r"^s\d{5}$", context.options["s"].value)

        if match is None:
            await context.respond("Twój numer studenta nie jest poprawny! Czy dodałeś **s**")
            return

        if datetime.now(timezone.utc) - context.author.created_at < timedelta(weeks=24):
            await context.respond(
                "Konta młodsze niż 6 miesięcy wymagają dodatkowej weryfikacji. Skontaktuj się z administracją."
            )
            manual_verification.insert_one(
                {
                    "discord_id": context.author.id,
                    "discord_name": str(context.author),
                    "account_created": context.author.created_at,
                }
            )
            return

        student_id = match.string

        target_email = f"{student_id}@pjwstk.edu.pl"

        validation_code = VerificationCode.create(
            str(context.author), target_email, context.author.id, context.guild_id
        )

        codes.insert_one(asdict(validation_code))

        mail = Mail(
            from_email=From("catguard@kpostek.dev", name="ガード猫"),
            to_emails=[target_email],
        )
        mail.dynamic_template_data = {
            "verificationUrl": f"{env.get('VERIFICATION_URL')}verify/{validation_code.code}",
            "discordTag": context.author.username,
        }
        mail.template_id = "d-589f1fd50a244a189b8b1539e688a41c"
        sg.send(mail)

        embed = embed_info("Sprawdź swojego **studenckiego** maila! "
                           "**Masz 15 minut** na kliknięcie w link!")
        embed.title = "Wysłano email z linkiem potwierdzającym weryfikację!"
        await context.respond(embed=embed)

    checks = [guild_only, guild_configured, unverified_only]


class VerifyForceCommand(SlashCommand):
    name = 'verify-force'
    description = 'Wymusza weryfikację użytkownika'

    user: User = Option("Użytkownik")
    s: str = Option("Numer studenta")

    async def callback(self, context: SlashCommandContext):
        user = context.options["user"].value
        s = context.options["s"].value
        when = datetime.now()
        s_mail = f"{s}@pjwstk.edu.pl"

        db["verified"].update_one(
            {"discord_id": user},
            {"$set": {
                "student_mail": s_mail,
                "discord_id": user,
                "when": when,
                "guild_id": context.guild_id,
                "verified_by": "operator",
                "operator": {
                    "name": str(context.author),
                    "id": context.author.id
                }
            }},
            upsert=True
        )

        verfied_role = db["roles"].find_one({"guild_id": context.guild_id})
        await context.bot.rest.add_role_to_member(
            context.guild_id, user, verfied_role["role_id"]
        )

        embed = embed_success("Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę `/manage self` ")
        embed.add_field("Serwer", context.get_guild().name)
        embed.add_field("Data weryfikacji", when.isoformat())
        embed.add_field("Operator weryfikacji", str(context.author))

        await (await context.bot.rest.fetch_user(user)).send(embed=embed)

        await context.respond("Zweryfikowano użytkownika.")

    checks = [operator_only]
