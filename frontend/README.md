# Nexventory Frontend

Minimal React dashboard for the Nexventory FastAPI backend.

## Quick start

1. Ensure the API is running at http://localhost:8000 (`docker compose up` or `uvicorn` from `app/`).
2. Copy env and install:

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

3. Open http://localhost:5173
4. Register a user via Swagger (`POST /register`) or curl, then sign in.

## Environment

| Variable       | Description                          |
| -------------- | ------------------------------------ |
| `VITE_API_URL` | FastAPI base URL (no trailing slash) |

## Scripts

| Command        | Description              |
| -------------- | ------------------------ |
| `npm run dev`  | Vite dev server (:5173)  |
| `npm run build`| Production build to `dist/` |
| `npm run preview` | Preview production build |

## Docker (standalone)

```powershell
docker build -t nexventory-frontend --build-arg VITE_API_URL=http://localhost:8000 ./frontend
docker run -p 3000:80 nexventory-frontend
```

Set `VITE_API_URL` at **build time** to the URL browsers will use to reach the API.
