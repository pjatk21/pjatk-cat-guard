from lightbulb.slash_commands import SlashCommandContext

from .embed_factory import embed_error, embed_warn
from .services import db


async def superusers_only(context: SlashCommandContext):
    if context.author.id == 285146237613899776:  # hehe lilpostian
        return True

    if db["superusers"].find_one({"discord_id": context.author.id}) is not None:
        return True
    else:
        return False


async def operator_only(context: SlashCommandContext):
    if context.member.permissions.MANAGE_GUILD:
        return True

    if await superusers_only(context):
        return True

    return False


async def verified_only(context: SlashCommandContext):
    verified_role_id = db["roles"].find_one({"guild_id": context.guild_id})["role_id"]

    user_roles = await context.member.fetch_roles()

    if verified_role_id in tuple(map(lambda x: x.id, user_roles)):
        return True

    verified = db["verified"]
    verification = verified.find_one({"discord_id": context.author.id, "guild_id": context.guild_id})
    if verification is None:
        await context.respond(
            embed=embed_error(
                "Nie dokonałeś weryfikacji! Wykonaj komendę `/verify` aby uzyskać weryfikację!"
            )
        )
        return False
    else:
        await context.member.add_role(verified_role_id)
        return True


async def unverified_only(context: SlashCommandContext):
    verified = db["verified"]
    verification = verified.find_one({"discord_id": context.author.id})
    if verification is not None:
        await context.respond(
            embed=embed_warn(
                "Już jesteś zarejestrowany, nie ma potrzeby ponownie wykonywać tej komendy!"
            )
        )
        return False
    else:
        return True


async def guild_configured(context: SlashCommandContext):
    target_role = db['roles'].find_one({"guild_id": context.guild_id})

    if target_role is None:
        await context.respond(embed=embed_error("Na tym serwerze jeszcze nie ustawiono rangi weryfikacyjnej. "
                                                "Skontaktuj się z administracją. (exec `/setup role`)"))
        return False

    return True
