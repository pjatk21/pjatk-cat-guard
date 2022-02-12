import logging
import os
import random

from lightbulb import BotApp, Plugin, command, implements, commands, Context, option

from shared.documents import VerificationRequest, UserIdentity, VerificationState, VerificationPhotos, \
    VerificationGoogle

plugin = Plugin('Admin')
logger = logging.getLogger('gadoneko.devel')


def load(bot: BotApp):
    if os.getenv('ENV') == 'dev':
        bot.add_plugin(plugin)


def unload(bot):
    bot.remove_plugin(plugin)


@plugin.command()
@command('dev', 'Zestaw narzędzi administracyjnych.')
@implements(commands.SlashCommandGroup)
def devel():
    pass


@devel.child()
@option('amount', 'Ilość', type=int)
@command('mock', 'Generuje potężną ilość requestów')
@implements(commands.SlashSubCommand)
async def devel_mock(ctx: Context):
    message = await ctx.respond(f'Tworzę {ctx.options.amount} requestów')
    for i in range(ctx.options.amount):
        vr = VerificationRequest()
        vr.identity = UserIdentity.from_context(ctx)
        vr.state = VerificationState.IN_REVIEW
        vr.photos = VerificationPhotos(
            front='gadoneko/static/id.front.png',
            back='gadoneko/static/id.back.png',
        )
        vr.google = VerificationGoogle(
            name=f'Mr. Mock {i}',
            email=f's{random.randint(1000, 9999)}@pjwstk.edu.pl',
            raw={
                'picture': 'https://i.pravatar.cc/120'
            }
        )
        vr.code = f'MOCK-{i}-{random.randint(1000, 9999)}'
        vr.save()

    await message.edit('Ukończono!')
