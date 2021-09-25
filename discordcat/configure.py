import json
from datetime import datetime

from hikari import Role, User
from lightbulb.slash_commands import (
    SlashCommandGroup,
    SlashSubCommand,
    SlashCommandContext,
    Option,
)

from .checks import superusers_only
from .embed_factory import embed_info
from .services import db

roles = db["roles"]
verifiers = db["verifiers"]


class SetupCommand(SlashCommandGroup):
    name = "setup"
    description = "Test slash command group."


@SetupCommand.subcommand()
class SetupVerifiedRoleCommand(SlashSubCommand):
    name = "role"
    description = "Ustawia rolę, która ma być przypisana"
    role: Role = Option("Rola, która ma być przyznawana po weryfikacji.")

    async def callback(self, context: SlashCommandContext):
        target_role = context.options["role"].value
        role_object = next(
            filter(
                lambda x: x.id == target_role,
                await context.bot.rest.fetch_roles(context.guild_id),
            )
        )
        roles.update_one(
            {"guild_id": context.guild_id},
            {
                "$set": {
                    "role_id": target_role,
                    "when": datetime.now(),
                    "who": context.author.id,
                }
            },
            upsert=True,
        )
        await context.respond(
            embed=embed_info(f"Przypisano {role_object.name} jako grupę zweryfikowaną")
        )

    checks = [superusers_only]


@SetupCommand.subcommand()
class SetupVerifierCommand(SlashSubCommand):
    name = "verifier"
    description = "Ustawia osobę, która będzie mogła werifikować użytkowników."
    user: User = Option("Osoba, która cośtam cośtam")

    async def callback(self, context: SlashCommandContext):
        target_user = context.options["user"].value
        user_object = await context.bot.rest.fetch_user(target_user)
        roles.update_one(
            {"guild_id": context.guild_id, "user_id": target_user},
            {
                "$set": {
                    "user_id": target_user,
                    "when": datetime.now(),
                    "who": context.author.id,
                }
            },
            upsert=True,
        )
        await context.respond(f"Dodano {user_object.mention} do verifiers")

    checks = [superusers_only]


@SetupCommand.subcommand()
class SetupAuditCommand(SlashSubCommand):
    name = "audit"
    description = "chujemuje"

    async def callback(self, context: SlashCommandContext):
        role = roles.find_one({"guild_id": context.guild_id})
        verifiers_audited_ids = verifiers.find({"guild_id": context.guild_id})

        guild_roles = await context.bot.rest.fetch_roles(role["guild_id"])
        role = next(filter(lambda x: x.id == role["role_id"], guild_roles))
        verifiers_audited = []

        for user_id in map(lambda x: x["user_id"], verifiers_audited_ids):
            user = await context.bot.rest.fetch_user(user_id)
            verifiers_audited.append(
                {
                    "nickname": user.username,
                }
            )

        await context.respond("Wysłano audyt na DM")
        await context.author.send(
            f'```json\n{json.dumps({"role": role.name, "verifiers": verifiers_audited})}\n```'
        )

    checks = [superusers_only]


@SetupCommand.subcommand()
class SetupSuperuserCommand(SlashSubCommand):
    name = "superuser"
    description = "papież"
    user: User = Option("nie wiedział o pedofilii")

    async def callback(self, context: SlashCommandContext):
        user = context.options["user"].value
        user_object = await context.bot.rest.fetch_user(user)
        db["superusers"].update_one(
            {"discord_id": user},
            {"$set": {"discord_id": user, "when": datetime.now()}},
            upsert=True,
        )
        await context.respond(f"Dodano {user_object.mention} do superusesrs")

    checks = [superusers_only]
