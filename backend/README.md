# Backend de Recomendación gSASRec + FAISS + Qdrant

Sistema de recomendación escalable basado en el modelo gSASRec entrenado en MovieLens-1M, con índices FAISS para búsquedas ultrarrápidas y Qdrant para búsquedas filtrables.

## Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │   FAISS Index   │    │  Qdrant Vector  │
│   (Puerto 8000) │◄──►│   (In-Memory)   │    │   Database      │
└─────────────────┘    └─────────────────┘    │  (Puerto 6333)  │
                                              └─────────────────┘
         │
         ▼
┌─────────────────┐
│ gSASRec Model   │
│ (Embeddings)    │
└─────────────────┘
```

## Componentes

### 1. Exportador de Embeddings (`embedding_exporter.py`)
- Carga el modelo gSASRec entrenado
- Extrae embeddings de items y usuarios
- Mapea índices internos a IDs reales

### 2. Índice FAISS (`faiss_index.py`)
- Motor de búsqueda en memoria
- Soporte para diferentes tipos de índice (Flat, IVF, HNSW)
- Búsquedas ultrarrápidas para similitud coseno

### 3. Servicio Qdrant (`qdrant_service.py`)
- Base de datos vectorial persistente
- Soporte para filtros complejos (género, año, rating)
- Metadata completa de películas

### 4. API FastAPI (`api.py`)
- Endpoints REST para recomendaciones
- Monitoreo de salud del sistema
- Cache de embeddings de usuarios

### 5. Servicio de Sincronización (`sync_service.py`)
- Sincronización automática entre FAISS y Qdrant
- Monitoreo de métricas del sistema
- Programación de tareas

## Instalación

### Requisitos
- Python 3.10+
- Docker y Docker Compose
- 4GB+ RAM disponible

### Instalación Local

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd SistemaDeRecomendacionTCD
```

2. **Instalar dependencias**
```bash
cd backend
pip install -r requirements.txt
```

3. **Iniciar Qdrant**
```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

4. **Ejecutar el backend**
```bash
python api.py
```

### Instalación con Docker Compose

1. **Construir y ejecutar todos los servicios**
```bash
docker-compose up --build
```

## Uso

### Endpoints de la API

#### 1. Recomendación Rápida (FAISS)
```bash
curl -X POST "http://localhost:8000/recommend_fast" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "k": 10
  }'
```

#### 2. Recomendación con Filtros (Qdrant)
```bash
curl -X POST "http://localhost:8000/recommend_filter" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "k": 10,
    "filters": {
      "genres": ["Action", "Adventure"],
      "year_min": 2000,
      "year_max": 2020,
      "rating_min": 4.0
    }
  }'
```

#### 3. Recomendaciones en Lote
```bash
curl -X POST "http://localhost:8000/recommend_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3, 4, 5],
    "k": 10
  }'
```

#### 4. Actualizar Usuario
```bash
curl -X POST "http://localhost:8000/update_user" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "movie_id": 123,
    "rating": 4.5
  }'
```

#### 5. Verificar Salud del Sistema
```bash
curl "http://localhost:8000/health"
```

#### 6. Estadísticas del Sistema
```bash
curl "http://localhost:8000/stats"
```

### Ejemplos de Respuesta

#### Recomendación Exitosa
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "movie_id": 123,
      "title": "The Matrix (1999)",
      "genres": ["Action", "Sci-Fi"],
      "year": 1999,
      "score": 0.95
    }
  ],
  "latency_ms": 15.2,
  "method": "faiss_fast"
}
```

## Configuración

### Variables de Entorno

```bash
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Modelo
MODEL_PATH=../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt

# Sincronización
SYNC_INTERVAL_HOURS=6
```

### Configuración de FAISS

El sistema soporta diferentes tipos de índice FAISS:

- **Flat**: Búsqueda exacta, más lenta pero precisa
- **IVF**: Búsqueda aproximada, más rápida
- **HNSW**: Búsqueda aproximada, muy rápida

```python
# En faiss_index.py
faiss_index = FAISSIndex(embedding_dim=128, index_type="flat")
```

## Monitoreo

### Métricas del Sistema

- **CPU**: Uso de procesador
- **RAM**: Uso de memoria
- **Disco**: Espacio en disco
- **Latencia**: Tiempo de respuesta de la API
- **QPS**: Consultas por segundo

### Logs

Los logs se guardan en:
- `sync_service.log`: Servicio de sincronización
- `api.log`: API de recomendación

## Rendimiento

### Benchmarks

| Método | Latencia Promedio | QPS |
|--------|-------------------|-----|
| FAISS Flat | 15ms | 66 |
| FAISS IVF | 8ms | 125 |
| Qdrant | 25ms | 40 |

### Optimizaciones

1. **Cache de Embeddings**: Los embeddings de usuarios se cachean en memoria
2. **Búsquedas en Lote**: Soporte para múltiples consultas simultáneas
3. **Índices Optimizados**: Configuración específica para cada tipo de búsqueda

## Desarrollo

### Estructura del Proyecto

```
backend/
├── api.py                 # API FastAPI principal
├── embedding_exporter.py  # Exportador de embeddings
├── faiss_index.py        # Índice FAISS
├── qdrant_service.py     # Servicio Qdrant
├── sync_service.py       # Servicio de sincronización
├── requirements.txt      # Dependencias
└── README.md            # Documentación
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

### Testing

```bash
# Instalar dependencias de testing
pip install pytest httpx

# Ejecutar tests
pytest tests/
```

## Troubleshooting

### Problemas Comunes

1. **Error de conexión a Qdrant**
   - Verificar que Qdrant esté ejecutándose
   - Verificar puerto 6333

2. **Error de memoria**
   - Reducir tamaño del índice FAISS
   - Usar índice IVF en lugar de Flat

3. **Latencia alta**
   - Verificar configuración de FAISS
   - Optimizar queries de Qdrant

### Logs de Error

```bash
# Ver logs del servicio
docker logs recommendation-api

# Ver logs de Qdrant
docker logs qdrant
```

## Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles. 