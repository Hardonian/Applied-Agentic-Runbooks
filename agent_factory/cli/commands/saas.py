"""
CLI commands for SaaS scaffold generation - Complete implementation.
"""

from pathlib import Path

import typer

from agent_factory.blueprints.loader import BlueprintLoader

app = typer.Typer(name="saas", help="SaaS scaffold generation commands")


@app.command()
def create(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
    output: str = typer.Option("./apps", "--output", "-o", help="Output directory"),
):
    """Create SaaS scaffold from blueprint."""
    output_path = Path(output) / blueprint_id

    try:
        # Try to load blueprint
        blueprint_path = Path(f"blueprints/{blueprint_id}/blueprint.yaml")
        if blueprint_path.exists():
            loader = BlueprintLoader()
            blueprint = loader.load(str(blueprint_path))
        else:
            # Create placeholder blueprint
            blueprint = None

        output_path.mkdir(parents=True, exist_ok=True)

        # Generate backend
        _generate_backend(output_path, blueprint_id, blueprint)

        # Generate frontend
        _generate_frontend(output_path, blueprint_id, blueprint)

        # Generate Docker configs
        _generate_docker(output_path, blueprint_id)

        # Generate README
        _generate_readme(output_path, blueprint_id, blueprint)

        typer.echo(f"✅ SaaS scaffold created at: {output_path}")
        typer.echo("\nNext steps:")
        typer.echo(f"  1. cd {output_path}")
        typer.echo("  2. Copy .env.example to .env and configure")
        typer.echo("  3. docker-compose up")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1) from e


def _generate_backend(output_path: Path, blueprint_id: str, blueprint) -> None:
    """Generate FastAPI backend."""
    backend_dir = output_path / "backend"
    backend_dir.mkdir(exist_ok=True)

    # main.py
    main_py = """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Agent SaaS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    input: str
    session_id: Optional[str] = None


class RunResponse(BaseModel):
    output: str
    status: str


@app.get("/")
def root():
    return {"message": "Agent SaaS API", "status": "running"}


@app.post("/api/v1/agents/{agent_id}/run", response_model=RunResponse)
async def run_agent(agent_id: str, request: RunRequest):
    # Integrate with agent_factory runtime
    from agent_factory.runtime.engine import RuntimeEngine
    from agent_factory.registry.local_registry import LocalRegistry
    
    runtime = RuntimeEngine()
    registry = LocalRegistry()
    
    # Load agent if not already registered
    agent = runtime.agents_registry.get(agent_id)
    if not agent:
        agent = registry.get_agent(agent_id)
        if agent:
            runtime.register_agent(agent)
        else:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    # Run agent
    try:
        execution_id = runtime.run_agent(
            agent_id=agent_id,
            input_text=request.input,
            session_id=request.session_id,
        )
        execution = runtime.get_execution(execution_id)
        
        if execution and execution.status == "completed":
            result = execution.result
            output = result.output if hasattr(result, "output") else str(result)
            return RunResponse(output=output, status="success")
        else:
            error = execution.error if execution else "Execution failed"
            return RunResponse(output=error, status="error")
    except Exception as e:
        return RunResponse(output=str(e), status="error")


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    (backend_dir / "main.py").write_text(main_py)

    # requirements.txt
    requirements = """fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.5.0
python-dotenv>=1.0.0
agent-factory>=0.1.0
"""
    (backend_dir / "requirements.txt").write_text(requirements)

    # Dockerfile
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    (backend_dir / "Dockerfile").write_text(dockerfile)


def _generate_frontend(output_path: Path, blueprint_id: str, blueprint) -> None:
    """Generate React frontend."""
    frontend_dir = output_path / "frontend"
    frontend_dir.mkdir(exist_ok=True)

    # Use UI generator
    from agent_factory.ui.generator import generate_ui

    generate_ui(blueprint_id, str(frontend_dir), template="react")

    # Add Dockerfile
    dockerfile = """FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
    (frontend_dir / "Dockerfile").write_text(dockerfile)


def _generate_docker(output_path: Path, blueprint_id: str) -> None:
    """Generate Docker Compose configuration."""
    docker_compose = """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
"""
    (output_path / "docker-compose.yml").write_text(docker_compose)

    # .env.example
    env_example = """# API Keys
OPENAI_API_KEY=your-openai-api-key-here

# Environment
ENVIRONMENT=production

# Backend
BACKEND_URL=http://localhost:8000
"""
    (output_path / ".env.example").write_text(env_example)


def _generate_readme(output_path: Path, blueprint_id: str, blueprint) -> None:
    """Generate README."""
    readme = f"""# {blueprint_id.replace('-', ' ').title()} SaaS Application

SaaS application generated from blueprint: {blueprint_id}

## Structure

- `backend/` - FastAPI backend
- `frontend/` - React frontend
- `docker-compose.yml` - Docker configuration
- `.env.example` - Environment variables template

## Quick Start

1. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

2. Start services:
   ```bash
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Deployment

See deployment documentation for production deployment instructions.

## Configuration

Update API endpoints in `frontend/src/App.js` if needed.

## License

See LICENSE file.
"""
    (output_path / "README.md").write_text(readme)
