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


def embed_user_audit(user_data, username):
    embed = Embed()
    embed.title = f'Dane o {username}'
    embed.color = Color.of("#64de9f")
    embed.add_field("Data weryfikacji", user_data["when"].isoformat())
    embed.add_field("Połączony numer studenta", user_data["student_mail"][:6])

    if user_data["verified_by"] == 'self-verified':
        embed.add_field("Metoda weryfikacji", "link dostarczony email'em")

    if user_data["verified_by"] == 'operator':
        embed.add_field("Metoda weryfikacji", "weryfikacja ręczna przez operatora")
        embed.add_field("Operator", user_data["operator"]["name"])

    return embed
