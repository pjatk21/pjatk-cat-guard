# PJATK cat guard
Bot do weryfikacji studentów.

## Contribution
### Nowe funkcje bota (slash commands, listeners)
1. Poznaj `hikari` i `hikari-lightbulb`
2. Kolejne funkcje dodawaj w folderze `gadoneko/plugins`
3. Pamiętaj aby tokeny do nowych usług podawać poprzez `os.getenv('SOME TOKEN')`
4. (Opcjonalne) Używaj formatera `black`

### Nowe elementy strony
1. Poznaj `starlette`, `jinja2` i `shards-ui` (i może `uvicorn`)
2. Każda nowa strona powinna bazować na `home.html`
3. Logikę opakowuj w `HTTPEndpoint`
4. Keep it lightweight and responsive

## Oficjalna instalacja
[free.itny.me](https://free.itny.me/)

## Instalacja
 - `git clone https://github.com/kpostekk/pjatk-cat-guard`
 - `cp .example.env .production.env`
 - `docker-compose up -d`
