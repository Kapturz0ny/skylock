#!/bin/sh

DATA_DIR="data"
if [ ! -d "$DATA_DIR" ]; then
    mkdir "$DATA_DIR"
fi

alembic upgrade head

exec uvicorn skylock.app:app --host 0.0.0.0 --reload --log-level debug
