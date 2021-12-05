from hikari.permissions import Permissions
from lightbulb.context import Context
from lightbulb.utils import permissions_for

from shared.documents import TrustedUser, GuildConfiguration, UserIdentity, VerificationMethod


async def trusted_only(ctx: Context):
    trust: TrustedUser = TrustedUser.objects(identity__user_id=ctx.user.id, identity__guild_id=ctx.guild_id).first()
    print(trust)

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
    is_manager = permissions_for(ctx.member) & Permissions.MANAGE_GUILD
    return is_manager or ctx.get_guild().owner_id == ctx.user.id


def guild_configured(ctx: Context):
    conf: GuildConfiguration = GuildConfiguration.objects(guild_id=ctx.guild_id).first()
    return bool(conf)


def guild_not_configured(ctx: Context):
    return not guild_configured(ctx)
