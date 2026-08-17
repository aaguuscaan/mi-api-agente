# app/main.py
import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.worker import get_worker
from app.observability import setup_observability
from app.hitl import approval_router

# ============================================================
# CONFIGURACIÓN
# ============================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Configurar observabilidad
setup_observability()

# ============================================================
# FASTAPI
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    # Inicializar worker al iniciar
    await get_worker(REDIS_URL)
    print("🚀 Worker inicializado")
    yield
    # Cerrar conexiones al apagar
    print("🛑 Cerrando conexiones...")

app = FastAPI(
    title="Agente RAG API",
    description="API asíncrona para agente con razonamiento cíclico, Redis y HITL",
    version="1.0.0",
    lifespan=lifespan
)

# Incluir router de aprobación
app.include_router(approval_router)

# ============================================================
# MODELOS
# ============================================================

class TaskRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None

class TaskResponse(BaseModel):
    job_id: str
    status: str = "PENDING"
    message: str = "Tarea encolada correctamente"

class TaskStatusResponse(BaseModel):
    job_id: str
    status: str
    response: Optional[str] = None
    thread_id: Optional[str] = None
    error: Optional[str] = None

# ============================================================
# ENDPOINTS
# ============================================================

@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Crea una tarea y la encola para ejecución asíncrona.
    """
    # 1. Generar ID único
    job_id = str(uuid.uuid4())
    
    # 2. Guardar estado inicial en Redis
    worker = await get_worker(REDIS_URL)
    await worker._update_status(job_id, "PENDING")
    
    # 3. Encolar la tarea en segundo plano
    background_tasks.add_task(
        worker.run_task,
        job_id,
        request.query,
        request.thread_id
    )
    
    return TaskResponse(
        job_id=job_id,
        status="PENDING",
        message="Tarea encolada correctamente"
    )

@app.get("/tasks/{job_id}", response_model=TaskStatusResponse)
async def get_task_status(job_id: str):
    """
    Consulta el estado de una tarea.
    """
    worker = await get_worker(REDIS_URL)
    task_data = await worker.get_task_status(job_id)
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return TaskStatusResponse(
        job_id=job_id,
        status=task_data.get("status", "UNKNOWN"),
        response=task_data.get("response"),
        thread_id=task_data.get("thread_id"),
        error=task_data.get("error")
    )

@app.get("/health")
async def health_check():
    """Verifica el estado de la API y Redis."""
    try:
        worker = await get_worker(REDIS_URL)
        await worker.redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}

# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)