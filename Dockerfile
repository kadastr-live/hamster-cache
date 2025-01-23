FROM python:3.11.11-alpine3.21 AS python3-base-image

RUN apk add nginx

COPY pyproject.toml /code/
COPY hamstercache/ /code/hamstercache

RUN pip install -e /code/

WORKDIR .

ENTRYPOINT ["hamster-cache"]
