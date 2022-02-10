# PJATK cat guard
Bot do weryfikacji studentów.

## Features
 - Weryfikacja przy użyciu logowania OAuth
 - Prawie zerowa konfiguracja
 - Wsparcie dla *slash commands* oraz *user commands*
 - Budowane na nowych technologiach
   - Python 3.10 + hikari + starlette
   - MongoDB
   - Docker
   - Uvicorn
 - Weryfikacja na podstawie dokumentów
 - Panel administracyjny

> Więcej o tym jak użwać bota, jest w [instrukcji obsługi](https://github.com/pjatk21/pjatk-cat-guard/blob/main/MANUAL.md)

## Instalacja
 - `git clone https://github.com/kpostekk/pjatk-cat-guard`
 - `cp .example.env .production.env`
 - `docker-compose up -d`
 > Jeżeli nie chce ci się hostować, skorzystaj z publicznej instalacji [free.itny.me](https://free.itny.me/)
