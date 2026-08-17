API de producción y monitoreo activo
📌 Descripción

Este proyecto implementa una API REST asíncrona construida con FastAPI que expone un agente autónomo basado en LangGraph, capaz de ejecutar tareas mediante un flujo de razonamiento cíclico.

La API está diseñada para trabajar de forma no bloqueante: cuando el usuario crea una tarea, recibe inmediatamente un job_id que permite consultar posteriormente su estado.

Además, el sistema incorpora:

⚡ Ejecución asíncrona de tareas.
🧠 Agente autónomo con LangGraph.
💾 Persistencia de estados y checkpoints mediante Redis.
🧑‍⚖️ Human-in-the-loop (HITL) para tareas que requieren aprobación.
📊 Observabilidad mediante LangSmith / Arize Phoenix.
🐳 Docker Compose para ejecutar Redis y la API.
❤️ Endpoint de health check.
🔄 Manejo de errores y estado FAILED.
🏗️ Arquitectura

El funcionamiento general del sistema puede representarse de la siguiente manera:

flowchart TD
    A[👤 Cliente] -->|POST /tasks| B[🚀 FastAPI]
    
    B --> C[🆔 Genera job_id]
    C --> D[📥 Encola tarea]
    D --> E[📤 Responde inmediatamente]

    D --> F[⚙️ Worker]
    F --> G[🧠 LangGraph]

    G --> H{¿Requiere aprobación?}

    H -->|No| I[🔧 Tools / LLM]
    H -->|Sí| J[⏸️ HITL]

    J --> K{👤 Aprobación humana}

    K -->|Aprobado| I
    K -->|Rechazado| L[❌ CANCELLED]

    I --> M[✅ DONE]
    I -->|Error| N[❌ FAILED]

    F --> O[(💾 Redis)]
    G --> O
    J --> O

    G --> P[📊 LangSmith / Phoenix]
🔄 Flujo de ejecución

El sistema funciona mediante un flujo desacoplado entre la API y la ejecución de las tareas.

1. 📥 Creación de tarea

El cliente realiza:

POST /tasks

La API genera un job_id, registra la tarea como PENDING y devuelve la respuesta sin esperar a que termine la ejecución.

2. ⚙️ Ejecución

El worker toma la tarea y cambia su estado a:

RUNNING

Luego ejecuta el grafo de LangGraph.

3. 🧠 Procesamiento del agente

El agente puede utilizar herramientas y modelos de lenguaje para completar la tarea.

4. 🧑‍⚖️ Human-in-the-loop

Si la tarea requiere una decisión humana, el grafo se pausa y pasa al estado:

PENDING_APPROVAL

La ejecución queda detenida hasta recibir una aprobación o rechazo mediante:

POST /tasks/{job_id}/approve
5. ✅ Finalización

Si todo sale correctamente:

DONE

Si ocurre una excepción:

FAILED

Si una tarea que esperaba aprobación es rechazada:

CANCELLED
📁 Estructura del proyecto
mi-api-agente/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI: endpoints asíncronos
│   ├── graph.py             # Orquestador con RedisSaver y HITL
│   ├── worker.py            # Ejecución en segundo plano
│   ├── observability.py     # Configuración de trazas
│   ├── hitl.py              # Nodo de aprobación humana
│   └── tools.py             # Herramientas del agente
│
├── screenshots/             # Capturas del dashboard
│   └── .gitkeep             # Mantiene la carpeta en Git
│
├── .env.example             # Variables de entorno
├── .gitignore               # Archivos ignorados por Git
├── docker-compose.yml       # Redis + API
├── requirements.txt         # Dependencias
└── README.md                # Documentación
🛠️ Tecnologías utilizadas
Tecnología	Uso
🐍 Python	Lenguaje principal
⚡ FastAPI	API REST asíncrona
🧠 LangGraph	Orquestación del agente
🔗 LangChain	Herramientas y modelos
🤖 OpenAI	Modelo GPT-4o
💾 Redis	Persistencia de estados y checkpoints
📊 LangSmith	Observabilidad
🔬 Arize Phoenix	Observabilidad y trazas
🐳 Docker Compose	Infraestructura
🚀 Uvicorn	Servidor ASGI
📡 Endpoints
1. POST /tasks

Crea una nueva tarea.

La API no espera a que termine la ejecución, sino que devuelve inmediatamente un identificador de trabajo.

Request
POST /tasks
Content-Type: application/json

Ejemplo:

{
  "prompt": "Analizá los pedidos del cliente 102"
}
Response
{
  "job_id": "abc123",
  "status": "PENDING"
}

El job_id se utiliza posteriormente para consultar o controlar la tarea.

2. GET /tasks/{job_id}

Permite consultar el estado actual de una tarea.

Ejemplo:

GET /tasks/abc123

Response:

{
  "job_id": "abc123",
  "status": "RUNNING"
}

Cuando finaliza:

{
  "job_id": "abc123",
  "status": "DONE",
  "result": "Tarea completada correctamente"
}
3. POST /tasks/{job_id}/approve

Permite aprobar o rechazar una tarea que está esperando intervención humana.

Aprobar
POST /tasks/abc123/approve
Content-Type: application/json
{
  "approved": true
}
Rechazar
{
  "approved": false
}

La decisión humana permite que el flujo continúe o finalice.

4. GET /health

Comprueba el estado de la API y la conexión con Redis.

GET /health

Ejemplo de respuesta:

{
  "status": "ok",
  "redis": "connected"
}

Este endpoint permite verificar rápidamente si los servicios principales están funcionando correctamente.

📊 Estados de las tareas

Una tarea puede pasar por los siguientes estados:

Estado	Descripción
PENDING	📥 Tarea encolada
RUNNING	⚙️ Tarea en ejecución
DONE	✅ Tarea completada exitosamente
FAILED	❌ La tarea falló
PENDING_APPROVAL	⏸️ Esperando aprobación humana
APPROVED	✅ Tarea aprobada
CANCELLED	🚫 Tarea rechazada
Flujo simplificado
PENDING
   │
   ▼
RUNNING
   │
   ├───────────────► FAILED
   │
   ▼
PENDING_APPROVAL
   │
   ├── aprobado ──► APPROVED ──► DONE
   │
   └── rechazado ─► CANCELLED
🧑‍⚖️ Human-in-the-loop (HITL)

El sistema incorpora un mecanismo Human-in-the-loop para evitar que determinadas tareas críticas sean ejecutadas automáticamente sin supervisión.

Cuando el agente llega al nodo HITL, la ejecución se pausa:

Agente
  ↓
¿Tarea crítica?
  ↓
Sí
  ↓
PENDING_APPROVAL
  ↓
⏸️ Ejecución pausada
  ↓
👤 Decisión humana
  ↓
┌───────────────┐
│               │
▼               ▼
APROBAR       RECHAZAR
│               │
▼               ▼
Continuar     CANCELLED

La aprobación se realiza externamente mediante:

POST /tasks/{job_id}/approve

Esto permite separar la toma de decisiones automática de las acciones que requieren supervisión humana.

💾 Persistencia con Redis

Redis se utiliza para mantener el estado de las tareas y los checkpoints necesarios para el funcionamiento del agente.

Esto permite que el sistema conserve información como:

job_id
Estado actual.
Resultado.
Errores.
Checkpoints del grafo.
Estado necesario para continuar una ejecución pausada.

La persistencia es especialmente importante para HITL, ya que el agente puede quedar pausado esperando una decisión externa.

⚠️ Manejo de errores

Si durante la ejecución ocurre una excepción, la tarea debe pasar a:

FAILED

Por ejemplo:

PENDING
   ↓
RUNNING
   ↓
❌ Excepción
   ↓
FAILED

Esto permite consultar posteriormente el estado de una tarea fallida mediante:

GET /tasks/{job_id}
📊 Observabilidad

El proyecto incorpora herramientas de observabilidad para poder analizar la ejecución del agente.

Se utilizan:

LangSmith
Arize Phoenix

Estas herramientas permiten visualizar información relacionada con las ejecuciones y las trazas del agente.

La configuración se encuentra centralizada en:

app/observability.py
📸 Capturas del dashboard

Las capturas relacionadas con la observabilidad deben almacenarse en:

screenshots/

Por ejemplo:

screenshots/
├── dashboard.png
├── trace.png
└── execution.png

Estas capturas sirven como evidencia visual de las trazas generadas por el sistema.

⚠️ Actualmente la carpeta screenshots/ puede estar vacía. Para completar el punto de observabilidad de la entrega, se deben agregar las capturas correspondientes al dashboard utilizado.

🐳 Docker Compose

El proyecto utiliza Docker Compose para levantar los servicios necesarios.

La configuración se encuentra en:

docker-compose.yml

El objetivo principal es ejecutar:

┌───────────────┐
│   Docker      │
│               │
│ ┌───────────┐ │
│ │ FastAPI   │ │
│ └─────┬─────┘ │
│       │       │
│ ┌─────▼─────┐ │
│ │   Redis   │ │
│ └───────────┘ │
└───────────────┘
⚙️ Instalación y configuración
1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd mi-api-agente

Reemplazá <URL_DEL_REPOSITORIO> por la URL real de tu repositorio.

2. Crear el archivo .env

Copiá el archivo de ejemplo:

Windows
copy .env.example .env
Linux / macOS
cp .env.example .env

Después completá las variables necesarias.

Ejemplo:

OPENAI_API_KEY=tu_api_key
LANGCHAIN_API_KEY=tu_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=pre-entrega-7

Las variables exactas dependen de la configuración utilizada en observability.py.

🔐 Seguridad de variables de entorno

No subas nunca el archivo .env a GitHub.

El repositorio debe contener:

.env.example

pero no:

.env

El .env.example debe contener solamente nombres de variables y valores de ejemplo.

Por ejemplo:

OPENAI_API_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=
🚨 Nunca incluyas en el repositorio:
API keys.
Tokens.
Contraseñas.
Credenciales de Redis.
Credenciales de servicios externos.
🐳 Ejecutar con Docker Compose

Con Docker Desktop iniciado, ejecutá:

docker compose up --build

Esto construirá la imagen de la API y levantará los servicios definidos en docker-compose.yml.

Para ejecutar los servicios en segundo plano:

docker compose up --build -d

Para detenerlos:

docker compose down
🐍 Ejecutar localmente

Si querés ejecutar la API sin Docker para el servidor, primero instalá las dependencias:

pip install -r requirements.txt

Luego iniciá Uvicorn:

uvicorn app.main:app --reload

La API quedará disponible en:

http://localhost:8000
📚 Documentación automática de FastAPI

FastAPI genera automáticamente documentación interactiva.

Una vez iniciada la API, podés acceder a:

http://localhost:8000/docs

También está disponible la documentación alternativa:

http://localhost:8000/redoc

Desde /docs podés probar los endpoints directamente sin utilizar una herramienta externa.

🧪 Ejemplos de uso
Crear una tarea
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Analizá los pedidos del cliente 102\"}"

Respuesta:

{
  "job_id": "abc123",
  "status": "PENDING"
}
Consultar una tarea
curl http://localhost:8000/tasks/abc123

Respuesta:

{
  "job_id": "abc123",
  "status": "RUNNING"
}
Aprobar una tarea
curl -X POST http://localhost:8000/tasks/abc123/approve \
  -H "Content-Type: application/json" \
  -d "{\"approved\":true}"
Rechazar una tarea
curl -X POST http://localhost:8000/tasks/abc123/approve \
  -H "Content-Type: application/json" \
  -d "{\"approved\":false}"
Verificar el estado de la API
curl http://localhost:8000/health

Respuesta esperada:

{
  "status": "ok",
  "redis": "connected"
}
🧩 Componentes principales
app/main.py

Contiene la aplicación FastAPI y los endpoints HTTP.

Responsabilidades principales:

Crear tareas.
Devolver job_id.
Consultar estados.
Gestionar aprobaciones.
Exponer /health.
app/graph.py

Contiene el grafo principal del agente.

Se encarga de:

Configurar LangGraph.
Utilizar RedisSaver.
Definir el flujo de ejecución.
Integrar el nodo HITL.
Gestionar checkpoints.
app/worker.py

Se ocupa de la ejecución de las tareas en segundo plano.

Esto permite que:

POST /tasks

no tenga que esperar a que el agente termine.

app/observability.py

Centraliza la configuración relacionada con:

LangSmith.
Arize Phoenix.
Trazas.
Observabilidad de las ejecuciones.
app/hitl.py

Contiene la lógica relacionada con la aprobación humana.

Permite pausar el flujo y esperar una decisión externa.

app/tools.py

Contiene las herramientas que puede utilizar el agente durante su ejecución.

📦 Dependencias

Las dependencias del proyecto están definidas en:

requirements.txt

Para instalarlas:

pip install -r requirements.txt

Esto permite reproducir el entorno necesario para ejecutar la aplicación.

🩺 Health Check

El endpoint:

GET /health

permite comprobar el estado de los componentes principales.

Ejemplo:

{
  "status": "ok",
  "redis": "connected"
}

Este endpoint resulta útil para verificar que:

La API está funcionando.
Redis está disponible.
La aplicación puede comunicarse con el sistema de persistencia.