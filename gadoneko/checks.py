import os

from hikari.permissions import Permissions
from lightbulb.context import Context
from lightbulb.utils import permissions_for

from shared.documents import TrustedUser, GuildConfiguration, UserIdentity, VerificationMethod


async def trusted_only(ctx: Context):
    trust: TrustedUser = TrustedUser.objects(identity__user_id=ctx.user.id, identity__guild_id=ctx.guild_id).first()

    if trust is None:
        conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()

        # Missing record in db
        if conf.trusted_role_id in ctx.member.role_ids:
            trust = TrustedUser()
            trust.identity = UserIdentity()
            trust.identity.user_id = ctx.user.id
            trust.identity.user_name = str(ctx.user)
            trust.identity.guild_id = ctx.get_guild().id
            trust.identity.guild_name = ctx.get_guild().name
            trust.verification_method = VerificationMethod.CONTEXT_PROVIDED

            await ctx.bot.rest.add_role_to_member(
                trust.identity.guild_id, trust.identity.user_id, conf.trusted_role_id
            )

            trust.save()

            return True
        return False
    return True


async def untrusted_only(ctx: Context):
    return not await trusted_only(ctx)


def staff_only(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()

    if conf:
        assign_based = ctx.user.id in conf.additional_staff
        for user_role in ctx.member.role_ids:
            for staff_role in conf.additional_staff_roles:
                assign_based = True if staff_role == user_role else assign_based
    else:
        assign_based = False

    is_manager = permissions_for(ctx.member) & Permissions.MANAGE_GUILD
    privileged_based = is_manager or ctx.get_guild().owner_id == ctx.user.id
    return privileged_based or assign_based


def guild_configured(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    return bool(conf)


def guild_not_configured(ctx: Context):
    return not guild_configured(ctx)


def bot_owner_only(ctx: Context):
    return ctx.user.id == os.environ.get('BOT_OWNER', 285146237613899776)
