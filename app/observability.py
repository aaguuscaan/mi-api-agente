# app/observability.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_observability():
    """
    Configura la instrumentación para observabilidad.
    Soporta LangSmith y Arize Phoenix.
    """
    # Intentar LangSmith primero
    langsmith_api_key = os.getenv("LANGCHAIN_API_KEY")
    if langsmith_api_key:
        try:
            import langsmith
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "agente-produccion")
            logger.info("✅ LangSmith configurado correctamente")
            logger.info(f"   Project: {os.environ['LANGCHAIN_PROJECT']}")
            return
        except ImportError:
            logger.warning("⚠️ LangSmith no disponible, intentando Phoenix...")
    
    # Intentar Arize Phoenix
    phoenix_endpoint = os.getenv("PHOENIX_ENDPOINT")
    if phoenix_endpoint:
        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor
            from phoenix.otel import register
            tracer_provider = register(endpoint=phoenix_endpoint)
            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info(f"✅ Arize Phoenix configurado (endpoint: {phoenix_endpoint})")
            return
        except ImportError:
            logger.warning("⚠️ Arize Phoenix no disponible")
    
    logger.info("ℹ️ Observabilidad no configurada (modo sin trazas)")