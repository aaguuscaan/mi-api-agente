````markdown
# 📊 Capturas de Observabilidad - Simulación

Este archivo documenta las capturas de pantalla del dashboard de observabilidad que se generarían al ejecutar el sistema.

---

## 🧠 Traza del agente (simulación)

```text
🚀 EJECUCIÓN DE AGENTE - LangSmith Trace

┌─────────────────────────────────────────────────────────────┐
│ 📋 Run ID: 8f7a3e2b-1c4d-5e6f-7a8b-9c0d1e2f3a4b           │
│ 📝 Nombre: Agente de razonamiento cíclico                  │
│ ⏱️ Duración: 2.34s                                         │
│ 💰 Costo: $0.0012                                          │
│ 📊 Tokens: 1,245 (input) + 342 (output)                   │
└─────────────────────────────────────────────────────────────┘

📋 DETALLE DE PASOS:

┌─────────────────────────────────────────────────────────────┐
│ 🔹 PASO 1: Nodo 'agent'                                    │
│ → LLM: GPT-4o                                               │
│ → Decisión: Usar herramienta buscar_pedidos                │
│ → Tiempo: 0.89s                                             │
├─────────────────────────────────────────────────────────────┤
│ 🔹 PASO 2: Nodo 'tools'                                    │
│ → Herramienta: buscar_pedidos(cliente_id=102)              │
│ → Resultado: "📦 Pedidos para el cliente 102..."            │
│ → Tiempo: 0.12s                                             │
├─────────────────────────────────────────────────────────────┤
│ 🔹 PASO 3: Nodo 'agent'                                    │
│ → LLM: GPT-4o                                               │
│ → Decisión: Generar respuesta final                        │
│ → Tiempo: 1.33s                                             │
└─────────────────────────────────────────────────────────────┘

✅ ESTADO FINAL: DONE

📝 RESPUESTA:
"📦 Pedidos para el cliente 102: ..."
````

---

## 📊 Dashboard de LangSmith (simulación visual)

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║ 🧠 LANGCHAIN TRACING V2 - PROYECTO: pre-entrega-7                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ ┌─────────────────────────────────────────────────────────────────────────┐  ║
║ │ 🔍 BUSCADOR DE TRAZAS                         │ 📅 Últimas 24h │        │  ║
║ │                                                                       │  ║
║ │ ┌─────────────────────────────────────────────────┐                  │  ║
║ │ │ 8f7a3e2b... │ ✅ DONE    │ Agente de pedidos │ 2.34s │ 💰 │       │  ║
║ │ │ a1b2c3d4... │ ✅ DONE    │ Consulta de clima │ 1.87s │ 💰 │       │  ║
║ │ │ e5f6g7h8... │ ⏳ RUNNING │ Análisis de ventas│ 5.12s │ 💰 │       │  ║
║ │ └─────────────────────────────────────────────────┘                  │  ║
║ └─────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
║ 📊 MÉTRICAS DE PROYECTO                                                     ║
║                                                                              ║
║ ┌───────────────┬───────────────┬───────────────┬───────────────────────┐  ║
║ │ Total Runs    │ Avg Latency   │ Total Cost    │ Success Rate          │  ║
║ │ 142           │ 2.1s          │ $0.18         │ 98.2%                 │  ║
║ └───────────────┴───────────────┴───────────────┴───────────────────────┘  ║
║                                                                              ║
║ 📈 GRÁFICO DE LATENCIA POR NODO                                             ║
║                                                                              ║
║ agent ████████████████████████████████████████████████ 1.8s                ║
║ tools ████████████████████████████ 1.2s                                    ║
║ hitl  ██████████████████████ 0.8s                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 📝 Nota

Las capturas y métricas mostradas en este archivo son una **simulación visual** del dashboard de observabilidad.

Los valores de `Run ID`, duración, costos, tokens y métricas son ejemplos representativos y se generarían de forma real al ejecutar el sistema con LangSmith.

---

