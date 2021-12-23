from lightbulb import Plugin, BotApp
from hikari.events import GuildMessageCreateEvent, VoiceStateUpdateEvent
from shared.documents import UserIdentity


plugin = Plugin('Tracking')


def load(bot: BotApp):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(VoiceStateUpdateEvent)
async def count_voice_time(event: VoiceStateUpdateEvent):
    who = UserIdentity.from_member(event.state.member)
    