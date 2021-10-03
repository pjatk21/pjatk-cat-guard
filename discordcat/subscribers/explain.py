from datetime import datetime

from hikari.events import GuildMessageCreateEvent

from .subscriber import Subscription


class Explainer(Subscription):
    event = GuildMessageCreateEvent

    disabled_until = datetime.now()

    shortcuts = {
        "AM": "Analiza matematyczna",
        "PPJ": "Podstawy programowania w Javie",
        "TAK": "Techniki i architektura komputerów",
        "WMZ": "Wstęp do marketingu i zarządzania",
        "WSI": "Wprowadzenie do systemów informacyjnych",
        "HKJ": "Historia i Kultura Japonii",
        "ANG": "Język angielski",
        "LEK": "Lektorat",
        "ALG": "Algebra liniowa i geometria",
        "MAD": "Matematyka dyskretna",
        "RBD": "Relacyjne bazy danych",
        "GUI": "Programowanie obiektowe i GUI",
        "PJC": "Programowanie w językach C i C++",
        "SOP": "Systemy operacyjne",
        "ASD": "Algorytmy i struktury danych",
        "SAD": "Statystyczna analiza dancyh",
        "SBD": "Systemy baz danych",
        "SYC": "Systemy cyfrowe i podstawy elektroniki",
        "UTP": "Uniwersalne techniki programowania",
        "SKJ": "Sieci komputerowe i programowanie sieciowe w języku Java",
        "NAI": "Narzędzia sztucznej inteligencji",
        "PRI": "Projektowanie systemów informacyjnych",
        "PPB": "Prawne podstawy działalności gospodarczej",
        "MUL": "Multimedia",
    }

    async def callback(self, event: GuildMessageCreateEvent):
        if event.author.is_bot or event.author.is_system or event.message.content is None:
            return

        action_words = {"co to jest", "czym jest", "co oznacza", "o co chodzi z"}
        action_flag = False

        for aw in action_words:
            if aw in event.message.content:
                action_flag = True
                break

        if not action_flag:
            return

        explanations = []

        for key, val in self.shortcuts.items():
            if key in event.message.content:
                explanations.append(f"**{key}** oznacza **{val}**")

        if len(explanations) > 0:
            await event.message.respond("_" + ", ".join(explanations) + "_", reply=True)
