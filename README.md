````markdown
# 🚀 Pre-entrega 7: API de producción y monitoreo activo

## 📌 Descripción

Este proyecto implementa una **API REST asíncrona** construida con **FastAPI** que expone un agente autónomo basado en **LangGraph**, capaz de ejecutar tareas mediante un flujo de razonamiento cíclico.

La **API** está diseñada para trabajar de forma **no bloqueante**: cuando el usuario crea una tarea, recibe inmediatamente un `job_id` que permite consultar posteriormente su estado.

### Características principales

- ⚡ Ejecución asíncrona de tareas.
- 🧠 Agente autónomo con LangGraph.
- 💾 Persistencia de estados y checkpoints mediante Redis.
- 🧑‍⚖️ Human-in-the-loop (HITL) para tareas que requieren aprobación.
- 📊 Observabilidad mediante LangSmith / Arize Phoenix.
- 🐳 Docker Compose para ejecutar Redis y la API.
- ❤️ Endpoint de health check.
- 🔄 Manejo de errores y estado `FAILED`.

---

## 🏗️ Arquitectura

```mermaid
flowchart TD
    A[Cliente] -->|POST /tasks| B[FastAPI]
    B --> C[Genera job_id]
    C --> D[Encola tarea]
    D --> E[Responde inmediatamente]

    D --> F[Worker]
    F --> G[LangGraph]

    G --> H{¿Requiere aprobación?}

    H -->|No| I[Tools / LLM]
    H -->|Sí| J[HITL]

    J --> K{Aprobación humana}

    K -->|Aprobado| I
    K -->|Rechazado| L[CANCELLED]

    I --> M[DONE]
    I -->|Error| N[FAILED]

    F --> O[Redis]
    G --> O
    J --> O

    G --> P[LangSmith / Phoenix]
````

---

## 📁 Estructura del proyecto

```text
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
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 📡 Endpoints

### `POST /tasks`

Crea una nueva tarea y devuelve un `job_id`.

**Request:**

```http
POST /tasks
Content-Type: application/json
```

**Body:**

```json
{
  "query": "Analizá los pedidos del cliente 102"
}
```

**Response:**

```json
{
  "job_id": "abc123",
  "status": "PENDING"
}
```

---

### `GET /tasks/{job_id}`

Consulta el estado de una tarea.

**Request:**

```http
GET /tasks/abc123
```

**Response — en ejecución:**

```json
{
  "job_id": "abc123",
  "status": "RUNNING"
}
```

**Response — finalizada:**

```json
{
  "job_id": "abc123",
  "status": "DONE",
  "result": "Tarea completada correctamente"
}
```

---

### `POST /tasks/{job_id}/approve`

Aprueba o rechaza una tarea en espera de aprobación humana.

**Request:**

```http
POST /tasks/abc123/approve
Content-Type: application/json
```

**Body — aprobar:**

```json
{
  "approved": true
}
```

**Body — rechazar:**

```json
{
  "approved": false
}
```

---

### `GET /health`

Verifica el estado de la API y Redis.

**Request:**

```http
GET /health
```

**Response:**

```json
{
  "status": "ok",
  "redis": "connected"
}
```

---

## 📊 Estados de las tareas

| Estado             | Descripción                     |
| ------------------ | ------------------------------- |
| `PENDING`          | 📥 Tarea encolada               |
| `RUNNING`          | ⚙️ Tarea en ejecución           |
| `DONE`             | ✅ Tarea completada exitosamente |
| `FAILED`           | ❌ La tarea falló                |
| `PENDING_APPROVAL` | ⏸️ Esperando aprobación humana  |
| `APPROVED`         | ✅ Tarea aprobada                |
| `CANCELLED`        | 🚫 Tarea rechazada              |

---

## ⚙️ Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone <https://github.com/aaguuscaan/mi-api-agente>
cd mi-api-agente
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

**Windows:**

```bash
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales.

### 5. Ejecutar la API

```bash
uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://localhost:8000
```

---

## 📦 Dependencias

```text
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
redis>=4.5.0
langgraph>=0.0.20
langchain>=0.1.0
langchain-openai>=0.1.0
python-dotenv>=0.1.0
pydantic>=2.0.0
langsmith>=0.0.50
```

---

## 🐳 Docker Compose

El proyecto incluye un archivo `docker-compose.yml` para ejecutar Redis y la API mediante Docker Compose.

Para construir e iniciar los servicios:

```bash
docker compose up --build
```

Para ejecutarlos en segundo plano:

```bash
docker compose up -d --build
```

---

## ❤️ Health Check

Una vez iniciada la aplicación, se puede verificar que la API y Redis estén funcionando correctamente mediante:

```http
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "redis": "connected"
}
```

---

## 📊 Observabilidad

El proyecto incorpora herramientas de observabilidad para monitorear la ejecución del agente y analizar sus trazas:

* **LangSmith**
* **Arize Phoenix**

Las trazas permiten observar el flujo de ejecución de LangGraph, incluyendo las herramientas utilizadas, los estados intermedios y posibles errores.

Las capturas del dashboard pueden almacenarse en:

```text
screenshots/
```

---

## 🧑‍⚖️ Human-in-the-loop (HITL)

Algunas tareas pueden requerir una aprobación humana antes de continuar con su ejecución.

El flujo es:

```text
PENDING
   ↓
RUNNING
   ↓
PENDING_APPROVAL
   ↓
   ├── APPROVED → continúa la ejecución → DONE
   │
   └── RECHAZADO → CANCELLED
```

Esto permite que el agente pueda detenerse temporalmente y esperar una decisión humana antes de ejecutar determinadas acciones.

---

## 🔄 Manejo de errores

Si durante la ejecución ocurre un error, la tarea pasa al estado:

```text
FAILED
```

Esto permite diferenciar entre:

* Tareas pendientes.
* Tareas en ejecución.
* Tareas esperando aprobación.
* Tareas completadas.
* Tareas rechazadas.
* Tareas que fallaron.

