
# zanella_project

TODO: Create description

Quick start (Windows PowerShell, using Poetry):


## Authentication

[Google Auth Quickstart](https://developers.google.com/workspace/sheets/api/quickstart/python?hl=pt-br) is needed for this project.



## Local setup (UV)

1. Create a virtual environment and activate it
2. [Install UV](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) and make sure it's in your path
3. `uv sync`


## Run in Docker

The project includes `Dockerfile` (development with auto-reload) and `Dockerfile.prod` (production with Gunicorn). Both use UV to manage dependencies from `pyproject.toml` and `uv.lock`.

### Development (with docker compose)

```powershell
# Start the development server with hot-reload
docker compose up --build

# Or run in detached mode
docker compose up -d --build

# Stop and remove volumes
docker compose down -v
```

### Production

```powershell
# Build and run the production image
docker build -f Dockerfile.prod -t zanella_project:prod .
docker run --rm -p 8000:8000 zanella_project:prod
```

The app will be available at `http://localhost:8000` with the health check at `http://localhost:8000/health`.