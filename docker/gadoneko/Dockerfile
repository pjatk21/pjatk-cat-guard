FROM python:3.10 AS base

RUN apt update && apt install -y build-essential git

RUN adduser --disabled-login --shell /bin/bash neko

USER neko

RUN pip3 install -U poetry

ENV PATH "${PATH}:/home/neko/.local/bin"

WORKDIR /pjatk

COPY poetry.lock pyproject.toml /pjatk/

RUN poetry install --no-dev

ENV PYTHONPATH "${PYTHONPATH}:/pjatk/"

ENV TZ "Europe/Warsaw"

COPY . /pjatk/

FROM base AS bot

HEALTHCHECK CMD python3 -m doctor bot

ENTRYPOINT poetry run python3 -O -m gadoneko.bot

FROM base AS web

ENTRYPOINT poetry run python -m uvicorn webpanel:app --host 0.0.0.0

FROM base AS cron

ENTRYPOINT poetry run python3 -O -m gadoneko.cron
