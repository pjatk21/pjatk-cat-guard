import os

from hikari import RESTApp, Embed, HikariError
from mongoengine import DoesNotExist
from sendgrid import SendGridAPIClient, Mail
from starlette.requests import Request

from shared.colors import *
from shared.documents import VerificationRequest, TrustedUser, GuildConfiguration, Reviewer, VerificationState


async def apply_trusted_role(tu: TrustedUser, conf: GuildConfiguration):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        user = await bot.fetch_user(tu.identity.user_id)
        await bot.add_role_to_member(
            conf.guild_id, user, conf.trusted_role_id, reason='Marked as trusted!'
        )

        embed = Embed(
            title='Zrobione!',
            description="Pomyślnie zweryfikowano! Możesz zarządzać weryfikacją poprzez komendę `/manage sign-out`",
            color=OK
        )
        embed.add_field("Data weryfikacji", tu.when.isoformat())
        embed.add_field("Powiązany numer studenta", tu.student_number)
        embed.add_field("Metoda weryfikacji", tu.verification_method.value)

        await user.send(embed=embed)


async def removed_trusted_role(vr: VerificationRequest):
    try:
        conf: GuildConfiguration = GuildConfiguration.objects.get(guild_id=vr.identity.guild_id)
    except DoesNotExist:
        return

    takedowns = [conf.trusted_role_id, 872855213525061662, 874665726886170695, 872854951964049448, 874668279984185374]

    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        try:
            for td in takedowns:
                await bot.remove_role_from_member(
                    conf.guild_id, vr.identity.user_id, td, reason=f'Trust removal requested by operator.'
                )
        except HikariError:
            pass


async def send_trust_confirmation(vr: VerificationRequest):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    mail = Mail(
        from_email=('gadoneko@free.itny.me', 'ガード猫'),
        to_emails=vr.google.email
    )
    mail.dynamic_template_data = {
        'who': vr.google.name,
        'student_num': vr.trust.student_number,
        'guild': vr.identity.guild_name,
        'discord': vr.identity.user_name,
    }
    mail.template_id = 'd-409b6361287f46a7949f030b399b4817'
    sg.send(mail)


async def send_rejection_mail(vr: VerificationRequest, message: str):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    mail = Mail(
        from_email=('gadoneko@free.itny.me', 'ガード猫'),
        to_emails=vr.google.email
    )
    mail.dynamic_template_data = {
        'guild': vr.identity.guild_name,
        'reason': message
    }
    mail.template_id = 'd-774ffd7fe61e457b85b6674cc1d0e001'
    sg.send(mail)


async def send_rejection_dm(vr: VerificationRequest, message: str):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        user = await bot.fetch_user(vr.identity.user_id)

        embed = Embed(
            title='O nie!',
            description=f"Nie udało się pomyślnie zweryfikować twojego konta z powodu: {message}",
            color=WARN
        )

        await user.send(embed=embed)


async def notify_requested_id(vr: VerificationRequest, request: Request):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        user = await bot.fetch_user(vr.identity.user_id)
        await user.send(
            embed=Embed(
                title='Papers please!',
                description=f'Weryfikujący poprosił o wysłanie legitymacji studenckiej w celu potwierdzenia tożsamości, odwiedź {request.url_for("verify:form", secret=vr.code)} aby przesłać dokument.',
                url=request.url_for('verify:form', secret=vr.code),
                colour=WARN
            )
        )
        # await user.send(f'Weryfikujący poprosił o wysłanie legitymacji studenckiej w celu potwierdzenia tożsamości, odwiedź {os.getenv("VERIFICATION_URL")}verify/{vr.code} aby przesłać dokument.')


async def notify_requested_id_mail(vr: VerificationRequest, request: Request):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    mail = Mail(
        from_email=('gadoneko@free.itny.me', 'ガード猫'),
        to_emails=vr.google.email
    )
    mail.dynamic_template_data = {
        'link': request.url_for('verify:form', secret=vr.code),
    }
    mail.template_id = 'd-0f04cd5c573b4ed39065dfabd889214b'
    sg.send(mail)


async def notify_reviewers(vr: VerificationRequest, request: Request):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        rs = Reviewer.objects(identity__guild_id=vr.identity.guild_id)
        user = await bot.fetch_user(vr.identity.user_id)

        for reviewer in [await bot.fetch_user(r.identity.user_id) for r in rs]:
            await reviewer.send(
                embed=Embed(
                    title='Nowa osoba do weryfikacji!',
                    description=f'{vr.identity.user_name} oczekuje na weryfikację!',
                    url=request.url_for('admin:review', rid=vr.id),
                    colour=user.accent_colour,
                ).set_thumbnail(user.avatar_url)
            )


async def notify_reviewer_docs(vr: VerificationRequest, request: Request):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        rs = Reviewer.objects.get(id=vr.reviewer.id)
        reviewer = await bot.fetch_user(rs.identity.user_id)
        await reviewer.send(
            embed=Embed(
                title='Dokumenty do weryfikacji!',
                description=f'{vr.identity.user_name} oczekuje na weryfikację dokumentów!',
                url=request.url_for('admin:review', rid=vr.id),
                colour=INFO
            )
        )


def remove_duplicate_requests(vr: VerificationRequest):
    duplicates = VerificationRequest.objects(identity=vr.identity, id__ne=vr.id, state__nin=[VerificationState.REJECTED, VerificationState.ACCEPTED, VerificationState.PENDING])
    duplicates.delete()


def notify_bypass_email(email: str, vr: VerificationRequest, request: Request):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    mail = Mail(
        from_email=('gadoneko@free.itny.me', 'ガード猫'),
        to_emails=email
    )
    mail.dynamic_template_data = {
        'link': request.url_for('verify:form', secret=vr.code),
        'student_num': email,
        'guild': vr.identity.guild_name,
        'discord': vr.identity.user_name,
    }
    mail.template_id = 'd-07aa4f50084d4f81bba9ab46c625ff21'
    sg.send(mail)
