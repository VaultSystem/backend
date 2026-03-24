set shell := ["powershell.exe", "-c"]

default:
    just --list

run port="8000":
    uv run ./main.py

migrate:
    alembic upgrade head

#uvicorn main:app --host 0.0.0.0 --port 8000 --reload
