FROM python:3.8

WORKDIR /app

COPY ./requirements.txt .

RUN set -ex; \
    pip install -r ./requirements.txt;

COPY . .

ENTRYPOINT ["/bin/bash", "/app/docker-entrypoint.sh"]

CMD ["uwsgi"]
