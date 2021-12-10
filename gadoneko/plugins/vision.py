import logging

from google.cloud.vision_v1p4beta1 import Image, ImageAnnotatorClient
from lightbulb import Plugin
from hikari.events import GuildMessageCreateEvent
import hashlib

from shared.documents import VisionCache

plugin = Plugin('AI Vision')
visioner = ImageAnnotatorClient()
logger = logging.getLogger('gadoneko.vision')

def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.listener(GuildMessageCreateEvent)
async def transcribe(event: GuildMessageCreateEvent):
    if event.message.referenced_message and event.message.content == 'transcribe':
        if event.message.referenced_message.attachments:
            ref_msg = event.message.referenced_message
            attachment = ref_msg.attachments[0]

            if not attachment.media_type.startswith('image/'):
                await plugin.bot.rest.create_message(
                    channel=event.channel_id,
                    reply=event.message,
                    content=f'Jeszcze nie obsługujemy typu {attachment.media_type}'
                )
                return

            # Hash check
            hash_of_file = hashlib.sha1(await attachment.read()).hexdigest()
            cache: VisionCache = VisionCache.objects(file_hash=hash_of_file).first()
            if cache:
                await plugin.bot.rest.create_message(
                    channel=event.channel_id,
                    reply=event.message,
                    content=f'`{cache.transcription}`'
                )
                logger.debug('Cache hit!, transcription reused')
                return
            else:
                logger.debug('Cache not found, continue')

            # Transcribe logic
            image = Image()
            image.source.image_uri = ref_msg.attachments[0].url
            vision_response = visioner.text_detection(image=image)

            await plugin.bot.rest.create_message(
                channel=event.channel_id,
                reply=event.message,
                content=f'`{vision_response.text_annotations[0].description}`'
            )

            VisionCache.objects(
                file_hash=hash_of_file
            ).update(upsert=True, transcription=vision_response.text_annotations[0].description)


@plugin.listener(GuildMessageCreateEvent)
async def transcribe(event: GuildMessageCreateEvent):
    if event.message.referenced_message and event.message.content == 'describe':
        if event.message.referenced_message.attachments:
            ref_msg = event.message.referenced_message
            attachment = ref_msg.attachments[0]

            if not attachment.media_type.startswith('image/'):
                await plugin.bot.rest.create_message(
                    channel=event.channel_id,
                    reply=event.message,
                    content=f'Jeszcze nie obsługujemy typu {attachment.media_type}'
                )
                return

            # Hash check
            hash_of_file = hashlib.sha1(await attachment.read()).hexdigest()
            cache: VisionCache = VisionCache.objects(file_hash=hash_of_file).first()
            if cache:
                await plugin.bot.rest.create_message(
                    channel=event.channel_id,
                    reply=event.message,
                    content=f'`{cache.description}`'
                )
                logger.debug('Cache hit!, transcription reused')
                return
            else:
                logger.debug('Cache not found, continue')

            # Describe logic
            image = Image()
            image.source.image_uri = ref_msg.attachments[0].url
            vision_response = visioner.object_localization(image=image)
            objects = vision_response.localized_object_annotations
            description = '\n'.join(
                [f'{o.name} ({o.score})' for o in objects]
            )

            await plugin.bot.rest.create_message(
                channel=event.channel_id,
                reply=event.message,
                content=f'`{description}`'
            )

            VisionCache.objects(
                file_hash=hash_of_file
            ).update(upsert=True, description=description)
