# 🎬 Guía del Sistema de Registro de Usuarios

## Descripción General

El Sistema de Recomendación ML32M Vectorial ahora incluye un completo sistema de registro de usuarios que permite:

- ✅ **Registro de nuevos usuarios** con preferencias básicas
- ✅ **Selección de géneros preferidos** de una lista predefinida  
- ✅ **Configuración detallada de preferencias** mediante selección de películas
- ✅ **Generación automática de embeddings** personalizados
- ✅ **Recomendaciones vectoriales** basadas en el perfil del usuario
- ✅ **Clasificación de usuarios** por preferencias y comportamiento

## 🚀 Inicio Rápido

### 1. Ejecutar la API

```bash
cd backend
uvicorn api_ml32m_vectorial:app --reload --host 0.0.0.0 --port 8000
```

### 2. Probar el Sistema

```bash
python backend/example_user_registration.py
```

## 📋 Endpoints Disponibles

### 🎭 Obtener Géneros Disponibles
```http
GET /genres
```

**Respuesta:**
```json
{
  "genres": [
    "Action", "Adventure", "Animation", "Children's", 
    "Comedy", "Crime", "Documentary", "Drama", 
    "Fantasy", "Film-Noir", "Horror", "Musical", 
    "Mystery", "Romance", "Sci-Fi", "Thriller", 
    "War", "Western"
  ],
  "count": 18,
  "timestamp": "2024-01-20 15:30:45"
}
```

### 🔥 Películas en Tendencia por Género
```http
GET /trending_movies?limit_per_genre=10
```

**Respuesta:**
```json
{
  "trending_by_genre": {
    "Action": [
      {
        "movie_id": 1,
        "title": "Toy Story (1995)",
        "year": 1995,
        "genres": "Adventure|Animation|Children|Comedy|Fantasy"
      }
    ]
  },
  "total_genres": 18,
  "movies_per_genre": 10
}
```

### 👤 Registrar Nuevo Usuario
```http
POST /register_user
Content-Type: application/json

{
  "username": "juan_perez",
  "email": "juan@ejemplo.com",
  "preferred_genres": ["Action", "Comedy", "Sci-Fi"],
  "age_range": "young_adult",
  "country": "España"
}
```

**Respuesta:**
```json
{
  "message": "Usuario registrado exitosamente",
  "user_id": 200001,
  "username": "juan_perez",
  "preferred_genres": ["Action", "Comedy", "Sci-Fi"],
  "next_step": "Configurar preferencias detalladas en /set_preferences"
}
```

### ⚙️ Configurar Preferencias Detalladas
```http
POST /set_preferences
Content-Type: application/json

{
  "user_id": 200001,
  "movies_by_genre": {
    "Action": [1, 2, 3],
    "Comedy": [10, 15, 25],
    "Sci-Fi": [50, 75, 100]
  }
}
```

**Respuesta:**
```json
{
  "message": "Preferencias configuradas exitosamente",
  "user_id": 200001,
  "initial_ratings_created": 9,
  "embedding_created": true,
  "ready_for_recommendations": true
}
```

### 🎯 Obtener Recomendaciones
```http
POST /recommend
Content-Type: application/json

{
  "user_id": 200001,
  "k": 10,
  "method": "vectorial"
}
```

### 👤 Obtener Perfil de Usuario
```http
GET /user_profile/200001
```

## 🔄 Flujo de Registro Completo

### Paso 1: Obtener Información Inicial
```python
import requests

# Obtener géneros disponibles
genres_response = requests.get("http://localhost:8000/genres")
genres = genres_response.json()["genres"]

# Obtener películas en tendencia para mostrar al usuario
trending_response = requests.get("http://localhost:8000/trending_movies?limit_per_genre=5")
trending_movies = trending_response.json()["trending_by_genre"]
```

### Paso 2: Registrar Usuario
```python
user_data = {
    "username": "nuevo_usuario",
    "email": "usuario@ejemplo.com",
    "preferred_genres": ["Action", "Comedy"],  # Seleccionados por el usuario
    "age_range": "adult",                      # teen, young_adult, adult, senior
    "country": "España"
}

register_response = requests.post("http://localhost:8000/register_user", json=user_data)
user_id = register_response.json()["user_id"]
```

### Paso 3: Configurar Preferencias Detalladas
```python
# El usuario selecciona películas específicas que le gustan de cada género
preferences = {
    "user_id": user_id,
    "movies_by_genre": {
        "Action": [1, 5, 10],     # IDs de películas de acción que le gustan
        "Comedy": [20, 25, 30]    # IDs de películas de comedia que le gustan
    }
}

prefs_response = requests.post("http://localhost:8000/set_preferences", json=preferences)
```

### Paso 4: Obtener Recomendaciones
```python
recommendations_request = {
    "user_id": user_id,
    "k": 10,
    "method": "vectorial"
}

recommendations = requests.post("http://localhost:8000/recommend", json=recommendations_request)
```

## 🧠 Cómo Funciona la Clasificación

### 1. **Embedding Inicial**
- Se crea un embedding promedio ponderado basado en las películas seleccionadas
- Mayor peso para géneros preferidos
- Menor peso para otros géneros seleccionados

### 2. **Clasificación por Preferencias**
- **Géneros preferidos**: Determina el tipo de contenido que le gusta
- **Rango de edad**: Influye en la madurez del contenido
- **País**: Puede influir en preferencias culturales
- **Películas seleccionadas**: Define el gusto específico dentro de cada género

### 3. **Actualización Continua**
- El embedding del usuario se actualiza con cada nueva calificación
- Las recomendaciones mejoran con más interacciones
- Se pueden encontrar usuarios similares para recomendaciones colaborativas

## 🎯 Estrategias de Recomendación

### Vectorial (Por Defecto)
- Usa el embedding del usuario para encontrar películas similares
- Muy efectivo para usuarios con preferencias bien definidas
- Funciona incluso con pocos datos de entrada

### Colaborativa (Próximamente)
- Encuentra usuarios con gustos similares
- Recomienda películas que gustaron a usuarios similares
- Mejor para descubrir nuevos géneros

### Híbrida (Próximamente)
- Combina vectorial y colaborativa
- Máxima precisión en recomendaciones
- Equilibra exploración y explotación

## 📊 Validaciones y Restricciones

### Usuario
- **Username**: 3-50 caracteres
- **Email**: Formato válido y único
- **Géneros**: Mínimo 1, máximo 10, deben existir en la lista
- **Age Range**: teen, young_adult, adult, senior

### Preferencias
- **Películas por género**: Las películas deben existir en la base de datos
- **Géneros**: Deben coincidir con los preferidos del usuario

## 🔧 Configuración Técnica

### Base de Datos
- **MongoDB**: Almacena perfiles de usuarios y ratings
- **Redis**: Cache para consultas frecuentes
- **Qdrant**: Almacena embeddings vectoriales

### Embeddings
- **Dimensión**: 256 (configurable en CONFIG_ML32M)
- **Distancia**: Coseno
- **Colecciones**: `movie_embeddings`, `user_embeddings`

### IDs de Usuario
- **Usuarios existentes**: 1-199999
- **Usuarios nuevos**: 200000+

## 🐛 Solución de Problemas

### Error 500: Database manager no inicializado
```bash
# Verificar que MongoDB y Redis estén ejecutándose
docker-compose up -d mongodb redis
```

### Error 404: Usuario no encontrado
```python
# Verificar que el user_id existe
response = requests.get(f"http://localhost:8000/user_profile/{user_id}")
```

### Error 400: Géneros inválidos
```python
# Obtener géneros válidos primero
genres = requests.get("http://localhost:8000/genres").json()["genres"]
```

## 📈 Monitoreo y Estadísticas

### Estado del Sistema
```http
GET /health
```

### Estadísticas Generales
```http
GET /stats
```

### Estadísticas de Usuario
```http
GET /user_stats/{user_id}
```

## 🌟 Casos de Uso

### 1. **Nuevo Usuario Completo**
- Registra con preferencias básicas
- Selecciona películas de muestra
- Obtiene recomendaciones inmediatas

### 2. **Usuario Casual**
- Solo registra géneros preferidos
- Recibe recomendaciones basadas en popularidad por género

### 3. **Usuario Avanzado**
- Configura preferencias detalladas
- Actualiza preferencias con nuevas calificaciones
- Obtiene recomendaciones muy precisas

---

## 🚀 Próximas Funcionalidades

- [ ] **Recomendaciones colaborativas** basadas en usuarios similares
- [ ] **Filtros avanzados** por año, rating, etc.
- [ ] **Listas de favoritos** personalizadas
- [ ] **Notificaciones** de nuevas películas recomendadas
- [ ] **Análisis de sentimientos** en reseñas
- [ ] **Integración con redes sociales**

---

*Para más información técnica, consulta la documentación de la API en `http://localhost:8000/docs`* 