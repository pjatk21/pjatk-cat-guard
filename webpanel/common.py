import os

from starlette.templating import Jinja2Templates
# from starlette_discord import DiscordOAuthClient

templates = Jinja2Templates(directory="templates")
# discord_oauth = DiscordOAuthClient(
#     os.getenv('DISCORD_CLIENTID'),
#     os.getenv('DISCORD_SECRET'),
#     os.getenv('DISCORD_REDIRECT'),
# )

