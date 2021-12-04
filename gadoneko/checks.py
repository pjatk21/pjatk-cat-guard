from hikari.permissions import Permissions
from lightbulb.context import Context
from lightbulb.utils import permissions_for

from shared.documents import TrustedUser


def trusted_only(ctx: Context):
    trust: TrustedUser = TrustedUser.objects(identity__user_id=ctx.user.id, identity__guild_id=ctx.guild_id).first()
    return bool(trust)


def untrusted_only(ctx: Context):
    return not trusted_only(ctx)


def staff_only(ctx: Context):
    is_manager = permissions_for(ctx.member) & Permissions.MANAGE_GUILD
    return is_manager or ctx.get_guild().owner_id == ctx.user.id
