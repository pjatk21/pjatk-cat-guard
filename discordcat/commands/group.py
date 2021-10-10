from hikari.channels import PermissionOverwriteType
from lightbulb import SlashCommandGroup, SlashSubCommand, SlashCommandContext, Option
from hikari import PermissionOverwrite
from ..collections import group_threads


class Group(SlashCommandGroup):
    name = 'group-thread'
    description = '...'


def create_group_code(number: int, group_type: str):
    output = str(number)

    if group_type == 'lektorat':
        output += 'l'
    elif group_type == 'ćwiczenia':
        output += 'c'
    
    return output


@Group.subcommand()
class Join(SlashSubCommand):
    name = 'join'
    description = "..."

    studying_mode: str = Option(name='tryb', description='...', choices=('stacjonarnie', 'zaocznie'))
    group_type: str = Option(name='grupa', description='...', choices=('lektorat', 'ćwiczenia'))
    group_number: int = Option(name='numer', description='...')

    async def callback(self, context: SlashCommandContext):
        group_code = create_group_code(context.options.group_number, context.options.group_type)

        assigned_thread = group_threads.find_one(
            {"guild_id": context.guild_id, "code": group_code, "mode": context.options.studying_mode}
        )

        if assigned_thread is None:
            channel = await context.bot.rest.create_guild_text_channel(
                context.get_guild(),
                group_code,
            )
            await context.bot.rest.edit_permission_overwrites(
                channel,
                context.author,
                allow=[]
            )

        await context.respond(str(context.options))
