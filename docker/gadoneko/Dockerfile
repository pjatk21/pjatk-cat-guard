FROM python:3.10 AS base

RUN apt update && apt install -y build-essential git

RUN adduser -D -s /bin/bash neko

USER neko

RUN pip3 install poetry

WORKDIR /pjatk

COPY poetry.lock pyproject.toml /pjatk/

RUN poetry install --no-dev && poetry run pip install kaleido

RUN apt remove -y build-essential

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
