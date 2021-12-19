FROM python:3.10-alpine

RUN apk add build-base openssl-dev libffi-dev

RUN pip3 install poetry

WORKDIR /pjatk

COPY poetry.lock pyproject.toml /pjatk/

RUN poetry install --no-dev

RUN apk del build-base openssl-dev libffi-dev

COPY gadoneko/ /pjatk/gadoneko/

COPY shared/ /pjatk/shared/

COPY webgate/ /pjatk/webgate/

COPY templates/ /pjatk/templates/

ENV PYTHONPATH "${PYTHONPATH}:/pjatk/"

ENV TZ "Europe/Warsaw"
