from hikari import User
from lightbulb import SlashSubCommand, SlashCommandGroup, Option, SlashCommandContext

from .checks import operator_only, verified_only
from .services import db


class ManageGroup(SlashCommandGroup):
    name = "manage"
    description = "Zarządzanie"


@ManageGroup.subcommand()
class ManageSelfCommand(SlashSubCommand):
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

    checks = [verified_only]


@ManageGroup.subcommand()
class ManageSomeone(SlashSubCommand):
    name = "user"
    description = "Zarządzaj innym użytkownikiem"

    user: User = Option('Użytkownik')
    action: str = Option('Operacja', choices=['remove', 'info'])

    async def callback(self, context: SlashCommandContext):
        user = context.options['user'].value
        action = context.options['action'].value

        if action == 'remove':
            db["verified"].delete_many({"discord_id": user})
            await context.respond("Unieważniono weryfikację użytkownika.")
        elif action == 'info':
            await context.respond("idk")

    checks = [operator_only]
