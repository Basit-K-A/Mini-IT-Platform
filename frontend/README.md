# Nexventory frontend

React + Vite dashboard connected to the FastAPI backend.

## Setup

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:5173

## API URL (`VITE_API_URL`)

| Mode | Value | Backend |
|------|--------|---------|
| Dev (direct API) | `http://localhost:8000` | `docker-compose.dev.yml` publishes API :8000 |
| Dev (via nginx) | `http://localhost/api` | Base stack on :80 with `/api` proxy |
| Production | `https://your-api-host` | No hardcoded localhost |

## Auth (backend mapping)

| UI | FastAPI |
|----|---------|
| Register | `POST /register` |
| Login | `POST /token` (form login) |
| Current user | `GET /users/me/` |

JWT is stored in `localStorage` and sent as `Authorization: Bearer`.

## Roles

- **Devices** (create/edit/delete): `admin`, `technician`
- **Audit logs**: `admin`, `analyst`
- **Viewer**: read devices/events only

Promote roles via API (`PATCH /users/{id}/role`) or SQL.

## Project structure

```
src/
  api/          # HTTP client + resource modules
  store/        # Zustand (devices list state)
  hooks/        # Auth context
  pages/        # Routes
  components/
```
