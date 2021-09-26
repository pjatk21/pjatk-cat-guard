from lightbulb import SlashSubCommand, SlashCommandGroup, Option, SlashCommandContext

from .services import db


class ManageGroup(SlashCommandGroup):
    name = "manage"
    description = "Zarządzanie"


@ManageGroup.subcommand()
class SetupVerifiedRoleCommand(SlashSubCommand):
    name = "self"
    description = "Zarządzaj swoim kontem"

    action: str = Option('Operacja', choices=['remove', 'info'])

    async def callback(self, context: SlashCommandContext):
        action = context.options['action'].value

        if action == 'remove':
            db["verified"].delete_many({"discord_id": context.author.id})
            await context.respond("Usunięto.")
        elif action == 'info':
            await context.respond("w dowodzie se sprawdź")
        else:
            await context.respond("ayo???")
