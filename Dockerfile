FROM python:3-alpine

RUN apk add build-base

RUN pip3 install pipenv

WORKDIR /pjatk

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install

RUN apk del build-base

COPY common/ /pjatk/common/

COPY discord_janitor/ /pjatk/discord_janitor/

COPY web_janitor/ /pjatk/web_janitor/

ENV PYTHONPATH "${PYTHONPATH}:/pjatk"
