from hikari import User
from lightbulb import SlashSubCommand, SlashCommandGroup, Option, SlashCommandContext

from .checks import operator_only, verified_only
from .services import db
from .embed_factory import embed_user_audit


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
            verified_role = db["roles"].find_one({"guild_id": context.guild_id})["role_id"]
            context.member.remove_role(verified_role)
            await context.respond("Wycofano weryfikację.")
        elif action == 'info':
            user_data = db["verified"].find_one({"discord_id": context.author.id, "guild_id": context.get_guild().id})
            embed = embed_user_audit(user_data, str(context.author))

            await context.respond(embed=embed)
        else:
            await context.respond("ayo???")

    checks = [verified_only]


@ManageGroup.subcommand()
class ManageSomeone(SlashSubCommand):
    name = "user"
    description = "Zarządzaj innym użytkownikiem"

    user: User = Option('Użytkownik')
    action: str = Option('Operacja', choices=['info', 'remove'])

    async def callback(self, context: SlashCommandContext):
        user = context.options['user'].value
        action = context.options['action'].value

        if action == 'remove':
            db["verified"].delete_many({"discord_id": user})
            verified_role = db["roles"].find_one({"guild_id": context.guild_id})["role_id"]
            await context.bot.rest.remove_role_from_member(
                context.guild_id,
                user,
                verified_role
            )
            await context.respond("Wycofano weryfikację.")
        elif action == 'info':
            user_data = db["verified"].find_one({"discord_id": context.author.id, "guild_id": context.get_guild().id})
            username = str(await context.bot.rest.fetch_user(user))
            embed = embed_user_audit(user_data, username)

            await context.respond(embed=embed)

    checks = [operator_only]
