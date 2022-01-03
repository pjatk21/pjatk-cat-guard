FROM python:3.10-alpine

RUN apk add build-base openssl-dev libffi-dev git

RUN pip3 install poetry

WORKDIR /pjatk

COPY poetry.lock pyproject.toml /pjatk/

RUN poetry install --no-dev

RUN apk del build-base openssl-dev libffi-dev

COPY gadoneko/ /pjatk/gadoneko/

COPY shared/ /pjatk/shared/

COPY webpanel/ /pjatk/webpanel/

COPY templates/ /pjatk/templates/

ENV PYTHONPATH "${PYTHONPATH}:/pjatk/"

ENV TZ "Europe/Warsaw"
