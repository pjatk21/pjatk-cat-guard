from datetime import datetime, timedelta

from hikari.events import GuildMessageCreateEvent

from discordcat.services import db
from discordcat.subscribers.subscriber import Subscription


class CheckUser(Subscription):
    event = GuildMessageCreateEvent

    async def callback(self, event: GuildMessageCreateEvent):
        if event.author.is_bot or event.author.is_system:
            return

        verification = db["verified"].find_one(
            {"discord_id": event.author.id, "guild_id": event.get_guild().id}
        )

        if verification is None:
            verification_reminder = db["reminders"].find_one(
                {
                    "discord_id": event.author.id,
                    "guild_id": event.get_guild().id,
                    "topic": "verification",
                }
            )

            if verification_reminder is None:
                await event.member.send(
                    "Wciąż nie dokonałeś weryfikacji bro/sis/nb!\n"
                    'Sprawdź kanał "#✋weryfikacja-członków" aby dowiedzieć się więcej uwu'
                )
                db["reminders"].insert_one(
                    {
                        "discord_id": event.author.id,
                        "guild_id": event.get_guild().id,
                        "topic": "verification",
                        "when": datetime.now(),
                    }
                )
            elif datetime.now() - verification_reminder["when"] > timedelta(minutes=10):
                await event.member.send(
                    "**Wciąż nie dokonałeś weryfikacji bro/sis/nb!**\n"
                    'Sprawdź kanał "#✋weryfikacja-członków" aby dowiedzieć się więcej.'
                )
                db["reminders"].update_one(
                    {
                        "discord_id": event.author.id,
                        "guild_id": event.get_guild().id,
                        "topic": "verification",
                    },
                    {"$set": {"when": datetime.now()}},
                )
