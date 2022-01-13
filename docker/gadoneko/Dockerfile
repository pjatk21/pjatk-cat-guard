FROM python:3.10 AS base

RUN apt update && apt install -y build-essential git

RUN pip3 install poetry

WORKDIR /pjatk

COPY poetry.lock pyproject.toml /pjatk/

RUN poetry install --no-dev && poetry run pip install kaleido

RUN apt remove -y build-essential

ENV PYTHONPATH "${PYTHONPATH}:/pjatk/"

ENV TZ "Europe/Warsaw"

FROM base AS bot

COPY shared/ /pjatk/shared/

COPY gadoneko/ /pjatk/gadoneko/

FROM base AS web

COPY shared/ /pjatk/shared/

COPY webpanel/ /pjatk/webpanel/

COPY templates/ /pjatk/templates/
