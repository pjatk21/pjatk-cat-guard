import re
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from lightbulb.slash_commands import SlashCommand, Option, SlashCommandContext
from sendgrid import Mail, From

from common.codes import VerificationCode
from .checks import verified_only, unverified_only, superusers_only
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
            await context.respond("Twój numer studenta nie jest poprawny!")
            return

        if datetime.now(timezone.utc) - context.author.created_at < timedelta(weeks=24):
            await context.respond(
                "Twoje konto jest podejrzanie świeże. Twoje konto wymaga manualnej weryfikacji!"
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
            from_email=From("discord-verification@kpostek.dev", name="Weryfikacja"),
            to_emails=[target_email],
        )
        mail.dynamic_template_data = {
            "verificationUrl": f"{env.get('VERIFICATION_URL')}verify/{validation_code.code}",
            "verificationCode": validation_code.code,
            "discordTag": context.author.username,
        }
        mail.template_id = "d-589f1fd50a244a189b8b1539e688a41c"
        sg.send(mail)

        embed = embed_info("Wysłano email z linkiem potwierdzającym weryfikację!")
        await context.author.send(f"UWAGA MAŁY `*****`! MASZ 15 MINUT, ŻEBY OTWORZYĆ {target_email} I KLIKNĄĆ W TEN `*******` LINK")
        await context.respond(embed=embed)

    checks = [unverified_only]


class InvalidateCommand(SlashCommand):
    name = "invalidate"
    description = "aaaaa"

    async def callback(self, context: SlashCommandContext):
        verified.delete_one({"discord_id": context.author.id})
        await context.member.remove_role(
            db["roles"].find_one({"guild_id": context.guild_id})["role_id"]
        )
        await context.respond("Unieważniono")

    checks = [verified_only]


class AboutMeCommand(SlashCommand):
    name = "aboutme"
    description = "Pokazuje informacje o tobie."

    async def callback(self, context: SlashCommandContext):
        him = verified.find_one({"discord_id": context.author.id})
        embed = embed_info(
            "Wraz z opuszczeniem serwera, te dane zostaną usunięte. Miej to na uwadze."
        )
        embed.title = "Informacje o " + str(context.author)
        embed.add_field("Połączony adres email (i numer studenta)", him["student_mail"])
        embed.add_field("Data weryfikacji", him["when"])
        if not him["about-ip"].get("bogon"):
            embed.add_field("Lokalizacja", him["about-ip"]["city"])
            embed.add_field("ISP", him["about-ip"]["org"])
        else:
            embed.add_field("Sieć lokalna", him["about-ip"]["ip"])

        await context.respond("Wysłano szczególy na DM")
        await context.author.send(embed=embed)

    checks = [verified_only]
