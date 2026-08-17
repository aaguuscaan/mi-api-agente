# app/worker.py
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage
import redis.asyncio as redis

from app.graph import create_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskWorker:
    """
    Worker que ejecuta tareas en segundo plano y actualiza el estado en Redis.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.graph = None
    
    async def initialize(self):
        """Inicializa conexiones."""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        
        # Crear grafo con RedisSaver
        try:
            from langgraph.checkpoint.redis import RedisSaver
            saver = RedisSaver.from_conn_string(self.redis_url)
            self.graph = create_graph(checkpointer=saver)
            logger.info(f"✅ RedisSaver configurado en: {self.redis_url}")
        except ImportError:
            logger.warning("⚠️ RedisSaver no disponible, usando MemorySaver")
            from langgraph.checkpoint.memory import MemorySaver
            saver = MemorySaver()
            self.graph = create_graph(checkpointer=saver)
        except Exception as e:
            logger.error(f"❌ Error configurando RedisSaver: {e}")
            from langgraph.checkpoint.memory import MemorySaver
            saver = MemorySaver()
            self.graph = create_graph(checkpointer=saver)
            logger.warning("⚠️ Usando MemorySaver (sin persistencia real)")
        
        logger.info("✅ Worker inicializado correctamente")
    
    async def run_task(self, task_id: str, query: str, thread_id: Optional[str] = None):
        """
        Ejecuta una tarea en segundo plano y actualiza el estado en Redis.
        """
        try:
            # 1. Actualizar estado a RUNNING
            await self._update_status(task_id, "RUNNING")
            
            # 2. Configurar thread_id
            if not thread_id:
                thread_id = f"thread_{task_id}"
            config = {"configurable": {"thread_id": thread_id}}
            
            # 3. Ejecutar el agente
            logger.info(f"🚀 Ejecutando tarea {task_id}: '{query[:50]}...'")
            
            result = await self.graph.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config=config,
                recursion_limit=10
            )
            
            # 4. Extraer la respuesta final
            final_response = result["messages"][-1].content
            
            # 5. Guardar resultado
            await self._update_status(task_id, "DONE", {
                "response": final_response,
                "thread_id": thread_id,
                "steps": len(result["messages"])
            })
            
            logger.info(f"✅ Tarea {task_id} completada")
            
        except Exception as e:
            # 6. Manejar errores
            error_msg = str(e)
            logger.error(f"❌ Error en tarea {task_id}: {error_msg}")
            await self._update_status(task_id, "FAILED", {
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _update_status(self, task_id: str, status: str, data: Dict[str, Any] = None):
        """
        Actualiza el estado de la tarea en Redis.
        """
        key = f"task:{task_id}"
        task_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if data:
            task_data.update(data)
        
        # Guardar en Redis con expiración de 1 hora
        await self.redis_client.setex(
            key,
            3600,  # 1 hora
            json.dumps(task_data)
        )
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una tarea desde Redis.
        """
        key = f"task:{task_id}"
        data = await self.redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def resume_task(self, task_id: str):
        """
        Reanuda una tarea pausada (para HITL).
        """
        task_data = await self.get_task_status(task_id)
        if not task_data:
            return
        
        thread_id = task_data.get("thread_id")
        if not thread_id:
            return
        
        # Actualizar estado a RUNNING
        await self._update_status(task_id, "RUNNING")
        
        # Continuar la ejecución del grafo
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Reanudar desde el punto de interrupción
            result = await self.graph.ainvoke(
                None,
                config=config,
            )
            
            # Actualizar con resultado
            final_response = result["messages"][-1].content
            await self._update_status(task_id, "DONE", {
                "response": final_response,
                "thread_id": thread_id,
                "steps": len(result["messages"])
            })
            
            logger.info(f"✅ Tarea {task_id} reanudada y completada")
            
        except Exception as e:
            logger.error(f"❌ Error reanudando tarea {task_id}: {e}")
            await self._update_status(task_id, "FAILED", {"error": str(e)})

# Worker global
_worker: Optional[TaskWorker] = None

async def get_worker(redis_url: str) -> TaskWorker:
    """
    Obtiene el worker global (singleton).
    """
    global _worker
    if _worker is None:
        _worker = TaskWorker(redis_url)
        await _worker.initialize()
    return _worker