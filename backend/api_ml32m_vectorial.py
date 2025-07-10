# API FastAPI para Sistema de Recomendación ML32M Vectorial
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import os
import sys
import torch
import numpy as np
import logging
import time
import json
from contextlib import asynccontextmanager

# Agregar paths
modelo_path = os.path.join(os.path.dirname(__file__), '..', 'modelo')
sys.path.append(modelo_path)

# Importaciones de servicios locales
from database import DatabaseManager, MovieLensDatabase
from qdrant_service import QdrantService
from fix_ml32m_model import load_ml32m_model_fixed

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración ML32M
CONFIG_ML32M = {
    'embedding_dim': 256,
    'max_seq_len': 200,
    'batch_size': 32,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
}

# Variables globales
db_manager = None
movie_db = None
qdrant_service = None
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    global db_manager, movie_db, qdrant_service, model
    
    try:
        logger.info("🚀 Iniciando Sistema de Recomendación ML32M Vectorial...")
        
        # 1. Conectar a bases de datos
        logger.info("📊 Conectando a bases de datos...")
        db_manager = DatabaseManager()
        await db_manager.connect()
        movie_db = MovieLensDatabase(db_manager)
        
        # 2. Conectar a Qdrant
        logger.info("🔍 Conectando a Qdrant...")
        qdrant_service = QdrantService(
            host="localhost", 
            port=6333, 
            collection_name="movie_embeddings"
        )
        
        # Verificar estado de Qdrant
        try:
            stats = qdrant_service.get_collection_stats()
            logger.info(f"Qdrant: {stats.get('points_count', 0)} embeddings disponibles")
        except Exception as e:
            logger.warning(f"No se pudo verificar Qdrant: {e}")
        
        # 3. Cargar modelo ML32M
        logger.info("🧠 Cargando modelo ML32M...")
        model = load_ml32m_model_fixed()
        if model:
            model.eval()
            logger.info("✅ Modelo cargado correctamente")
        else:
            logger.warning("⚠️ Modelo no cargado, algunas funciones limitadas")
        
        logger.info("✅ Sistema iniciado exitosamente")
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante inicialización: {e}")
        raise
    finally:
        if db_manager:
            await db_manager.disconnect()

# Crear aplicación FastAPI
app = FastAPI(
    title="🎬 Sistema de Recomendación ML32M Vectorial",
    description="API para recomendaciones basadas en embeddings vectoriales con MovieLens 32M",
    version="3.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class RecommendationRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    k: int = Field(10, ge=1, le=50, description="Número de recomendaciones")
    method: str = Field("vectorial", description="Método: vectorial, collaborative, hybrid")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionales")

class SimilarMoviesRequest(BaseModel):
    movie_id: int = Field(..., description="ID de la película")
    k: int = Field(10, ge=1, le=50, description="Número de películas similares")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionales")

class UserUpdateRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    movie_id: int = Field(..., description="ID de la película")
    rating: float = Field(..., ge=0.5, le=5.0, description="Calificación (0.5-5.0)")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Término de búsqueda")
    limit: int = Field(20, ge=1, le=100, description="Número de resultados")

class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")
    email: str = Field(..., description="Email del usuario")
    preferred_genres: List[str] = Field(..., min_items=1, max_items=10, description="Géneros preferidos")
    age_range: str = Field(..., description="Rango de edad: teen, young_adult, adult, senior")
    country: Optional[str] = Field(None, description="País del usuario")

class UserPreferencesUpdate(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    preferred_genres: Optional[List[str]] = Field(None, description="Nuevos géneros preferidos")
    age_range: Optional[str] = Field(None, description="Nuevo rango de edad")
    country: Optional[str] = Field(None, description="Nuevo país")

class GenrePreferenceRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    movies_by_genre: Dict[str, List[int]] = Field(..., description="Películas seleccionadas por género")
    
class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    model: Dict[str, Any]
    qdrant: Dict[str, Any]
    system: Dict[str, Any]

# Dependencies
async def get_db_manager():
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database manager no inicializado")
    return db_manager

async def get_movie_db():
    if movie_db is None:
        raise HTTPException(status_code=500, detail="Movie database no inicializada")
    return movie_db

async def get_qdrant_service():
    if qdrant_service is None:
        raise HTTPException(status_code=500, detail="Qdrant service no inicializado")
    return qdrant_service

# Funciones auxiliares
def get_user_embedding(user_sequence: List[int]) -> np.ndarray:
    """Genera embedding de usuario basado en su secuencia"""
    try:
        if not model or not user_sequence:
            return None
        
        # Preparar secuencia
        seq_len = min(len(user_sequence), CONFIG_ML32M['max_seq_len'])
        padded_sequence = [0] * (CONFIG_ML32M['max_seq_len'] - seq_len) + user_sequence[-seq_len:]
        
        # Generar embedding
        with torch.no_grad():
            sequence_tensor = torch.tensor([padded_sequence], dtype=torch.long)
            seq_emb, _ = model(sequence_tensor)
            user_embedding = seq_emb[:, -1, :].squeeze().numpy()
        
        return user_embedding
        
    except Exception as e:
        logger.error(f"Error generando embedding de usuario: {e}")
        return None

# Géneros disponibles en MovieLens
AVAILABLE_GENRES = [
    "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
]

def get_movies_by_genre(genre: str, limit: int = 50) -> List[int]:
    """Obtiene películas populares de un género específico"""
    try:
        if not movie_db:
            return []
        
        # Buscar películas del género en la base sincrónica
        movies = movie_db.sync_db.movies.find(
            {"genres": {"$regex": genre, "$options": "i"}},
            {"movieId": 1, "_id": 0}
        ).limit(limit)
        
        return [movie["movieId"] for movie in movies]
    except Exception as e:
        logger.error(f"Error obteniendo películas del género {genre}: {e}")
        return []

def create_initial_user_embedding(preferred_genres: List[str], sample_movies: Dict[str, List[int]]) -> Optional[np.ndarray]:
    """Crea embedding inicial para usuario basado en preferencias"""
    try:
        if not model or not qdrant_service:
            return None
        
        # Obtener embeddings de películas seleccionadas
        all_embeddings = []
        weights = []
        
        for genre, movies in sample_movies.items():
            if genre in preferred_genres:
                # Mayor peso para géneros preferidos
                weight = 1.0
            else:
                # Menor peso para otros géneros
                weight = 0.3
            
            for movie_id in movies:
                try:
                    movie_data = qdrant_service.get_movie_by_id(movie_id)
                    if movie_data and movie_data.get("vector"):
                        vector = movie_data["vector"]
                        if isinstance(vector, list):
                            embedding = np.array(vector)
                        else:
                            embedding = np.array(vector.tolist()) if hasattr(vector, 'tolist') else np.array(vector)
                        
                        all_embeddings.append(embedding)
                        weights.append(weight)
                except Exception as e:
                    logger.warning(f"Error obteniendo embedding de película {movie_id}: {e}")
                    continue
        
        if not all_embeddings:
            return None
        
        # Crear embedding promedio ponderado
        embeddings_array = np.array(all_embeddings)
        weights_array = np.array(weights).reshape(-1, 1)
        
        weighted_average = np.average(embeddings_array, axis=0, weights=weights_array.flatten())
        
        return weighted_average
        
    except Exception as e:
        logger.error(f"Error creando embedding inicial: {e}")
        return None

async def save_user_profile(user_data: Dict[str, Any]) -> int:
    """Guarda perfil de usuario en base de datos y retorna nuevo user_id"""
    try:
        if not db_manager:
            raise Exception("Database manager no disponible")
        
        # Obtener siguiente user_id
        last_user = await db_manager.mongo_client.movie_recommendations.users.find_one(
            {},
            sort=[("userId", -1)]
        )
        
        new_user_id = (last_user.get("userId", 0) + 1) if last_user else 200000  # Empezar desde 200000 para nuevos usuarios
        
        # Crear documento de usuario
        user_doc = {
            "userId": new_user_id,
            "username": user_data["username"],
            "email": user_data["email"],
            "preferred_genres": user_data["preferred_genres"],
            "age_range": user_data["age_range"],
            "country": user_data.get("country"),
            "registration_date": time.strftime('%Y-%m-%d %H:%M:%S'),
            "is_active": True,
            "initial_preferences_set": False
        }
        
        # Guardar en MongoDB
        await db_manager.mongo_client.movie_recommendations.users.insert_one(user_doc)
        
        logger.info(f"Usuario {new_user_id} registrado exitosamente")
        return new_user_id
        
    except Exception as e:
        logger.error(f"Error guardando perfil de usuario: {e}")
        raise

# Endpoints principales
@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "message": "🎬 Sistema de Recomendación ML32M Vectorial",
        "version": "3.0.0",
        "status": "active",
        "endpoints": {
            "recomendaciones": "/recommend",
            "similares": "/similar_movies",
            "buscar": "/search_movies",
            "popular": "/popular_movies",
            "estadisticas": "/user_stats/{user_id}",
            "registro": "/register_user",
            "generos": "/genres",
            "tendencias": "/trending_movies",
            "preferencias": "/set_preferences",
            "salud": "/health"
        }
    }

@app.post("/recommend", summary="🎯 Obtener recomendaciones para usuario")
async def recommend(
    request: RecommendationRequest,
    movie_db_instance = Depends(get_movie_db),
    qdrant_instance = Depends(get_qdrant_service)
):
    """Genera recomendaciones personalizadas para un usuario"""
    try:
        start_time = time.time()
        
        # 1. Obtener secuencia del usuario
        user_sequence = await movie_db_instance.get_user_sequence(request.user_id)
        
        if not user_sequence:
            raise HTTPException(
                status_code=404, 
                detail=f"Usuario {request.user_id} no encontrado o sin historial"
            )
        
        # 2. Generar embedding del usuario
        user_embedding = get_user_embedding(user_sequence)
        
        if user_embedding is None:
            raise HTTPException(
                status_code=500,
                detail="Error generando embedding del usuario"
            )
        
        # 3. Buscar películas similares en Qdrant
        similar_movies = qdrant_instance.search_similar(
            query_embedding=user_embedding,
            k=request.k * 2,  # Obtener más para filtrar
            filters=request.filters
        )
        
        # 4. Filtrar películas ya vistas
        seen_movies = set(user_sequence)
        recommendations = [
            movie for movie in similar_movies 
            if movie["movie_id"] not in seen_movies
        ][:request.k]
        
        # 5. Enriquecer con metadata
        for rec in recommendations:
            metadata = await movie_db_instance.get_movie_metadata(rec["movie_id"])
            if metadata:
                rec.update({
                    "title": metadata.get("title", "Título desconocido"),
                    "year": metadata.get("year"),
                    "full_genres": metadata.get("genres", "")
                })
        
        elapsed_time = time.time() - start_time
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations,
            "method": request.method,
            "count": len(recommendations),
            "user_history_size": len(user_sequence),
            "processing_time": round(elapsed_time, 3),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/similar_movies", summary="🎭 Encontrar películas similares")
async def similar_movies(
    request: SimilarMoviesRequest,
    movie_db_instance = Depends(get_movie_db),
    qdrant_instance = Depends(get_qdrant_service)
):
    """Encuentra películas similares a una película dada"""
    try:
        # 1. Obtener embedding de la película base
        base_movie = qdrant_instance.get_movie_by_id(request.movie_id)
        
        if not base_movie or not base_movie.get("vector"):
            raise HTTPException(
                status_code=404,
                detail=f"Película {request.movie_id} no encontrada en base vectorial"
            )
        
        # 2. Validar y convertir vector
        try:
            vector = base_movie["vector"]
            if isinstance(vector, list):
                query_vector = np.array(vector)
            else:
                query_vector = np.array(vector.tolist()) if hasattr(vector, 'tolist') else np.array(vector)
            
            # Verificar dimensiones
            if query_vector.shape[0] != CONFIG_ML32M['embedding_dim']:
                raise ValueError(f"Dimensión de vector incorrecta: {query_vector.shape[0]} vs {CONFIG_ML32M['embedding_dim']}")
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error procesando vector de película {request.movie_id}: {str(e)}"
            )
        
        # 3. Buscar similares
        similar = qdrant_instance.search_similar(
            query_embedding=query_vector,
            k=request.k + 1,  # +1 porque incluirá la película base
            filters=request.filters
        )
        
        # 3. Remover la película base de los resultados
        similar_filtered = [
            movie for movie in similar 
            if movie["movie_id"] != request.movie_id
        ][:request.k]
        
        # 4. Enriquecer con metadata
        base_metadata = await movie_db_instance.get_movie_metadata(request.movie_id)
        for movie in similar_filtered:
            metadata = await movie_db_instance.get_movie_metadata(movie["movie_id"])
            if metadata:
                movie.update({
                    "title": metadata.get("title", "Título desconocido"),
                    "year": metadata.get("year"),
                    "full_genres": metadata.get("genres", "")
                })
        
        return {
            "base_movie": {
                "movie_id": request.movie_id,
                "title": base_metadata.get("title", "Desconocido") if base_metadata else "Desconocido",
                "genres": base_metadata.get("genres", "") if base_metadata else ""
            },
            "similar_movies": similar_filtered,
            "count": len(similar_filtered),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error buscando similares: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/update_user", summary="📝 Actualizar preferencias de usuario")
async def update_user(
    request: UserUpdateRequest,
    background_tasks: BackgroundTasks,
    movie_db_instance = Depends(get_movie_db)
):
    """Actualiza las preferencias de un usuario"""
    try:
        # Actualizar calificación
        await movie_db_instance.update_user_rating(
            user_id=request.user_id,
            movie_id=request.movie_id,
            rating=request.rating
        )
        
        # Tarea en background: recalcular embedding del usuario
        # (opcional para futuras optimizaciones)
        
        return {
            "message": "Preferencias actualizadas",
            "user_id": request.user_id,
            "movie_id": request.movie_id,
            "rating": request.rating,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Error actualizando usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/search_movies", summary="🔍 Buscar películas")
async def search_movies(
    request: SearchRequest,
    movie_db_instance = Depends(get_movie_db)
):
    """Busca películas por título"""
    try:
        results = await movie_db_instance.search_movies(request.query, request.limit)
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/popular_movies", summary="🔥 Películas populares")
async def get_popular_movies(
    limit: int = Query(20, ge=1, le=100, description="Número de películas"),
    movie_db_instance = Depends(get_movie_db)
):
    """Obtiene las películas más populares"""
    try:
        popular = await movie_db_instance.get_popular_movies(limit)
        
        return {
            "popular_movies": popular,
            "count": len(popular),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo populares: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/user_stats/{user_id}", summary="📊 Estadísticas de usuario")
async def get_user_stats(
    user_id: int,
    movie_db_instance = Depends(get_movie_db)
):
    """Obtiene estadísticas de un usuario específico"""
    try:
        stats = await movie_db_instance.get_user_stats(user_id)
        sequence = await movie_db_instance.get_user_sequence(user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "user_id": user_id,
            "stats": stats,
            "sequence_length": len(sequence),
            "recent_movies": sequence[-10:] if sequence else [],
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/health", summary="💚 Estado del sistema")
async def health_check():
    """Verifica el estado de todos los componentes"""
    health_status = {
        "status": "healthy",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "components": {}
    }
    
    try:
        # Verificar base de datos
        if db_manager:
            await db_manager.mongo_client.admin.command('ping')
            await db_manager.redis_client.ping()
            health_status["components"]["database"] = {"status": "ok", "mongodb": "connected", "redis": "connected"}
        else:
            health_status["components"]["database"] = {"status": "error", "detail": "No inicializado"}
        
        # Verificar Qdrant
        if qdrant_service:
            stats = qdrant_service.get_collection_stats()
            health_status["components"]["qdrant"] = {"status": "ok", "stats": stats}
        else:
            health_status["components"]["qdrant"] = {"status": "error", "detail": "No inicializado"}
        
        # Verificar modelo
        if model:
            health_status["components"]["model"] = {
                "status": "ok", 
                "device": str(CONFIG_ML32M['device']),
                "embedding_dim": CONFIG_ML32M['embedding_dim']
            }
        else:
            health_status["components"]["model"] = {"status": "warning", "detail": "Modelo no cargado"}
        
        # Determinar estado general
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "error" in component_statuses:
            health_status["status"] = "degraded"
        elif "warning" in component_statuses:
            health_status["status"] = "partial"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "error",
            "detail": str(e),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }

@app.get("/stats", summary="📈 Estadísticas del sistema")
async def get_system_stats():
    """Obtiene estadísticas generales del sistema"""
    try:
        stats = {}
        
        # Estadísticas de MongoDB usando cliente sincrónico
        if db_manager:
            db = db_manager.sync_mongo_client.movie_recommendations
            try:
                stats["mongodb"] = {
                    "movies": db.movies.estimated_document_count(),
                    "ratings": db.ratings.estimated_document_count(),
                    "users": len(db.ratings.distinct("userId"))
                }
            except Exception as e:
                # Fallback a conteo exacto si no funciona estimated
                stats["mongodb"] = {
                    "movies": db.movies.count_documents({}),
                    "ratings": db.ratings.count_documents({}),
                    "users": len(db.ratings.distinct("userId"))
                }
        
        # Estadísticas de Qdrant
        if qdrant_service:
            stats["qdrant"] = qdrant_service.get_collection_stats()
        
        # Estadísticas de Redis
        if db_manager and db_manager.redis_client:
            redis_info = await db_manager.redis_client.info()
            stats["redis"] = {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory_human", "0B"),
                "keyspace_hits": redis_info.get("keyspace_hits", 0)
            }
        
        return {
            "system_stats": stats,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/genres", summary="🎭 Obtener géneros disponibles")
async def get_available_genres():
    """Obtiene todos los géneros disponibles en el sistema"""
    try:
        return {
            "genres": AVAILABLE_GENRES,
            "count": len(AVAILABLE_GENRES),
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error obteniendo géneros: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/trending_movies", summary="🔥 Películas en tendencia por género")
async def get_trending_movies(
    limit_per_genre: int = Query(10, ge=5, le=20, description="Películas por género"),
    movie_db_instance = Depends(get_movie_db)
):
    """Obtiene películas populares organizadas por género para selección inicial"""
    try:
        trending_by_genre = {}
        
        for genre in AVAILABLE_GENRES:
            # Obtener películas populares del género
            movies = get_movies_by_genre(genre, limit_per_genre * 2)
            
            # Enriquecer con metadata
            enriched_movies = []
            for movie_id in movies[:limit_per_genre]:
                metadata = await movie_db_instance.get_movie_metadata(movie_id)
                if metadata:
                    enriched_movies.append({
                        "movie_id": movie_id,
                        "title": metadata.get("title", "Título desconocido"),
                        "year": metadata.get("year"),
                        "genres": metadata.get("genres", "")
                    })
            
            if enriched_movies:
                trending_by_genre[genre] = enriched_movies
        
        return {
            "trending_by_genre": trending_by_genre,
            "total_genres": len(trending_by_genre),
            "movies_per_genre": limit_per_genre,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo tendencias: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/register_user", summary="👤 Registrar nuevo usuario")
async def register_user(request: UserRegistrationRequest):
    """Registra un nuevo usuario con sus preferencias básicas"""
    try:
        # Validar géneros
        invalid_genres = [g for g in request.preferred_genres if g not in AVAILABLE_GENRES]
        if invalid_genres:
            raise HTTPException(
                status_code=400, 
                detail=f"Géneros inválidos: {invalid_genres}. Géneros disponibles: {AVAILABLE_GENRES}"
            )
        
        # Validar rango de edad
        valid_age_ranges = ["teen", "young_adult", "adult", "senior"]
        if request.age_range not in valid_age_ranges:
            raise HTTPException(
                status_code=400,
                detail=f"Rango de edad inválido. Valores válidos: {valid_age_ranges}"
            )
        
        # Verificar si el email ya existe
        if db_manager:
            existing_user = await db_manager.mongo_client.movie_recommendations.users.find_one(
                {"email": request.email}
            )
            if existing_user:
                raise HTTPException(status_code=400, detail="Email ya registrado")
        
        # Guardar usuario
        user_data = {
            "username": request.username,
            "email": request.email,
            "preferred_genres": request.preferred_genres,
            "age_range": request.age_range,
            "country": request.country
        }
        
        new_user_id = await save_user_profile(user_data)
        
        return {
            "message": "Usuario registrado exitosamente",
            "user_id": new_user_id,
            "username": request.username,
            "preferred_genres": request.preferred_genres,
            "next_step": f"Configurar preferencias detalladas en /set_preferences",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/set_preferences", summary="⚙️ Configurar preferencias detalladas")
async def set_user_preferences(
    request: GenrePreferenceRequest,
    qdrant_instance = Depends(get_qdrant_service)
):
    """Permite al usuario seleccionar películas específicas por género para refinar sus preferencias"""
    try:
        # Verificar que el usuario existe
        if db_manager:
            user = await db_manager.mongo_client.movie_recommendations.users.find_one(
                {"userId": request.user_id}
            )
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Crear embedding inicial basado en selecciones
        user_embedding = create_initial_user_embedding(
            user.get("preferred_genres", []),
            request.movies_by_genre
        )
        
        if user_embedding is not None:
            # Guardar embedding en Qdrant (colección de usuarios)
            try:
                qdrant_instance.save_user_embedding(request.user_id, user_embedding)
                logger.info(f"Embedding guardado para usuario {request.user_id}")
            except Exception as e:
                logger.warning(f"No se pudo guardar embedding en Qdrant: {e}")
        
        # Crear ratings iniciales basados en selecciones
        initial_ratings = []
        for genre, movies in request.movies_by_genre.items():
            for movie_id in movies:
                # Rating alto para películas seleccionadas
                rating = 4.5 if genre in user.get("preferred_genres", []) else 4.0
                initial_ratings.append({
                    "userId": request.user_id,
                    "movieId": movie_id,
                    "rating": rating,
                    "timestamp": int(time.time())
                })
        
        # Guardar ratings iniciales
        if db_manager and initial_ratings:
            await db_manager.mongo_client.movie_recommendations.ratings.insert_many(initial_ratings)
        
        # Marcar como configurado
        if db_manager:
            await db_manager.mongo_client.movie_recommendations.users.update_one(
                {"userId": request.user_id},
                {"$set": {"initial_preferences_set": True}}
            )
        
        return {
            "message": "Preferencias configuradas exitosamente",
            "user_id": request.user_id,
            "initial_ratings_created": len(initial_ratings),
            "embedding_created": user_embedding is not None,
            "ready_for_recommendations": True,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configurando preferencias: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/user_profile/{user_id}", summary="👤 Obtener perfil de usuario")
async def get_user_profile(user_id: int):
    """Obtiene el perfil completo de un usuario registrado"""
    try:
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager no disponible")
        
        # Buscar usuario
        user = await db_manager.mongo_client.movie_recommendations.users.find_one(
            {"userId": user_id},
            {"_id": 0}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Obtener estadísticas adicionales
        if movie_db:
            stats = await movie_db.get_user_stats(user_id)
            sequence = await movie_db.get_user_sequence(user_id)
        else:
            stats = {}
            sequence = []
        
        return {
            "profile": user,
            "stats": stats,
            "activity": {
                "total_ratings": len(sequence),
                "recent_movies": sequence[-10:] if sequence else []
            },
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Para ejecutar: uvicorn api_ml32m_vectorial:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 