# app/hitl.py
import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.worker import get_worker
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

approval_router = APIRouter(prefix="/tasks", tags=["approval"])

class ApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None

@approval_router.post("/{job_id}/approve")
async def approve_task(job_id: str, request: ApprovalRequest):
    """
    Endpoint para aprobar o rechazar una tarea pausada.
    """
    # 1. Obtener el estado actual
    worker = await get_worker(REDIS_URL)
    task_data = await worker.get_task_status(job_id)
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if task_data.get("status") != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail="La tarea no está esperando aprobación"
        )
    
    # 2. Guardar la decisión
    approval_key = f"approval:{job_id}"
    await worker.redis_client.setex(
        approval_key,
        3600,
        json.dumps({
            "approved": request.approved,
            "comment": request.comment,
            "timestamp": datetime.now().isoformat()
        })
    )
    
    # 3. Si es aprobada, reanudar la ejecución
    if request.approved:
        # Actualizar estado
        await worker._update_status(job_id, "APPROVED", {
            "comment": request.comment
        })
        
        # Reanudar en segundo plano
        import asyncio
        asyncio.create_task(worker.resume_task(job_id))
        
        return {
            "status": "approved",
            "message": "✅ Tarea aprobada. La ejecución continuará en segundo plano."
        }
    else:
        # Si es rechazada, marcar como cancelada
        await worker._update_status(job_id, "CANCELLED", {
            "reason": request.comment or "Rechazada por el usuario"
        })
        return {
            "status": "rejected",
            "message": "❌ Tarea rechazada. La ejecución se ha cancelado."
        }