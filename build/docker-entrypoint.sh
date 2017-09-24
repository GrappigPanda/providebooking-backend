#!/bin/bash

python3 migrate.py db upgrade
exec gunicorn almanac.wsgi:app --timeout=${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} -b 0.0.0.0:8000 --log-level ${GUNICORN_LOG_LEVEL}
