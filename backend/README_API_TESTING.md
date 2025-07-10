# 🎬 Guía de Pruebas API ML32M Vectorial

Esta guía te explica cómo probar la **API FastAPI** que acabamos de crear para el sistema de recomendación ML32M vectorial.

## 📋 Requisitos Previos

### ✅ Base Vectorizada Lista
Debes haber completado la conversión vectorial:
```bash
python convert_to_vector_db.py
```

### 🔌 Servicios Corriendo
Asegúrate de que estos servicios estén activos:
- **MongoDB** (puerto 27017)
- **Redis** (puerto 6379) 
- **Qdrant** (puerto 6333)

### 📦 Dependencias Python
```bash
pip install fastapi uvicorn motor redis qdrant-client requests
```

## 🚀 Paso 1: Iniciar la API

### Opción A: Script Automático (Recomendado)
```bash
cd backend
python start_api.py
```

Esto validará el entorno y iniciará la API automáticamente.

### Opción B: Manual
```bash
cd backend
uvicorn api_ml32m_vectorial:app --reload --host 0.0.0.0 --port 8000
```

### ✅ Verificar que Funciona
Deberías ver:
```
INFO:     Started server process
INFO:     Waiting for application startup
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🧪 Paso 2: Probar Endpoints

### Opción A: Script de Prueba Automático
```bash
python test_api_endpoints.py
```

Esto ejecutará **todas las pruebas** automáticamente.

### Opción B: Pruebas Específicas
```bash
# Solo health check
python test_api_endpoints.py --test health

# Solo recomendaciones para usuario 1
python test_api_endpoints.py --test recommendations --user-id 1

# Solo películas similares
python test_api_endpoints.py --test similar --movie-id 1
```

### Opción C: Navegador Web
Ve a: **http://localhost:8000/docs**

Esto abrirá la **documentación interactiva** de FastAPI donde puedes probar todos los endpoints.

## 📊 Paso 3: Endpoints Disponibles

### 🏠 Endpoint Raíz
```http
GET http://localhost:8000/
```
Información general del sistema.

### 💚 Health Check
```http
GET http://localhost:8000/health
```
Estado de todos los componentes (MongoDB, Redis, Qdrant, Modelo).

### 🎯 Recomendaciones Personalizadas
```http
POST http://localhost:8000/recommend
Content-Type: application/json

{
  "user_id": 1,
  "k": 10,
  "method": "vectorial"
}
```

### 🎭 Películas Similares
```http
POST http://localhost:8000/similar_movies
Content-Type: application/json

{
  "movie_id": 1,
  "k": 5
}
```

### 🔍 Buscar Películas
```http
POST http://localhost:8000/search_movies
Content-Type: application/json

{
  "query": "matrix",
  "limit": 10
}
```

### 🔥 Películas Populares
```http
GET http://localhost:8000/popular_movies?limit=20
```

### 📊 Estadísticas de Usuario
```http
GET http://localhost:8000/user_stats/1
```

### 📝 Actualizar Preferencias
```http
POST http://localhost:8000/update_user
Content-Type: application/json

{
  "user_id": 999,
  "movie_id": 1,
  "rating": 4.5
}
```

### 📈 Estadísticas del Sistema
```http
GET http://localhost:8000/stats
```

## 🧪 Ejemplos de Respuesta

### Recomendaciones
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "movie_id": 1234,
      "title": "The Matrix",
      "score": 0.892,
      "genres": ["Action", "Sci-Fi"],
      "year": 1999
    }
  ],
  "count": 10,
  "processing_time": 0.245,
  "user_history_size": 156
}
```

### Health Check
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "ok", "mongodb": "connected", "redis": "connected"},
    "qdrant": {"status": "ok", "vectors_count": 1000},
    "model": {"status": "ok", "embedding_dim": 256}
  }
}
```

## 🔧 Solución de Problemas

### ❌ Error "Database manager no inicializado"
**Problema:** MongoDB/Redis no están corriendo
**Solución:**
```bash
# Iniciar MongoDB
sudo systemctl start mongod

# Iniciar Redis
sudo systemctl start redis

# O con Docker
docker-compose up -d
```

### ❌ Error "Qdrant service no inicializado"
**Problema:** Qdrant no está corriendo
**Solución:**
```bash
# Con Docker
docker run -p 6333:6333 qdrant/qdrant
```

### ❌ Error "Usuario no encontrado"
**Problema:** El usuario no tiene historial en la base de datos
**Solución:**
- Usar un usuario que exista (ej: 1, 2, 3...)
- O crear ratings con `/update_user`

### ❌ Error "Modelo no cargado"
**Problema:** El archivo del modelo no se encuentra
**Solución:**
- Verificar que `fix_ml32m_model.py` existe
- Verificar que el modelo está en `../modelo/pre_trained/`

## 📈 Métricas de Rendimiento

### ⏱️ Tiempos Esperados:
- **Health Check:** ~0.1s
- **Búsqueda:** ~0.2s
- **Recomendaciones:** ~0.3-0.5s
- **Similares:** ~0.2-0.4s

### 📊 Escalabilidad:
- **Concurrencia:** FastAPI soporta requests concurrentes
- **Cache:** Redis cachea resultados frecuentes
- **Vectorial:** Qdrant optimiza búsquedas de similitud

## 🔬 Pruebas Avanzadas

### A. Prueba de Carga
```bash
# Instalar herramienta
pip install locust

# Crear archivo de prueba locust_test.py
# Ejecutar
locust -f locust_test.py --host=http://localhost:8000
```

### B. Prueba de Diversos Usuarios
```bash
# Probar múltiples usuarios
for i in {1..10}; do
  python test_api_endpoints.py --test recommendations --user-id $i
done
```

### C. Análisis de Respuesta
```bash
# Con curl y jq para análisis
curl -s http://localhost:8000/health | jq '.components'
```

## 🎯 Casos de Uso Principales

### 1. **E-commerce de Películas**
```bash
# Obtener recomendaciones para usuario
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "k": 5}'
```

### 2. **Sistema de "Películas Relacionadas"**
```bash
# Obtener similares a una película específica
curl -X POST "http://localhost:8000/similar_movies" \
  -H "Content-Type: application/json" \
  -d '{"movie_id": 1, "k": 5}'
```

### 3. **Analytics Dashboard**
```bash
# Obtener estadísticas del sistema
curl http://localhost:8000/stats
```

## 🚀 Siguientes Pasos

### Para Producción:
1. **Nginx:** Proxy reverso
2. **Docker:** Containerización
3. **Monitoring:** Prometheus + Grafana
4. **Auth:** JWT/OAuth2
5. **Rate Limiting:** Throttling de requests

### Para Frontend:
```javascript
// Ejemplo en JavaScript
const recommendations = await fetch('http://localhost:8000/recommend', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: 1, k: 10})
});
```

¡Ya tienes tu API vectorial funcionando! 🎉

---

**Archivo creado:** `README_API_TESTING.md`
**Última actualización:** $(date) 