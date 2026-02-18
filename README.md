Run with Docker
==========================

Short description
-----------------
All services run via Docker Compose — frontend (port 3000) and backend (port 8000).

Access
-----
Once the services are running, you can access:
- Frontend (Sensor Dashboard): http://localhost:3000
- Backend API: http://localhost:8000

Prerequisites
-------------
- Docker Desktop (Windows/macOS) or Docker Engine + Docker Compose (Linux)
- Docker must be running

Run (build + start)
-------------------
From project root (where `docker-compose.yml` is located):

```bash
docker compose up --build -d
```
