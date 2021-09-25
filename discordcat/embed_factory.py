from hikari import Embed, Color


def embed_error(message: str) -> Embed:
    embed = Embed()
    embed.title = "Błąd"
    embed.description = message
    embed.color = Color.of("#ed0c2e")

    return embed


def embed_warn(message: str) -> Embed:
    embed = Embed()
    embed.title = "Ostrzeżenie"
    embed.description = message
    embed.color = Color.of("#dbc951")

    return embed


def embed_info(message: str) -> Embed:
    embed = Embed()
    embed.title = "Informacja"
    embed.description = message
    embed.color = Color.of("#4984bf")

    return embed


def embed_success(message: str) -> Embed:
    embed = Embed()
    embed.title = "Zrobione!"
    embed.description = message
    embed.color = Color.of("#5fc782")

    return embed
