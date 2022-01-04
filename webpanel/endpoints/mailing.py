import os
from io import StringIO

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from markdownify import markdownify
from hikari import RESTApp, Embed
from shared.documents import ParsedMail

from shared.colors import INFO


class MailFetcher(HTTPEndpoint):
    async def post(self, request: Request):
        mail = await request.form()
        text = markdownify(mail['html'], conevrt=['b', 'i', 'u', 's', 'strike'])

        ParsedMail(**mail).save()  # Just dump mail into db lol, i love NoSQL

        async with RESTApp().acquire(os.getenv("DISCORD_TOKEN"), "Bot") as bot:
            embed = Embed(
                    title=f"{mail['subject']}",
                    color=INFO,
                ).set_footer(text=f'Od {mail["from"]} do {mail["to"]}')

            if len(text) > 3500:
                embed.description = text[:1000] + '...'
                mm = await bot.create_message(
                    os.getenv('DISCORD_MAIL', 893027233650847764),
                    embed=embed,
                    attachment=StringIO(text),
                )
            else:
                embed.description = text
                mm = await bot.create_message(
                    os.getenv('DISCORD_MAIL', 893027233650847764),
                    embed=embed,
                )

        return PlainTextResponse(str(mm.id))


routes = [
    Route('/receive', MailFetcher)
]
