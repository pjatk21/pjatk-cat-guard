import asyncio
import hashlib
import logging
import re
import threading
from datetime import datetime

from hikari import UnicodeEmoji, Attachment, Embed, Message, CustomEmoji, KnownCustomEmoji
from hikari.events import GuildMessageCreateEvent, GuildReactionAddEvent, MessageCreateEvent
from lightbulb import Plugin, implements, commands, command, Context, option
from mongoengine import DoesNotExist, Q

from shared.colors import FILE
from shared.documents import CommonRepoFile, UserIdentity
from shared.formatting import code_block
from shared.tika import tika_ocr

plugin = Plugin('Archive repository')
logger = logging.getLogger('gadoneko.plugins.repo')


def load(bot):
    bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


MATCH_PATTERN = r'application\/(pdf|zip)|text\/x-.*'
ARCHIVE_EMOJI = UnicodeEmoji('🗂')


@plugin.listener(GuildMessageCreateEvent)
async def add_archive_option(event: GuildMessageCreateEvent):
    """
    Listens for files uploaded, give option to mark file as achievable
    """
    if len(event.message.attachments) == 0:
        return

    for attachment in event.message.attachments:
        logger.debug('Checking pattern for %s', attachment.media_type)
        if not re.match(MATCH_PATTERN, attachment.media_type):
            continue

        await event.message.add_reaction(ARCHIVE_EMOJI)


async def process_attachment(attachment: Attachment, message: Message) -> Embed:
    file_hash = hashlib.sha256(await attachment.read()).hexdigest()
    try:
        file_doc = CommonRepoFile.objects(file_hash=file_hash).get()
    except DoesNotExist:
        file_doc = CommonRepoFile()
        file_doc.message_id = message.id
        file_doc.file_type = attachment.media_type
        file_doc.file_hash = file_hash
        file_doc.file_url = attachment.url
        file_doc.file_name = attachment.filename
        file_doc.added = message.created_at.astimezone()
        file_doc.save()

        # Run background ocr
        async def bg_ocr():
            logger.debug('OCR begin for %s (%s)', file_doc.file_name, file_doc.file_type)
            start = datetime.now()
            response, metadata = await tika_ocr(await attachment.read())
            file_doc.extra = {'text': response, 'metadata': metadata, 'time': (datetime.now() - start).total_seconds()}
            file_doc.save()
            logger.debug('OCR finished for %s', file_doc.file_name)

        threading.Thread(
            target=lambda: asyncio.run(bg_ocr()), daemon=True, name=f'ocr-{file_doc.file_hash}'
        ).start()

    return Embed(title=file_doc.file_name, color=FILE) \
        .add_field('SHA-256', code_block(file_doc.file_hash)) \
        .add_field('Added', file_doc.added.isoformat())


@plugin.listener(GuildReactionAddEvent)
async def receive_arch_signal(event: GuildReactionAddEvent):
    if event.member.is_bot:
        return

    if event.emoji_name != '\N{card index dividers}':
        pass

    logger.debug('Marked as archival!')
    message = await plugin.bot.rest.fetch_message(channel=event.channel_id, message=event.message_id)
    await message.remove_all_reactions(emoji=ARCHIVE_EMOJI)

    results = [await process_attachment(attachment, message) for attachment in message.attachments]
    await plugin.bot.rest.create_message(
        channel=message.channel_id,
        reply=message,
        embeds=results
    )


@plugin.listener(GuildMessageCreateEvent)
async def update_tags(event: GuildMessageCreateEvent):
    if event.message.referenced_message and event.message.content:
        ref = await plugin.bot.rest.fetch_message(event.message.referenced_message.channel_id,
                                                  event.message.referenced_message.id)
        tags = re.match(r'tags: ((\w|\d).*(\w|\d))', event.message.content)
        if tags is None:
            return
        tags = tags.groups()[0].split(' ')
        for attachment in ref.attachments:
            try:
                a_file = CommonRepoFile.objects(file_hash=hashlib.sha256(await attachment.read()).hexdigest()).get()
                a_file.tags = tags
                a_file.save()
            except DoesNotExist:
                logger.info('User tried to tag file which is not archived.')
        ce = UnicodeEmoji('🆗')
        await event.message.add_reaction(ce)


@plugin.command()
@command('arc', 'arc')
@implements(commands.SlashCommandGroup)
def arc():
    pass


@arc.child()
@option('tag', 'tag')
@command('tag-search', 'Wyszukuje plik po tagach')
@implements(commands.SlashSubCommand)
async def find_tags(ctx: Context):
    results = CommonRepoFile.objects(tags__contains=ctx.options.tag)
    if len(results):
        await ctx.respond(str(results))
    else:
        await ctx.respond('Nie ma takich plików')


@arc.child()
@option('query', 'zapytanie')
@command('search', 'Szuka w archiwum')
@implements(commands.SlashSubCommand)
async def find_arc(ctx: Context):
    tq = ctx.options.query
    query = Q(file_name__contains=tq) | Q(file_hash__startswith=tq) | Q(file_type=tq) | Q(tags__contains=tq)
    query |= Q(extra__text__contains=tq) | Q(extra__metadata__contains=tq)

    results = CommonRepoFile.objects(query)
    if len(results):
        def create_embed(r: CommonRepoFile):
            embed = Embed(title=r.file_name, url=r.file_url, timestamp=r.added.astimezone(), color=FILE).add_field(
                'tags', ', '.join(r.tags) if r.tags else 'brak tagów'
            ).add_field(
                'mini hash', f'`{r.file_hash[:24]}...`'
            )

            if re.match(r'image/', r.file_type):
                embed.set_thumbnail(r.file_url)

            return embed

        await ctx.respond(
            embeds=[create_embed(r) for r in results]
        )
    else:
        await ctx.respond('Brak takich plików w archiwum.')
