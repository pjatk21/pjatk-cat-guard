from hikari import User
from lightbulb import SlashCommandGroup, SlashSubCommand, SlashCommandContext, Option

from discordcat.services import db
from ..checks import operator_only


class FindBy(SlashCommandGroup):
    name = "find-by"
    description = "przeszukuje baze danych"


@FindBy.subcommand()
class Discord(SlashSubCommand):
    name = "discord"
    description = "discord"

    user: User = Option(description="user ds")

    async def callback(self, context: SlashCommandContext):
        await context.respond(
            str(
                db["verified"].find_one(
                    {
                        "guild_id": context.get_guild().id,
                        "discord_id": context.options.user,
                    }
                )
            )
        )

    checks = [operator_only]


@FindBy.subcommand()
class Eska(SlashSubCommand):
    name = "eska"
    description = "eska"

    eska: str = Option(description="eska lub mail")

    async def callback(self, context: SlashCommandContext):
        await context.respond(
            str(
                db["verified"].find_one(
                    {
                        "guild_id": context.get_guild().id,
                        "student_mail": {"$regex": context.options.eska},
                    }
                )
            )
        )

    checks = [operator_only]
