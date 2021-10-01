import json
import platform
from datetime import datetime

from lightbulb import SlashCommand, SlashCommandContext

from ..checks import superusers_only
from ..services import db


class SystemCheckCommand(SlashCommand):
    name = "system"
    description = "Pokazuje stan systemu"

    async def callback(self, context: SlashCommandContext):
        from pipenv.project import Project

        response = {
            "time": datetime.now().isoformat(),
            "platform": platform.platform(),
            "mongo": {"name": db.name, "client": str(db.client)},
            "packages": str(Project().packages),
            "runtime": {
                "packages": list(
                    sorted([str(p) for p in Project().installed_packages])
                ),
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
            },
        }
        del Project

        await context.respond(f"```json\n{json.dumps(response, indent=2)}\n```")

    checks = [superusers_only]
