from ..commands.manage import ManageGroup
from lightbulb import SlashCommandContext, SlashSubGroup, SlashSubCommand, Option
from hikari import TextableChannel

from ..services import db


@ManageGroup.subgroup()
class ManageAudit(SlashSubGroup):
    name = 'audit'
    description = 'ustawia kanał z audytem'


@ManageAudit.subcommand()
class ManageAuditSet(SlashSubCommand):
    name = 'set'
    description = 'pch'

    channel: TextableChannel = Option('kanał docelowy')

    async def callback(self, context: SlashCommandContext):
        channel = context.options.channel

        db['audit'].update_one(
            {"guild_id": context.guild_id},
            {"$set": {"channel_id": channel}},
            upsert=True
        )

        await context.respond("ok.")
