import re
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from lightbulb import guild_only
from lightbulb.slash_commands import SlashCommand, Option, SlashCommandContext
from sendgrid import Mail, From

from common.codes import VerificationCode
from .checks import verified_only, unverified_only, superusers_only, guild_configured
from .embed_factory import embed_info
from .services import db, sg, env

verified = db["verified"]
codes = db["codes"]
manual_verification = db["manual_verification"]


class VerifyCommand(SlashCommand):
    name = "verify"
    description = "Verifies you"
    s: str = Option("Your index number (like s21337)")

    async def callback(self, context: SlashCommandContext):
        match = re.match(r"^s\d{5}$", context.options["s"].value)

        if match is None:
            await context.respond("Twój numer studenta nie jest poprawny! Czy dodałeś ****")
            return

        if datetime.now(timezone.utc) - context.author.created_at < timedelta(weeks=24):
            await context.respond(
                "Twoje konto jest podejrzanie świeże. Twoje konto wymaga manualnej weryfikacji!. "
                "Skontaktuj się z administracją!"
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
            "verificationCode": validation_code.code,
            "discordTag": context.author.username,
        }
        mail.template_id = "d-589f1fd50a244a189b8b1539e688a41c"
        sg.send(mail)

        embed = embed_info("Sprawdź swojego **studenckiego** maila! "
                           "**Masz 15 minut** na kliknięcie w link!")
        embed.title = "Wysłano email z linkiem potwierdzającym weryfikację!"
        await context.respond(embed=embed)

    checks = [guild_only, guild_configured, unverified_only]
