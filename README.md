# Mini IT Platform

FastAPI backend with JWT authentication and PostgreSQL (SQLAlchemy ORM).

## Project layout

```
├── app/                 # Application source (run uvicorn from here for local dev)
│   ├── main.py          # FastAPI entry point
│   ├── database.py      # Engine, SessionLocal, get_db()
│   ├── auth/            # JWT + password security
│   ├── crud/            # Database operations
│   ├── models/          # SQLAlchemy ORM models
│   ├── routers/         # API routes
│   └── schemas/         # Pydantic request/response models
├── requirements.txt     # Python dependencies (used by Docker)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Prerequisites

- Python 3.12+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for containerized setup)
- Optional: local PostgreSQL if not using Docker for the database

## Environment variables

Copy the example file and set a strong `SECRET_KEY`:

```powershell
copy .env.example .env
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default `30`) |

**Docker networking:** Inside Compose, the API must use host `db` (the PostgreSQL service name), not `localhost`. `docker-compose.yml` sets `DATABASE_URL` for the `api` service automatically.

**Local API on your machine:** Use `localhost` in `DATABASE_URL` when PostgreSQL is on your host or port `5432` is published from the `db` container.

## Run with Docker (recommended)

From the project root:

```powershell
copy .env.example .env
# Edit .env and set SECRET_KEY

docker compose up --build
```

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

Stop containers (keep database data):

```powershell
docker compose down
```

Stop and delete database volume:

```powershell
docker compose down -v
```

## Run locally without Docker

1. Start PostgreSQL and create database `mini_it_platform`.
2. Install dependencies:

```powershell
cd app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment:

```powershell
copy .env.example .env
```

4. Run the API:

```powershell
uvicorn main:app --reload
```

## API quick test

1. **Register** — `POST /register` with JSON body `username`, `email`, `password`.
2. **Login** — `POST /token` with form fields `username`, `password` → receive JWT.
3. **Profile** — `GET /users/me/` with header `Authorization: Bearer <token>`.

Use Swagger at `/docs` to try endpoints interactively (authorize with the token from `/token`).

## Dependencies

Listed in `requirements.txt`. Notable choices:

- **PyJWT** — JWT encode/decode (`import jwt`)
- **passlib + bcrypt** — password hashing (`bcrypt<5` for passlib compatibility)
- **SQLAlchemy + psycopg2-binary** — PostgreSQL ORM

`python-jose` is not used in this project.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API cannot connect to DB in Docker | Ensure `DATABASE_URL` uses `@db:5432`, not `@localhost` |
| `ModuleNotFoundError` in container | Image runs `main:app` from `/app`; do not use `app.main:app` unless you convert to a package layout |
| passlib / bcrypt warning on Windows | Pin `bcrypt<5` (already in requirements.txt) |
| Empty database | Tables are created on API startup via `Base.metadata.create_all()` |
