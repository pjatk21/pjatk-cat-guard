import os

from dotenv import load_dotenv
from lightbulb.slash_commands import SlashCommand, SlashCommandContext, Option
from lightbulb.checks import Check, owner_only
from lightbulb.errors import NotOwner
from hikari import Role

from discord_janitor.services import db

load_dotenv()

env = os.environ

config = db["configuration"]


async def is_onwer(context: SlashCommandContext):
    if str(context.author) != 'lil Postman#1221':
        await context.respond("You are not a lilPostian bro")
        raise NotOwner("You are not a lilPostian bro")
    return True


class SetupRoleCommand(SlashCommand):
    name = 'setup-verification-role'
    description = 'Konfiguruje serwer (wyłącznie dla administracji)'
    role: Role = Option('Grupa, która zostanie przypisana po weryfikacji.')

    async def callback(self, context: SlashCommandContext):
        role = context.options['role'].value
        config.update_one({'server_id': context.guild_id}, {"$set": {'server_id': context.guild_id, 'set_role': role}}, upsert=True)
        await context.respond("Ustawiono")

    checks = [
        Check(is_onwer)
    ]


class ReadRoleCommand(SlashCommand):
    name = 'read-verification-role'
    description = 'Konfiguruje serwer (wyłącznie dla administracji)'
    role: Role = Option('Grupa, która zostanie przypisana po weryfikacji.')

    async def callback(self, context: SlashCommandContext):
        await context.respond(config.find_one({'server_id': context.guild_id}))

    checks = [
        Check(is_onwer)
    ]

