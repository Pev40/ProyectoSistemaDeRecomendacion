# 🧪 Guía de Pruebas Paso a Paso

Esta guía te ayudará a probar cada componente del sistema de recomendación individualmente antes de contenerizarlo todo.

## 📋 Prerrequisitos

### Servicios Requeridos
- **MongoDB**: Ejecutándose en `localhost:27017`
- **Redis**: Ejecutándose en `localhost:6379`
- **Qdrant**: Ejecutándose en `localhost:6333`

### Dependencias Python
```bash
pip install -r requirements.txt
```

## 🚀 Inicio Rápido

### Opción 1: Inicio Automático
```bash
cd backend
python start_step_by_step.py
```

Este script:
1. ✅ Verifica dependencias
2. ✅ Verifica servicios
3. ✅ Carga datos de prueba
4. ✅ Prueba componentes
5. ✅ Inicia la API
6. ✅ Prueba endpoints
7. ✅ Muestra instrucciones

### Opción 2: Pruebas Manuales

#### Paso 1: Verificar Componentes
```bash
python test_components.py
```

Este script prueba:
- 🔍 MongoDB
- 🔍 Redis  
- 🔍 Qdrant
- 🔍 Modelo gSASRec
- 🔍 FAISS
- 🔍 Base de datos
- 🔍 Cliente TorchServe

#### Paso 2: Cargar Datos de Prueba
```bash
python load_test_data.py
```

Crea:
- 📽️ 20 películas de prueba
- 👥 100 usuarios de prueba
- ⭐ Ratings aleatorios
- 🧠 Embeddings de prueba

#### Paso 3: Iniciar API
```bash
uvicorn api_v2:app --host 0.0.0.0 --port 8000 --reload
```

#### Paso 4: Probar API
```bash
python test_api.py
```

## 📊 Endpoints Disponibles

### Información del Sistema
- `GET /health` - Estado del sistema
- `GET /stats` - Estadísticas detalladas

### Películas
- `GET /movies` - Listar películas
- `GET /movies/{movie_id}` - Obtener película específica
- `GET /movies/{movie_id}/similar` - Películas similares
- `GET /movies/search?q={query}` - Búsqueda de películas

### Usuarios
- `GET /users` - Listar usuarios
- `GET /users/{user_id}` - Obtener usuario específico
- `GET /users/{user_id}/ratings` - Ratings del usuario

### Recomendaciones
- `GET /recommendations/user/{user_id}` - Recomendaciones para usuario
- `POST /recommendations/batch` - Recomendaciones en lote

## 🔧 Comandos Útiles

### Verificar Servicios
```bash
# MongoDB
mongosh --eval "db.adminCommand('ping')"

# Redis
redis-cli ping

# Qdrant
curl http://localhost:6333/collections
```

### Ver Logs
```bash
# API logs
tail -f logs/api.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log

# Redis logs
docker logs redis-container
```

### Limpiar Datos
```bash
# Limpiar MongoDB
mongosh movielens_32m --eval "db.dropDatabase()"

# Limpiar Redis
redis-cli FLUSHALL

# Limpiar Qdrant
curl -X DELETE http://localhost:6333/collections/movies
```

## 🐛 Troubleshooting

### MongoDB no conecta
```bash
# Verificar que esté ejecutándose
sudo systemctl status mongod

# Iniciar si no está ejecutándose
sudo systemctl start mongod
```

### Redis no conecta
```bash
# Verificar contenedor
docker ps | grep redis

# Reiniciar contenedor
docker restart redis-container
```

### Qdrant no conecta
```bash
# Verificar contenedor
docker ps | grep qdrant

# Reiniciar contenedor
docker restart qdrant-container
```

### API no inicia
```bash
# Verificar puerto
netstat -tulpn | grep 8000

# Matar proceso si está ocupado
pkill -f uvicorn

# Verificar logs
tail -f logs/api.log
```

### Modelo no carga
```bash
# Verificar archivo del modelo
ls -la ../modelo/pre_trained/

# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

## 📈 Monitoreo

### Métricas del Sistema
```bash
# CPU y memoria
htop

# Disco
df -h

# Red
iftop
```

### Métricas de la API
```bash
# Requests por segundo
curl -s http://localhost:8000/stats | jq '.requests_per_second'

# Latencia promedio
curl -s http://localhost:8000/stats | jq '.average_latency_ms'
```

### Métricas de Base de Datos
```bash
# MongoDB
mongosh --eval "db.stats()"

# Redis
redis-cli info memory

# Qdrant
curl http://localhost:6333/collections/movies
```

## 🧪 Tests Avanzados

### Test de Carga
```bash
# Instalar Apache Bench
sudo apt install apache2-utils

# Test de carga básico
ab -n 1000 -c 10 http://localhost:8000/health

# Test de recomendaciones
ab -n 100 -c 5 -p test_data.json -T application/json http://localhost:8000/recommendations/user/1
```

### Test de Latencia
```bash
# Medir latencia de recomendaciones
time curl -s http://localhost:8000/recommendations/user/1 > /dev/null
```

### Test de Memoria
```bash
# Monitorear uso de memoria
watch -n 1 'ps aux | grep uvicorn'
```

## 📝 Logs y Debugging

### Niveles de Log
```python
# En api_v2.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Logs Estructurados
```python
# Los logs ya están configurados con structlog
# Se guardan en logs/api.log
```

### Debug de Queries
```python
# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.movielens_32m
db.movies.find({"title": {"$regex": "Matrix"}}).explain()
```

## 🔄 Próximos Pasos

Una vez que todo funcione correctamente:

1. **Contenerización**: Usar Docker Compose
2. **Producción**: Configurar nginx, gunicorn
3. **Monitoreo**: Prometheus, Grafana
4. **CI/CD**: GitHub Actions
5. **Testing**: Pytest, coverage

## 📞 Soporte

Si encuentras problemas:

1. ✅ Revisa los logs
2. ✅ Verifica servicios
3. ✅ Ejecuta `test_components.py`
4. ✅ Consulta este README
5. 📧 Crea un issue en el repositorio

---

**¡Happy Testing! 🎉** 