import os
import re
from dataclasses import asdict

from dotenv import load_dotenv
from hikari import Embed
from lightbulb import Bot
from lightbulb.slash_commands import SlashCommand, Option, SlashCommandContext
from pymongo import MongoClient
from sendgrid import SendGridAPIClient, Mail, From

from common.codes import VerificationCode

load_dotenv()

env = os.environ

bot = Bot(token=env.get("DISCORD_TOKEN"), slash_commands_only=True)
sg = SendGridAPIClient(env.get("SENDGRID_APIKEY"))
mongo = MongoClient(env.get("MONGODB_URL"))
db = mongo["verifications"]


class VerifyCommand(SlashCommand):
    name = "verify"
    description = "Verifies you"
    s: str = Option("Your index number (like s21337)")

    async def callback(self, context: SlashCommandContext):
        match = re.match(r"^s\d{5}$", context.options["s"].value)

        if match is None:
            await context.respond("Twój numer studenta nie jest poprawny!")
            return

        student_index = match.string

        target_email = f"{student_index}@pjwstk.edu.pl"

        validation_code = VerificationCode.create(
            str(context.author), target_email, context.author.id
        )
        codes = db["codes"]
        codes.insert_one(asdict(validation_code))

        mail = Mail(
            from_email=From("discord-verification@kpostek.dev", name="Weryfikacja"),
            to_emails=[target_email],
        )
        mail.dynamic_template_data = {
            "verificationUrl": f"http://127.0.0.1:8000/{validation_code.code}",
            "verificationCode": validation_code.code,
            "discordTag": context.author.username,
        }
        mail.template_id = "d-589f1fd50a244a189b8b1539e688a41c"
        sg.send(mail)

        embed = Embed()
        embed.title = "Wysłano weryfikację!"
        embed.add_field("Mail docelowy", target_email)
        embed.set_footer(text="Jeżeli link w adresie nie działa, skopiuj kod i wykonaj komendę /use-code")

        await context.respond(embed=embed)


class FallbackVerification(SlashCommand):
    name = 'use-code'
    description = 'Alternative method for authentication'
    code: str = Option('Verification code')

    async def callback(self, context: SlashCommandContext):
        codes = db["codes"]
        code = context.options["code"].value

        trusted_code = codes.find_one({"code": code})

        del trusted_code["_id"]
        trusted_code = VerificationCode(**trusted_code)

        if trusted_code.has_expired:
            await context.author.send("Kod wygasł, spróbuj ponownie!")
            return

        codes.delete_many({"who": trusted_code.who})
        codes.delete_many({"email": trusted_code.email})

        await context.author.send("Zweryfikowano i dodano rangę!")


bot.add_slash_command(VerifyCommand)
bot.add_slash_command(FallbackVerification)

bot.run()
