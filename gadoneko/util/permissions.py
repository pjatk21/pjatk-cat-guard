import yaml
from hikari import CommandPermission, CommandPermissionType, Embed
from lightbulb import Context

from shared.colors import WARN, RESULT
from shared.consts import BOT_CREATOR_ID
from shared.documents import GuildConfiguration
from shared.formatting import code_block


async def update_permissions(ctx: Context, conf: GuildConfiguration):
    # Update permissions for commands
    embed = Embed(title='Aktualizacja uprawnień w toku!', description='Proszę czekać', color=WARN)
    message = await ctx.bot.rest.create_message(
        ctx.get_channel(),
        embed=embed
    )

    # Compute permissions
    computed_permissions = [
        # @everyone id is equal to guild id, disable admin for @everyone
        CommandPermission(id=ctx.guild_id, type=CommandPermissionType.ROLE, has_access=False),
        # Fail-safe, assign bot creator
        CommandPermission(id=BOT_CREATOR_ID, type=CommandPermissionType.USER, has_access=True),
        # Fail-safe, assign guild owner
        CommandPermission(id=ctx.get_guild().owner_id, type=CommandPermissionType.USER, has_access=True),
        # Fail-safe, assign temporarily command invoker
        CommandPermission(id=ctx.author.id, type=CommandPermissionType.USER, has_access=True),
    ]
    for user in conf.additional_staff:
        computed_permissions.append(CommandPermission(id=user, type=CommandPermissionType.USER, has_access=True))
    for role in conf.additional_staff_roles:
        computed_permissions.append(CommandPermission(id=role, type=CommandPermissionType.ROLE, has_access=True))

    await ctx.bot.rest.set_application_guild_commands_permissions(
        ctx.app.application.id,
        ctx.get_guild(),
        {
            ctx.bot.slash_commands.get('adm').instances[None].id: computed_permissions,
            ctx.bot.slash_commands.get('reload').instances[None].id: computed_permissions,
        }
    )

    embed.title = f'Zaktualizowano {len(computed_permissions)} uprawnień!'
    embed.description = code_block(
        yaml.dump([{'id': int(cp.id), 'type': str(cp.type), 'access': cp.has_access} for cp in computed_permissions[4:]]),
        'yaml'
    )
    embed.color = RESULT
    await message.edit(embed=embed)
