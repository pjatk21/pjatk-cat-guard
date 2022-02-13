FROM python:3.10 AS base

RUN apt update && apt install -y build-essential git cowsay figlet

WORKDIR /usr/share/figlet

COPY docker/gadoneko/download_fonts.sh .

RUN bash download_assets.sh && rm download_fonts.sh

RUN adduser --disabled-login --shell /bin/bash neko

USER neko

RUN pip3 install -U poetry

ENV PATH "${PATH}:/home/neko/.local/bin"

WORKDIR /pjatk

COPY poetry.lock pyproject.toml /pjatk/

RUN poetry install --no-dev

ENV PYTHONPATH "${PYTHONPATH}:/pjatk/"

ENV PATH "${PATH}:/usr/games"

ENV TZ "Europe/Warsaw"

COPY . /pjatk/

RUN mkdir "/pjatk/data"

VOLUME /pjatk/data

# Update permissions
USER root

RUN chmod -R 777 /pjatk && chmod -R 755 /pjatk/gadoneko /pjatk/doctor /pjatk/shared/ /pjatk/webpanel && chown -R neko /pjatk

USER neko

FROM base AS bot

HEALTHCHECK CMD python3 -m doctor bot

ENTRYPOINT poetry run python3 -O -m gadoneko.bot

FROM base AS web

ENTRYPOINT poetry run python -m uvicorn webpanel:app --host 0.0.0.0 --proxy-headers --forwarded-allow-ips="*" --workers=2 --log-level=debug

FROM base AS celery

ENTRYPOINT poetry run celery -A gadoneko.tasks worker -l INFO -B -P threads
