#!/usr/bin/env bash

uv run gunicorn --bind 0.0.0.0:$SERVER_PORT --workers 1 --timeout 300 wsgi:app