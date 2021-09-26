import json
import platform
from datetime import datetime

from lightbulb import SlashCommand, SlashCommandContext

from ..checks import superusers_only
from ..services import db


class SystemCheckCommand(SlashCommand):
    name = 'system'
    description = 'Pokazuje stan systemu'

    async def callback(self, context: SlashCommandContext):
        response = {
            "time": datetime.now().isoformat(),
            "platform": platform.platform(),
            "mongo": {
                "name": db.name,
                "client": str(db.client)
            }
        }

        await context.respond(f"```json\n{json.dumps(response, indent=2)}\n```")

    checks = [superusers_only]
