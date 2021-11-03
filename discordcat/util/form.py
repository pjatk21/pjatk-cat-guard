from dataclasses import dataclass

from lightbulb import Bot
from hikari.events import MessageCreateEvent

@dataclass()
class FormQuestion:
    question: str
    wait_for: str = 'text'  # attachment or text


async def send_form(bot: Bot, channel_id: int, structure: dict[str, FormQuestion]):
    result = {}

    for key, question in structure.items():
        await bot.rest.create_message(channel_id, question.question)

        match question.wait_for:
            case 'text':
                ev = await bot.wait_for(
                    MessageCreateEvent, 120,
                    lambda e: e.channel_id == channel_id and e.content is not None
                )
                result.update({key: ev.content})
            case 'attachment':
                ev = await bot.wait_for(
                    MessageCreateEvent, 120,
                    lambda e: e.channel_id == channel_id and len(e.message.attachments) > 0
                )
                result.update({key: ev.message.attachments})
            case _:
                raise Exception("Programista chuj ci w dupe")

    return result
