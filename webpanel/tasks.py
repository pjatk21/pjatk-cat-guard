import os
import re

from hikari import RESTApp, Embed

from shared.colors import OK
from shared.documents import VerificationRequest, TrustedUser, VerificationMethod, GuildConfiguration


async def apply_trusted_role(tu: TrustedUser, conf: GuildConfiguration):
    async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
        user = await bot.fetch_user(tu.identity.user_id)
        await bot.add_role_to_member(
            conf.guild_id, user, conf.trusted_role_id
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
