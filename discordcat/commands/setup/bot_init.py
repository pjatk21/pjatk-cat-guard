from lightbulb.context import Context


async def init_bot_guild(ctx: Context):
    if ctx.author:
        await ctx.respond("Bruh")
    else:
        await ctx.respond("not bruh")
