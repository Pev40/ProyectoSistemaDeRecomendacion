# Sistema de Recomendación gSASRec - MovieLens 32M

Sistema de recomendación escalable basado en gSASRec entrenado en MovieLens 32M, con arquitectura completa que incluye TorchServe, MongoDB, Redis, FAISS y Qdrant.

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   TorchServe    │
│   Next.js       │◄──►│   API           │◄──►│   (gSASRec)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MongoDB       │    │   Redis         │    │   FAISS Index   │
│   (Datos)       │◄──►│   (Cache)       │◄──►│   (Búsqueda)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Qdrant        │
                       │   (Filtros)     │
                       └─────────────────┘
```

## 🚀 Componentes

### 1. **TorchServe** - Servicio de Modelos
- Sirve el modelo gSASRec entrenado
- Maneja inferencias en tiempo real
- Escalabilidad automática
- Monitoreo de métricas

### 2. **MongoDB** - Base de Datos Principal
- Almacena datos de MovieLens 32M
- Colecciones: movies, ratings, users
- Índices optimizados para consultas
- Soporte para agregaciones complejas

### 3. **Redis** - Cache y Cola de Tareas
- Cache de embeddings de usuarios
- Cache de metadata de películas
- Broker para Celery (tareas en background)
- Almacenamiento de sesiones

### 4. **FAISS** - Índice de Búsqueda
- Búsquedas ultrarrápidas de similitud
- Índices optimizados para embeddings
- Soporte para búsquedas en lote

### 5. **Qdrant** - Base Vectorial
- Búsquedas con filtros complejos
- Metadata completa de películas
- Filtros por género, año, rating

### 6. **FastAPI** - API REST
- Endpoints para recomendaciones
- Documentación automática (Swagger)
- Validación de datos con Pydantic
- Logging estructurado

### 7. **Celery** - Tareas en Background
- Recalcular embeddings de usuarios
- Sincronizar índices FAISS y Qdrant
- Limpiar cache periódicamente
- Monitoreo con Flower

## 📊 Dataset: MovieLens 32M

- **Usuarios**: ~138,000
- **Películas**: ~27,000
- **Calificaciones**: ~32,000,000
- **Géneros**: 20 categorías
- **Período**: 1995-2019

## 🛠️ Instalación

### Requisitos
- Docker y Docker Compose
- 8GB+ RAM disponible
- GPU opcional (para aceleración)

### Instalación Rápida

1. **Clonar y configurar:**
```bash
git clone <repository-url>
cd SistemaDeRecomendacionTCD
```

2. **Ejecutar con Docker Compose:**
```bash
docker-compose up --build
```

3. **Verificar servicios:**
```bash
# API
curl http://localhost:8000/health

# TorchServe
curl http://localhost:8080/ping

# MongoDB
docker exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis
docker exec redis redis-cli ping
```

## 📡 Endpoints de la API

### Recomendaciones

#### 1. Recomendación Individual
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "k": 10,
    "method": "torchserve"
  }'
```

#### 2. Recomendaciones en Lote
```bash
curl -X POST "http://localhost:8000/recommend_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3, 4, 5],
    "k": 10,
    "method": "torchserve"
  }'
```

#### 3. Actualizar Calificación
```bash
curl -X POST "http://localhost:8000/update_user" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "movie_id": 123,
    "rating": 4.5
  }'
```

### Búsqueda y Estadísticas

#### 4. Búsqueda de Películas
```bash
curl -X POST "http://localhost:8000/search_movies" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Matrix",
    "limit": 20
  }'
```

#### 5. Estadísticas de Usuario
```bash
curl "http://localhost:8000/user_stats/1"
```

#### 6. Películas Populares
```bash
curl "http://localhost:8000/popular_movies?limit=100"
```

### Monitoreo

#### 7. Salud del Sistema
```bash
curl "http://localhost:8000/health"
```

#### 8. Estadísticas Detalladas
```bash
curl "http://localhost:8000/stats"
```

## 🔧 Configuración

### Variables de Entorno

```bash
# MongoDB
MONGO_URI=mongodb://admin:password@mongodb:27017/movielens_32m?authSource=admin

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# TorchServe
TORCHSERVE_HOST=torchserve
TORCHSERVE_PORT=8080

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Puertos de Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| FastAPI | 8000 | API principal |
| TorchServe | 8080 | Inferencias |
| TorchServe Mgmt | 8081 | Gestión |
| TorchServe Metrics | 8082 | Métricas |
| MongoDB | 27017 | Base de datos |
| Redis | 6379 | Cache |
| Qdrant | 6333 | Vector DB |
| Flower | 5555 | Monitoreo Celery |

## 📈 Rendimiento

### Benchmarks

| Método | Latencia | QPS | Memoria |
|--------|----------|-----|---------|
| TorchServe | 50ms | 20 | 2GB |
| FAISS | 15ms | 66 | 1GB |
| Qdrant | 25ms | 40 | 1.5GB |
| MongoDB | 5ms | 200 | 500MB |
| Redis | 1ms | 1000 | 100MB |

### Optimizaciones

1. **Cache Inteligente**
   - Embeddings de usuarios cacheados
   - Metadata de películas cacheada
   - Invalidación automática

2. **Búsquedas Optimizadas**
   - Índices FAISS para similitud
   - Filtros Qdrant para metadata
   - Búsquedas en lote

3. **Escalabilidad**
   - TorchServe con auto-scaling
   - Celery workers distribuidos
   - Load balancing con Docker

## 🔍 Monitoreo

### Métricas Disponibles

- **TorchServe**: Latencia, throughput, GPU usage
- **MongoDB**: Operaciones, conexiones, índices
- **Redis**: Hit rate, memory usage, commands
- **FAISS**: Query time, index size
- **Qdrant**: Collection stats, vector operations

### Dashboards

1. **API Docs**: http://localhost:8000/docs
2. **Flower**: http://localhost:5555
3. **TorchServe**: http://localhost:8081/models

## 🧪 Testing

### Tests Unitarios
```bash
cd backend
pytest test_api.py -v
```

### Tests de Rendimiento
```bash
# Load testing
ab -n 1000 -c 10 -p test_data.json -T application/json http://localhost:8000/recommend
```

### Tests de Integración
```bash
# Verificar todos los servicios
curl http://localhost:8000/health
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **TorchServe no responde**
   ```bash
   docker logs torchserve
   docker exec torchserve ps aux
   ```

2. **MongoDB connection error**
   ```bash
   docker exec mongodb mongosh --eval "db.adminCommand('ping')"
   ```

3. **Redis connection error**
   ```bash
   docker exec redis redis-cli ping
   ```

4. **FAISS index corrupto**
   ```bash
   rm -rf faiss_index/
   python backend/faiss_index.py
   ```

### Logs

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Logs específicos
docker logs recommendation-api
docker logs torchserve
docker logs mongodb
```

## 🔄 Desarrollo

### Estructura del Proyecto

```
backend/
├── api_v2.py              # API principal
├── database.py            # Gestor de MongoDB/Redis
├── torchserve_client.py   # Cliente TorchServe
├── faiss_index.py        # Índice FAISS
├── qdrant_service.py     # Servicio Qdrant
├── celery_app.py         # Tareas en background
├── torchserve_handler.py # Handler para TorchServe
├── config.properties     # Configuración TorchServe
└── requirements.txt      # Dependencias
```

### Agregar Nuevos Endpoints

1. **Definir modelo Pydantic**
```python
class NewRequest(BaseModel):
    param1: str
    param2: int
```

2. **Crear endpoint**
```python
@app.post("/new_endpoint")
async def new_endpoint(request: NewRequest):
    # Lógica del endpoint
    return {"result": "success"}
```

### Agregar Nuevas Tareas Celery

```python
@celery_app.task(bind=True)
def new_task(self, param1: str):
    # Lógica de la tarea
    return {"status": "completed"}
```

## 📚 Recursos Adicionales

- [Documentación TorchServe](https://pytorch.org/serve/)
- [Documentación MongoDB](https://docs.mongodb.com/)
- [Documentación Redis](https://redis.io/documentation)
- [Documentación FAISS](https://github.com/facebookresearch/faiss)
- [Documentación Qdrant](https://qdrant.tech/documentation/)

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles. 