FROM python:3.13-slim AS builder

ENV POETRY_VERSION=1.8.4
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry export --without-hashes -o requirements.txt

FROM python:3.13-slim AS deploy

WORKDIR /app

COPY --from=builder /app/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT [ "./entrypoint_dev.sh" ]
