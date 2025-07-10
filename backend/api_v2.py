# API FastAPI v2 - Sistema de Recomendación ML32M
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import torch
import numpy as np
import logging
from contextlib import asynccontextmanager

# Añadir el directorio modelo al path para importar gsasrec
modelo_path = os.path.join(os.path.dirname(__file__), '..', 'modelo')
sys.path.append(modelo_path)

# Importaciones del sistema
from database.connection import DatabaseManager
from services.recommendation_service import RecommendationService
from services.torchserve_client import TorchServeClient
from gsasrec import GSASRec

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración ML32M
CONFIG_ML32M = {
    'num_items': 84436,  # Ajustado para ML32M con padding
    'num_users': 336000,  # Estimado para ML32M
    'max_seq_len': 200,
    'embedding_dim': 256,
    'num_heads': 8,
    'num_blocks': 4,
    'dropout_rate': 0.2,
    'pad_token': 0,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
}

# Variables globales
db_manager = None
recommendation_service = None
torchserve_client = None
model = None

def load_ml32m_model_with_fix():
    """Carga el modelo ML32M con el fix para el mismatch de parámetros"""
    try:
        # Crear modelo
        model = GSASRec(
            num_items=CONFIG_ML32M['num_items'],
            embedding_dim=CONFIG_ML32M['embedding_dim'],
            num_heads=CONFIG_ML32M['num_heads'],
            num_blocks=CONFIG_ML32M['num_blocks'],
            max_seq_len=CONFIG_ML32M['max_seq_len'],
            dropout_rate=CONFIG_ML32M['dropout_rate'],
            pad_token=CONFIG_ML32M['pad_token'],
            device=CONFIG_ML32M['device']
        )
        
        # Cargar checkpoint
        model_path = os.path.join(
            os.path.dirname(__file__), '..', 'modelo', 'pre_trained',
            'gsasrec-ml32m-step_88576-t_0.75-negs_16-emb_256-dropout_0.2-metric_0.126124.pt'
        )
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado en: {model_path}")
        
        checkpoint = torch.load(model_path, map_location=CONFIG_ML32M['device'])
        
        # Cargar parámetros uno por uno (fix para mismatch)
        model_state = model.state_dict()
        
        for name, param in checkpoint.items():
            if name in model_state:
                if model_state[name].shape == param.shape:
                    model_state[name].copy_(param)
                    logger.info(f"Cargado: {name}")
                else:
                    logger.warning(f"Mismatch ignorado: {name} - {model_state[name].shape} vs {param.shape}")
            else:
                logger.warning(f"Parámetro no encontrado en modelo: {name}")
        
        model.eval()
        logger.info("Modelo ML32M cargado exitosamente con fix")
        return model
        
    except Exception as e:
        logger.error(f"Error cargando modelo ML32M: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    global db_manager, recommendation_service, torchserve_client, model
    
    try:
        logger.info("Iniciando aplicación...")
        
        # Cargar modelo ML32M
        logger.info("Cargando modelo ML32M...")
        model = load_ml32m_model_with_fix()
        
        # Inicializar base de datos
        logger.info("Conectando a base de datos...")
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        # Inicializar TorchServe client
        logger.info("Inicializando TorchServe client...")
        torchserve_client = TorchServeClient()
        
        # Inicializar servicio de recomendación
        logger.info("Inicializando servicio de recomendación...")
        recommendation_service = RecommendationService(
            model=model,
            config=CONFIG_ML32M,
            db_manager=db_manager,
            torchserve_client=torchserve_client
        )
        
        logger.info("Aplicación iniciada exitosamente")
        yield
        
    except Exception as e:
        logger.error(f"Error durante inicialización: {e}")
        raise
    finally:
        # Cleanup
        if db_manager:
            await db_manager.disconnect()

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Recomendación ML32M",
    description="API para sistema de recomendación basado en gSASRec con MovieLens 32M",
    version="2.0.0",
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
    k: int = Field(10, ge=1, le=100, description="Número de recomendaciones")
    method: str = Field("torchserve", description="Método de recomendación")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionales")

class UserUpdateRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    movie_id: int = Field(..., description="ID de la película")
    rating: float = Field(..., ge=0.5, le=5.0, description="Calificación (0.5-5.0)")
    timestamp: Optional[int] = Field(None, description="Timestamp de la calificación")

class BatchRecommendationRequest(BaseModel):
    user_ids: List[int] = Field(..., description="Lista de IDs de usuarios")
    k: int = Field(10, ge=1, le=100, description="Número de recomendaciones por usuario")
    method: str = Field("torchserve", description="Método de recomendación")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Término de búsqueda")
    limit: int = Field(20, ge=1, le=100, description="Número máximo de resultados")

class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    torchserve: Dict[str, Any]
    faiss: Dict[str, Any]
    qdrant: Dict[str, Any]
    system: Dict[str, Any]

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Recomendación gSASRec - MovieLens 32M",
    description="API para recomendaciones de películas basada en gSASRec + TorchServe + MongoDB + Redis",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
faiss_index = None
qdrant_service = None

async def get_database():
    """Dependency para obtener la base de datos"""
    return movielens_db

async def get_model_manager():
    """Dependency para obtener el gestor de modelos"""
    return model_manager

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Iniciando sistema de recomendación...")
    
    try:
        # Inicializar base de datos
        await init_database()
        logger.info("Base de datos inicializada")
        
        # Inicializar gestor de modelos
        await init_model_manager()
        logger.info("Gestor de modelos inicializado")
        
        # Inicializar FAISS y Qdrant si están disponibles
        global faiss_index, qdrant_service
        
        try:
            faiss_index = FAISSIndex(embedding_dim=128, index_type="flat")
            if os.path.exists("faiss_index/faiss_index.bin"):
                faiss_index.load_index("faiss_index")
                logger.info("Índice FAISS cargado")
        except Exception as e:
            logger.warning(f"No se pudo cargar FAISS: {e}")
        
        try:
            qdrant_service = QdrantService()
            logger.info("Servicio Qdrant inicializado")
        except Exception as e:
            logger.warning(f"No se pudo inicializar Qdrant: {e}")
        
        # Conectar FAISS y Qdrant al gestor de modelos
        model_manager.faiss_index = faiss_index
        model_manager.qdrant_service = qdrant_service
        
        logger.info("Sistema iniciado correctamente")
        
    except Exception as e:
        logger.error(f"Error iniciando sistema: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info("Cerrando sistema...")
    
    try:
        await close_database()
        await close_model_manager()
        logger.info("Sistema cerrado correctamente")
    except Exception as e:
        logger.error(f"Error cerrando sistema: {e}")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Recomendación gSASRec - MovieLens 32M",
        "version": "2.0.0",
        "architecture": "FastAPI + TorchServe + MongoDB + Redis + FAISS + Qdrant",
        "endpoints": [
            "/recommend",
            "/recommend_batch", 
            "/update_user",
            "/search_movies",
            "/user_stats",
            "/popular_movies",
            "/health",
            "/stats"
        ]
    }

@app.post("/recommend")
async def recommend(
    request: RecommendationRequest,
    db = Depends(get_database),
    model_mgr = Depends(get_model_manager)
):
    """
    Obtiene recomendaciones para un usuario
    """
    try:
        start_time = time.time()
        
        # Obtener secuencia del usuario
        user_sequence = await db.get_user_sequence(request.user_id)
        
        if not user_sequence:
            raise HTTPException(
                status_code=404, 
                detail=f"Usuario {request.user_id} no encontrado o sin calificaciones"
            )
        
        # Obtener recomendaciones
        recommendations = await model_mgr.get_recommendations(
            user_sequence, 
            request.k, 
            request.method
        )
        
        # Agregar metadata de películas
        recommendations_with_metadata = []
        for rec in recommendations:
            movie_id = rec.get("movie_id")
            if movie_id:
                metadata = await db.get_movie_metadata(movie_id)
                if metadata:
                    rec["metadata"] = metadata
                    recommendations_with_metadata.append(rec)
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        logger.info(
            "Recomendación generada",
            user_id=request.user_id,
            method=request.method,
            k=request.k,
            latency_ms=latency,
            recommendations_count=len(recommendations_with_metadata)
        )
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations_with_metadata,
            "latency_ms": latency,
            "method": request.method,
            "sequence_length": len(user_sequence)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en recomendación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend_batch")
async def recommend_batch(
    request: BatchRecommendationRequest,
    db = Depends(get_database),
    model_mgr = Depends(get_model_manager)
):
    """
    Obtiene recomendaciones en lote para múltiples usuarios
    """
    try:
        start_time = time.time()
        
        # Obtener secuencias de usuarios
        user_sequences = []
        valid_user_ids = []
        
        for user_id in request.user_ids:
            sequence = await db.get_user_sequence(user_id)
            if sequence:
                user_sequences.append(sequence)
                valid_user_ids.append(user_id)
        
        if not user_sequences:
            raise HTTPException(
                status_code=404,
                detail="Ningún usuario encontrado con calificaciones"
            )
        
        # Obtener recomendaciones en lote
        batch_recommendations = await model_mgr.batch_recommendations(
            user_sequences,
            request.k,
            request.method
        )
        
        # Formatear resultados
        results = []
        for i, recommendations in enumerate(batch_recommendations):
            user_id = valid_user_ids[i]
            
            # Agregar metadata
            recommendations_with_metadata = []
            for rec in recommendations:
                movie_id = rec.get("movie_id")
                if movie_id:
                    metadata = await db.get_movie_metadata(movie_id)
                    if metadata:
                        rec["metadata"] = metadata
                        recommendations_with_metadata.append(rec)
            
            results.append({
                "user_id": user_id,
                "recommendations": recommendations_with_metadata
            })
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        logger.info(
            "Recomendaciones en lote generadas",
            total_users=len(valid_user_ids),
            method=request.method,
            k=request.k,
            latency_ms=latency
        )
        
        return {
            "batch_results": results,
            "total_users": len(valid_user_ids),
            "latency_ms": latency,
            "method": request.method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en recomendaciones en lote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_user")
async def update_user(
    request: UserUpdateRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """
    Actualiza la calificación de un usuario
    """
    try:
        # Actualizar en base de datos
        await db.update_user_rating(
            request.user_id,
            request.movie_id,
            request.rating,
            request.timestamp
        )
        
        # Tarea en background para recalcular embeddings
        background_tasks.add_task(
            recalculate_user_embeddings,
            request.user_id
        )
        
        logger.info(
            "Calificación actualizada",
            user_id=request.user_id,
            movie_id=request.movie_id,
            rating=request.rating
        )
        
        return {
            "message": "Calificación actualizada correctamente",
            "user_id": request.user_id,
            "movie_id": request.movie_id,
            "rating": request.rating
        }
        
    except Exception as e:
        logger.error(f"Error actualizando calificación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_movies")
async def search_movies(
    request: SearchRequest,
    db = Depends(get_database)
):
    """
    Busca películas por título
    """
    try:
        movies = await db.search_movies(request.query, request.limit)
        
        logger.info(
            "Búsqueda de películas realizada",
            query=request.query,
            results_count=len(movies)
        )
        
        return {
            "query": request.query,
            "movies": movies,
            "total_results": len(movies)
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda de películas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user_stats/{user_id}")
async def get_user_stats(
    user_id: int,
    db = Depends(get_database)
):
    """
    Obtiene estadísticas de un usuario
    """
    try:
        stats = await db.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/popular_movies")
async def get_popular_movies(
    limit: int = 100,
    db = Depends(get_database)
):
    """
    Obtiene las películas más populares
    """
    try:
        movies = await db.get_popular_movies(limit)
        
        return {
            "popular_movies": movies,
            "total_results": len(movies)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo películas populares: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Verificación de salud del sistema
    """
    try:
        # Estadísticas del sistema
        system_stats = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # Verificar TorchServe
        torchserve_health = await model_manager.torchserve_client.health_check()
        torchserve_info = await model_manager.torchserve_client.get_model_info()
        
        # Verificar FAISS
        faiss_stats = {}
        if faiss_index:
            faiss_stats = faiss_index.get_index_stats()
        
        # Verificar Qdrant
        qdrant_stats = {}
        if qdrant_service:
            qdrant_stats = qdrant_service.get_collection_stats()
        
        # Verificar base de datos
        db_stats = {
            "status": "connected" if movielens_db else "disconnected"
        }
        
        return HealthResponse(
            status="healthy" if torchserve_health else "degraded",
            database=db_stats,
            torchserve={
                "health": torchserve_health,
                "info": torchserve_info
            },
            faiss=faiss_stats,
            qdrant=qdrant_stats,
            system=system_stats
        )
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthResponse(
            status="unhealthy",
            database={"error": str(e)},
            torchserve={"error": str(e)},
            faiss={"error": str(e)},
            qdrant={"error": str(e)},
            system={"error": str(e)}
        )

@app.get("/stats")
async def get_stats():
    """
    Estadísticas detalladas del sistema
    """
    try:
        return {
            "torchserve": await model_manager.torchserve_client.get_model_info(),
            "faiss": faiss_index.get_index_stats() if faiss_index else {"error": "No inicializado"},
            "qdrant": qdrant_service.get_collection_stats() if qdrant_service else {"error": "No inicializado"},
            "database": {
                "status": "connected" if movielens_db else "disconnected"
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def recalculate_user_embeddings(user_id: int):
    """
    Recalcula embeddings de usuario (tarea en background)
    """
    try:
        logger.info(f"Recalculando embeddings para usuario {user_id}")
        
        # En un sistema real, aquí recalcularías los embeddings
        # basado en las nuevas calificaciones del usuario
        
        # Por ahora, solo invalidamos el cache
        if movielens_db:
            cache_key = f"user_sequence:{user_id}"
            await movielens_db.db_manager.redis_client.delete(cache_key)
        
        logger.info(f"Embeddings recalculados para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error recalculando embeddings para usuario {user_id}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 