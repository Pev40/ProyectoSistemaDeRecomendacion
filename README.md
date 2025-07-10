# 🎬 Sistema de Recomendación de Películas TCD

Sistema de recomendación escalable basado en el modelo **gSASRec** (Self-Attention Sequential Recommendation) entrenado con el dataset **MovieLens 32M**, implementando una arquitectura distribuida con múltiples tecnologías de vanguardia.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   TorchServe    │
│   Next.js       │◄──►│   Backend       │◄──►│   (gSASRec)     │
│   (Puerto 3000) │    │   (Puerto 8000) │    │   (Puerto 8080) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MongoDB       │    │   Redis         │    │   FAISS Index   │
│   (Puerto 27017)│◄──►│   (Puerto 6379) │◄──►│   (In-Memory)   │
│   Datos Persist.│    │   Cache/Broker  │    │   Búsq. Rápida  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Qdrant        │    │   Celery        │
                       │   (Puerto 6333) │    │   Workers       │
                       │   DB Vectorial  │    │   Tareas Async  │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Componentes Principales

### 🎯 **Frontend (Next.js)**
- **Tecnología**: React/Next.js + TypeScript + Tailwind CSS
- **Funcionalidades**:
  - Dashboard de usuario con recomendaciones personalizadas
  - Sistema de autenticación y registro
  - Búsqueda avanzada de películas con filtros
  - Interfaz de onboarding para nuevos usuarios
  - Diseño responsivo y moderno

### 🔧 **Backend API (FastAPI)**
- **Tecnología**: Python FastAPI + Pydantic + Uvicorn
- **Endpoints Principales**:
  - `/recommend` - Recomendaciones personalizadas
  - `/recommend_batch` - Recomendaciones en lote
  - `/search_movies` - Búsqueda de películas
  - `/health` - Monitoreo del sistema
  - `/stats` - Estadísticas en tiempo real
- **Características**:
  - Documentación automática con Swagger
  - Validación de datos con Pydantic
  - Logging estructurado
  - Manejo de errores robusto

### 🧠 **Modelo de ML (gSASRec + TorchServe)**
- **Algoritmo**: gSASRec (Self-Attention Sequential Recommendation)
- **Dataset**: MovieLens 32M (~32 millones de ratings)
- **Características del Modelo**:
  - Arquitectura Transformer con self-attention
  - Embeddings de 256 dimensiones
  - Secuencias de hasta 200 películas
  - Entrenado con contrastive learning
- **Infraestructura**:
  - **TorchServe**: Servicio de modelos escalable
  - **Handler personalizado**: Preprocesamiento y postprocesamiento
  - **Múltiples estrategias**: TorchServe, FAISS, Qdrant

### 🗄️ **Bases de Datos**

#### **MongoDB (Datos Principales)**
- **Colecciones**:
  - `movies`: Metadatos de películas (título, géneros, año)
  - `users`: Información de usuarios
  - `ratings`: Calificaciones usuario-película
  - `interactions`: Historial de interacciones
- **Índices Optimizados**: Para consultas eficientes
- **Agregaciones**: Estadísticas en tiempo real

#### **Redis (Cache y Cola)**
- **Funciones**:
  - Cache de embeddings de usuarios frecuentes
  - Cache de metadatos de películas populares
  - Broker para Celery (tareas asíncronas)
  - Almacenamiento de sesiones de usuario
  - Rate limiting para API

#### **Qdrant (Base de Datos Vectorial)**
- **Características**:
  - Búsquedas vectoriales con filtros complejos
  - Colecciones especializadas:
    - `movies`: Embeddings de películas + metadata
    - `user_embeddings`: Embeddings de usuarios
    - `sequence_embeddings`: Embeddings de secuencias
  - **Filtros avanzados**: Por género, año, rating, director
  - **Escalabilidad**: Clustering y sharding

#### **FAISS (Índice de Búsqueda Rápida)**
- **Propósito**: Búsquedas ultrarrápidas de similitud coseno
- **Tipos de Índice**:
  - `IndexFlatIP`: Búsqueda exacta (desarrollo)
  - `IndexIVFFlat`: Para datasets medianos
  - `IndexHNSW`: Para datasets grandes (producción)
- **Optimizaciones**: Búsquedas en lote, normalización automática

### ⚙️ **Servicios de Soporte**

#### **Celery (Tareas Asíncronas)**
- **Workers**: Procesamiento en background
- **Tareas**:
  - Recálculo de embeddings de usuarios
  - Sincronización FAISS ↔ Qdrant
  - Limpieza de cache periódica
  - Generación de reportes
- **Flower**: Monitoreo de tareas en tiempo real

#### **Servicio de Sincronización**
- **Función**: Mantener consistencia entre FAISS y Qdrant
- **Programación**: Sincronización cada 6 horas
- **Monitoreo**: Métricas de salud del sistema

## 📊 Dataset: MovieLens 32M

### Estadísticas
- **Usuarios**: ~138,493
- **Películas**: ~84,436 (con padding para ML)
- **Calificaciones**: ~32,482,045
- **Géneros**: 20 categorías
- **Período**: 1995-2019
- **Densidad**: ~0.28% (matriz usuario-película)

### Preprocesamiento
- **Filtrado**: Usuarios con mínimo 5 ratings, películas con mínimo 10 ratings
- **Secuencias**: Ordenadas cronológicamente por usuario
- **Padding**: Token 0 para secuencias cortas
- **Negatives**: Muestreo negativo para entrenamiento

## 🛠️ Instalación y Configuración

### Prerrequisitos
- **Docker** y **Docker Compose**
- **Python 3.10+** (para desarrollo local)
- **Node.js 18+** (para frontend)
- **8GB+ RAM** disponible
- **GPU** opcional (acelera inferencia)

### Instalación Completa con Docker

1. **Clonar el repositorio**:
```bash
git clone https://github.com/Pev40/ProyectoSistemaDeRecomendacion.git
cd SistemaDeRecomendacionTCD
```

2. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. **Iniciar todos los servicios**:
```bash
docker-compose up --build
```

4. **Verificar servicios**:
```bash
# API de recomendación
curl http://localhost:8000/health

# TorchServe
curl http://localhost:8080/ping

# Frontend
curl http://localhost:3000

# Qdrant
curl http://localhost:6333/collections

# MongoDB
docker exec mongodb mongosh --eval "db.runCommand('ping')"
```

### Instalación para Desarrollo

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Iniciar servicios externos
docker-compose up mongodb redis qdrant

# Iniciar API
uvicorn api_v2:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### TorchServe
```bash
cd modelo
torch-model-archiver --model-name gsasrec \
  --version 1.0 \
  --handler ../backend/torchserve_handler.py \
  --extra-files gsasrec.py,transformer_decoder.py \
  --export-path ../model-store

torchserve --start --model-store ../model-store \
  --models gsasrec=gsasrec.mar \
  --ts-config config.properties
```

## 📡 API Endpoints

### Recomendaciones

#### Recomendación Individual
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "k": 10,
    "method": "torchserve",
    "filters": {
      "genres": ["Action", "Sci-Fi"],
      "year_min": 2000,
      "rating_min": 4.0
    }
  }'
```

#### Recomendaciones en Lote
```bash
curl -X POST "http://localhost:8000/recommend_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3, 4, 5],
    "k": 10,
    "method": "faiss"
  }'
```

#### Búsqueda de Películas
```bash
curl -X GET "http://localhost:8000/search_movies?query=matrix&limit=10"
```

### Usuarios

#### Estadísticas de Usuario
```bash
curl -X GET "http://localhost:8000/user_stats/1"
```

#### Actualizar Perfil
```bash
curl -X POST "http://localhost:8000/update_user" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "movie_id": 123,
    "rating": 4.5
  }'
```

### Monitoreo

#### Estado del Sistema
```bash
curl -X GET "http://localhost:8000/health"
```

#### Estadísticas Detalladas
```bash
curl -X GET "http://localhost:8000/stats"
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Base de datos
MONGO_URI=mongodb://admin:password@localhost:27017/movielens_32m?authSource=admin
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Servicios vectoriales
QDRANT_HOST=localhost
QDRANT_PORT=6333
FAISS_INDEX_TYPE=flat  # flat, ivf, hnsw

# TorchServe
TORCHSERVE_HOST=localhost
TORCHSERVE_PORT=8080
TORCHSERVE_MANAGEMENT_PORT=8081

# Modelo
MODEL_PATH=/app/modelo/pre_trained/gsasrec-ml32m.pt
EMBEDDING_DIM=256
MAX_SEQUENCE_LENGTH=200

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
LOG_LEVEL=INFO

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_SERIALIZER=json

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### Configuración del Modelo gSASRec

```python
CONFIG_ML32M = {
    'num_items': 84436,      # Número total de películas
    'num_users': 336000,     # Número estimado de usuarios
    'max_seq_len': 200,      # Longitud máxima de secuencia
    'embedding_dim': 256,    # Dimensión de embeddings
    'num_heads': 8,          # Cabezas de atención
    'num_blocks': 4,         # Bloques transformer
    'dropout_rate': 0.2,     # Tasa de dropout
    'pad_token': 0,          # Token de padding
    'device': 'cuda'         # Dispositivo (cuda/cpu)
}
```

## 📈 Monitoreo y Métricas

### Métricas del Sistema
- **Latencia de API**: P50, P95, P99
- **Throughput**: Recomendaciones/segundo
- **Uso de memoria**: FAISS, Redis, modelo
- **Uso de CPU/GPU**: Por servicio
- **Errores**: Rate y tipos

### Métricas del Modelo
- **nDCG@10**: Calidad de recomendaciones
- **Recall@10**: Cobertura
- **Diversity**: Diversidad de géneros
- **Coverage**: Catálogo cubierto
- **Freshness**: Películas recientes recomendadas

### Dashboards Disponibles
- **API Metrics**: `/stats` endpoint
- **Flower**: Monitoreo de Celery en `http://localhost:5555`
- **Qdrant Dashboard**: `http://localhost:6333/dashboard`

## 🧪 Testing

### Tests Unitarios
```bash
cd backend
pytest tests/ -v --cov=.
```

### Tests de Integración
```bash
python test_components.py  # Verifica todos los servicios
python test_api.py         # Prueba endpoints
python load_test_data.py   # Carga datos de prueba
```

### Tests de Carga
```bash
# Usando locust
pip install locust
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🚀 Despliegue en Producción

### Docker Swarm
```bash
docker swarm init
docker stack deploy -c docker-compose.prod.yml recommendation-system
```

### Kubernetes
```bash
kubectl apply -f k8s/
kubectl get pods -n recommendation-system
```

### Optimizaciones de Producción
- **FAISS**: Usar IndexHNSW para datasets grandes
- **Redis**: Cluster para alta disponibilidad
- **MongoDB**: Replica set
- **TorchServe**: Múltiples workers
- **Load Balancer**: Nginx/HAProxy

## 🤝 Contribución

### Estructura del Proyecto
```
SistemaDeRecomendacionTCD/
├── backend/                 # API FastAPI
│   ├── api_v2.py           # API principal
│   ├── services/           # Servicios de negocio
│   ├── database/           # Conexiones DB
│   └── tests/              # Tests
├── frontend/               # Aplicación Next.js
│   ├── app/                # App router
│   ├── components/         # Componentes reutilizables
│   └── lib/                # Utilidades
├── modelo/                 # Modelo gSASRec
│   ├── gsasrec.py          # Implementación del modelo
│   ├── datasets/           # Datos preprocesados
│   └── pre_trained/        # Modelos entrenados
├── scripts/                # Scripts de utilidad
└── docker-compose.yml      # Orquestación de servicios
```

### Roadmap
- [ ] **Evaluación A/B**: Sistema de experimentación
- [ ] **Recomendaciones en tiempo real**: Streaming con Kafka
- [ ] **Explicabilidad**: Explicaciones de recomendaciones
- [ ] **Diversidad**: Algoritmos anti-filter bubble
- [ ] **Cold start**: Mejor manejo de usuarios nuevos
- [ ] **Multi-objetivo**: Balancear popularidad vs personalización

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 📞 Contacto

- **Desarrollador**: Equipo TCD
- **Email**: [contact@tcd-recommendations.com](mailto:contact@tcd-recommendations.com)
- **GitHub**: [https://github.com/Pev40/ProyectoSistemaDeRecomendacion](https://github.com/Pev40/ProyectoSistemaDeRecomendacion)

---

⭐ Si este proyecto te ha sido útil, ¡no olvides darle una estrella en GitHub! 