# app/graph.py
import json
import logging
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.tools import tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# 1. ESTADO
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    # Campos específicos para HITL
    needs_approval: bool
    approved: bool
    approval_message: str

# ============================================================
# 2. MODELO
# ============================================================

model = ChatOpenAI(model="gpt-4o", temperature=0)
model_with_tools = model.bind_tools(tools)

# ============================================================
# 3. NODOS
# ============================================================

async def call_model(state: AgentState):
    """Nodo que invoca el LLM."""
    response = await model_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

async def approval_node(state: AgentState):
    """
    Nodo de aprobación humana (HITL).
    Pausa la ejecución hasta que se apruebe manualmente.
    """
    logger.info("⏸️ Ejecución pausada. Esperando aprobación humana...")
    
    return {
        "needs_approval": True,
        "approved": False,
        "approval_message": "Se requiere aprobación para ejecutar la herramienta de descuento."
    }

async def after_approval(state: AgentState):
    """Nodo que se ejecuta después de la aprobación."""
    logger.info("✅ Aprobación recibida. Continuando ejecución...")
    return {"approved": True}

# ============================================================
# 4. CONDICIONALES
# ============================================================

def should_approve(state: AgentState) -> Literal["approval", "tools", "__end__"]:
    """
    Decide si se necesita aprobación humana.
    """
    # Verificar si hay una solicitud de descuento
    for msg in state["messages"]:
        if hasattr(msg, "content") and msg.content:
            if "descuento" in msg.content.lower() or "vip" in msg.content.lower():
                # Si ya fue aprobada, seguir a herramientas
                if state.get("approved", False):
                    return "tools"
                # Si no, pedir aprobación
                return "approval"
    
    # Si no hay herramienta crítica, continuar
    return "tools"

def after_approval_route(state: AgentState) -> Literal["tools", "__end__"]:
    """Ruta después de la aprobación."""
    if state.get("approved", False):
        return "tools"
    return "__end__"

# ============================================================
# 5. CONSTRUCCIÓN DEL GRAFO
# ============================================================

def create_graph(checkpointer=None):
    """
    Crea el grafo con el checkpointer proporcionado.
    """
    workflow = StateGraph(AgentState)
    
    # Nodos
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("approval", approval_node)
    workflow.add_node("after_approval", after_approval)
    
    # Aristas
    workflow.add_edge(START, "agent")
    
    # Arista condicional desde el agente
    workflow.add_conditional_edges(
        "agent",
        should_approve,
        {
            "approval": "approval",
            "tools": "tools",
            "__end__": END
        }
    )
    
    # Arista condicional desde approval
    workflow.add_conditional_edges(
        "approval",
        after_approval_route,
        {
            "tools": "tools",
            "__end__": END
        }
    )
    
    # Después de tools, volver al agente
    workflow.add_edge("tools", "agent")
    
    # Compilar con checkpointer si se proporciona
    if checkpointer:
        app = workflow.compile(checkpointer=checkpointer)
        logger.info("✅ Grafo compilado con checkpointer")
    else:
        app = workflow.compile()
        logger.info("✅ Grafo compilado sin checkpointer")
    
    return app