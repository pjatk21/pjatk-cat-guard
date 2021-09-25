from hikari.events import MessageCreateEvent
from lightbulb import SlashSubCommand, SlashCommandGroup, SlashCommandContext

from .checks import superusers_only
from .embed_factory import embed_error, embed_success


class UpdateCommand(SlashCommandGroup):
    name = "update"
    description = "Test slash command group."


@UpdateCommand.subcommand()
class SetupVerifiedRoleCommand(SlashSubCommand):
    name = "lists"
    description = "Wczytuje listę użytkowników"

    async def callback(self, context: SlashCommandContext):
        await context.respond("Wyślij plik")
        file_upload: MessageCreateEvent = await context.bot.wait_for(
            MessageCreateEvent,
            timeout=10,
            predicate=lambda x: x.channel_id == context.channel_id
            and x.author == context.author,
        )
        if len(file_upload.message.attachments) == 1:
            attachment = file_upload.message.attachments[0]
            if attachment.extension != "json":
                await context.bot.rest.create_message(
                    context.channel_id, embed=embed_error("Złe rozszerzenie pliku!")
                )
                return

            file_content = await attachment.read()

            await context.bot.rest.create_message(
                context.channel_id,
                "Baza wirusów Avast została zaktualizowana...",
                tts=True,
            )
            await context.bot.rest.create_message(
                context.channel_id,
                embed=embed_success("Zaktualizowano bazę studentów!"),
            )
        else:
            await context.bot.rest.create_message(
                context.channel_id, embed=embed_error("To nie jest plik mordo!")
            )

    checks = [superusers_only]
