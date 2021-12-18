from hikari import ButtonStyle, Embed
from lightbulb.ext.neon import ComponentMenu, button
from hikari.events import GuildMessageCreateEvent


class AdminQueryMenu(ComponentMenu):
    @button("kick", "query_kick", ButtonStyle.PRIMARY)
    async def kick(self):
        await self.context.user.send('you suck')
        await self.edit_msg(embed=Embed(title='we suck'))

    @button("email", "query_email", ButtonStyle.SECONDARY, emoji='📨')
    async def email(self):
        await self.context.bot.rest.create_message(
            self.context.channel_id,
            'mail here'
        )
        r: GuildMessageCreateEvent = await self.context.bot.wait_for(
            GuildMessageCreateEvent, timeout=60, predicate=lambda m: m.channel_id == self.context.channel_id
        )
        await self.edit_msg(f'Email: {r.content}')
