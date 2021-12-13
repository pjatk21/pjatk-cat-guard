import yaml
from hikari import CommandPermission, CommandPermissionType, Embed
from lightbulb import Context

from shared.consts import BOT_CREATOR_ID
from shared.documents import GuildConfiguration
from shared.colors import WARN, RESULT
from shared.formatting import code_block
from asyncio import sleep


async def update_permissions(ctx: Context, conf: GuildConfiguration):
    # Update permissions for commands
    embed = Embed(title='Aktualizacja uprawnień w toku!', description='Proszę czekać', color=WARN)
    message = await ctx.bot.rest.create_message(
        ctx.get_channel(),
        embed=embed
    )
    async with ctx.bot.rest.trigger_typing(ctx.get_channel()):
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
                ctx.bot.slash_commands.get('adm').instances[None].id: computed_permissions
            }
        )
        await sleep(2)
    embed.title = f'Zaktualizowano {len(computed_permissions)} uprawnień!'
    embed.description = code_block(
        '# Disclaimer: first 4 rules, are fail-safes '
        '(disable admin for @everyone, enable for bot creator, enable for guild owner, tmp cmd invoker). '
        'You can ignore them.\n' +
        yaml.dump([{'id': int(cp.id), 'type': str(cp.type), 'access': cp.has_access} for cp in computed_permissions]),
        'yaml'
    )
    embed.color = RESULT
    await message.edit(embed=embed)
