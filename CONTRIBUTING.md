# Contributuing
## Zgłaszanie błędów
 - Załączaj screeny
 - Czas wydarzenia
 - Opowiedz co chciałeś uzyskać a co faktycznie uzyskałeś

## Nowe funkcje bota (slash commands, listeners)
1. Poznaj `hikari` i `hikari-lightbulb`
2. Kolejne funkcje dodawaj w folderze `gadoneko/plugins`
3. Pamiętaj aby tokeny do nowych usług podawać poprzez `os.getenv('SOME TOKEN')`
4. Testuj swoje rozwiązanie **zawsze** z najnowszymi bibliotekami
5. (Opcjonalne) Uruchom chociaż raz bota w dockerze
6. (Opcjonalne) Używaj formatera `black`

## Nowe elementy strony
1. Poznaj `starlette`, `jinja2` i `shards-ui` (i może `uvicorn`)
2. Każda nowa strona powinna bazować na `home.html`
3. Logikę opakowuj w `HTTPEndpoint`
4. Keep it lightweight and responsive


## Uruchamianie
Nie polecam robić dev na dockerze bezpośrednio. Uruchamiaj wszystko wewnątrz pipenv jako odzielne procesy.

Bot
```
poetry run python3 -O -m gadoneko.bot
```

Bot CRON
```
poetry run python3 -O -m gadoneko.cron
```

Webgate 
```
poetry run python -m uvicorn webgate:app
```

Database (in docker)
```
docker run -p 27017:27017 --restart always --name mongodb -d mongo:latest
```

Redis (messaging broker and cache)
```
docker run --name dev-redis -d -p 6379:6379 redis:latest
```

Celery
```
poetry run python -m celery -A tasukuneko.heart worker -B -l DEBUG
```

## Nazewnictwo
 - *gado neko (ガード猫)* - guard cat (main discord bot codebase)
 - *tasuku neko (タスク猫)* - task cat (codebase related to the celery tasks)
