import logging
from datetime import datetime

from hikari import CommandInteractionOption
from lightbulb import Plugin
from lightbulb.events import SlashCommandInvocationEvent, SlashCommandCompletionEvent

from shared.documents import AuditLog, UserIdentity, ExecutedCommand

plugin = Plugin('Auditor')
logger = logging.getLogger('gadoneko.plugins.audit')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


def create_options_tree(option: CommandInteractionOption, output=None):
    if output is None:
        output = {}

    if option.value:
        return option.value

    for subop in option.options:
        if subop.value:
            output.update({subop.name: subop.value})
        else:
            output.update(
                {subop.name: [create_options_tree(s, output) for s in subop.options]}
            )

    return {option.name: output}


@plugin.listener(SlashCommandInvocationEvent)
async def invoked(event: SlashCommandInvocationEvent):
    log = AuditLog()
    log.interaction = event.context.interaction.id  # Can be treated like exec id
    log.identity = UserIdentity.from_context(event.context)

    if event.context.interaction.options:
        options = [create_options_tree(s) for s in event.context.interaction.options]
    else:
        options = None

    log.exec_cmd = ExecutedCommand(name=event.command.name, options=options)
    log.save()


@plugin.listener(SlashCommandCompletionEvent)
async def invoked(event: SlashCommandCompletionEvent):
    log: AuditLog = AuditLog.objects(interaction=event.context.interaction.id).first()
    log.completed = datetime.now()
    log.save()
