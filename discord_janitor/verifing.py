import os
import re
from dataclasses import asdict

from dotenv import load_dotenv
from hikari import Embed
from lightbulb.slash_commands import SlashCommand, Option, SlashCommandContext
from sendgrid import Mail, From

from common.codes import VerificationCode
from .services import db, sg

load_dotenv()

env = os.environ

registered = db["registered"]
codes = db["codes"]


class VerifyCommand(SlashCommand):
    name = "verify"
    description = "Verifies you"
    s: str = Option("Your index number (like s21337)")

    async def callback(self, context: SlashCommandContext):
        match = re.match(r"^s\d{5}$", context.options["s"].value)

        if match is None:
            await context.respond("Twój numer studenta nie jest poprawny!")
            return

        student_id = match.string

        if registered.find_one(
            {"student_id": student_id}
        ) is not None or registered.find_one({"discord_id": context.author.id}):
            await context.respond(
                "Te konto lub numer studenta już były wykorzystywane do rejestracji!"
            )
            return

        target_email = f"{student_id}@pjwstk.edu.pl"

        validation_code = VerificationCode.create(
            str(context.author), target_email, context.author.id
        )

        codes.insert_one(asdict(validation_code))

        mail = Mail(
            from_email=From("discord-verification@kpostek.dev", name="Weryfikacja"),
            to_emails=[target_email],
        )
        mail.dynamic_template_data = {
            "verificationUrl": f"{env.get('VERIFICATION_URL')}{validation_code.code}",
            "verificationCode": validation_code.code,
            "discordTag": context.author.username,
        }
        mail.template_id = "d-589f1fd50a244a189b8b1539e688a41c"
        sg.send(mail)

        embed = Embed()
        embed.title = "Wysłano weryfikację!"
        embed.add_field("Mail docelowy", target_email)
        embed.set_footer(
            text="Jeżeli link w adresie nie działa, skopiuj kod i wykonaj komendę /use-code"
        )

        await context.respond(embed=embed)


class FallbackVerification(SlashCommand):
    name = "use-code"
    description = "Alternative method for authentication"
    code: str = Option("Verification code")

    async def callback(self, context: SlashCommandContext):
        code = context.options["code"].value

        trusted_code = codes.find_one({"code": code})

        if trusted_code is None:
            await context.author.send("Kod nie istnieje!")
            return

        del trusted_code["_id"]
        trusted_code = VerificationCode(**trusted_code)

        if trusted_code.has_expired:
            await context.author.send("Kod wygasł, spróbuj ponownie!")
            return

        await context.respond("Zweryfikowano i dodano rangę!")

        codes.delete_many({"who": trusted_code.who})
        codes.delete_many({"email": trusted_code.email})

        registered.insert_one(
            {"student_id": trusted_code.who, "discord_id": context.author.id}
        )
