# API FastAPI v2 - Sistema de Recomendación ML32M
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import sys
import torch
import numpy as np
import logging
import time
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
        loaded_params = 0
        skipped_params = 0
        
        for name, param in checkpoint.items():
            if name in model_state:
                if model_state[name].shape == param.shape:
                    model_state[name].copy_(param)
                    loaded_params += 1
                else:
                    logger.warning(f"Mismatch ignorado: {name} - {model_state[name].shape} vs {param.shape}")
                    skipped_params += 1
            else:
                logger.warning(f"Parámetro no encontrado en modelo: {name}")
                skipped_params += 1
        
        model.eval()
        logger.info(f"Modelo ML32M cargado: {loaded_params} parámetros cargados, {skipped_params} omitidos")
        return model
        
    except Exception as e:
        logger.error(f"Error cargando modelo ML32M: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    global db_manager, recommendation_service, torchserve_client, model
    
    try:
        logger.info("Iniciando aplicación ML32M...")
        
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
        
        logger.info("Aplicación ML32M iniciada exitosamente")
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
    method: str = Field("local", description="Método de recomendación (local/torchserve)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionales")

class UserUpdateRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    movie_id: int = Field(..., description="ID de la película")
    rating: float = Field(..., ge=0.5, le=5.0, description="Calificación (0.5-5.0)")
    timestamp: Optional[int] = Field(None, description="Timestamp de la calificación")

class BatchRecommendationRequest(BaseModel):
    user_ids: List[int] = Field(..., description="Lista de IDs de usuarios")
    k: int = Field(10, ge=1, le=100, description="Número de recomendaciones por usuario")
    method: str = Field("local", description="Método de recomendación")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Término de búsqueda")
    limit: int = Field(20, ge=1, le=100, description="Número máximo de resultados")

class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    model: Dict[str, Any]
    system: Dict[str, Any]

# Dependencies
async def get_db_manager():
    """Dependency para obtener el database manager"""
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database manager no inicializado")
    return db_manager

async def get_recommendation_service():
    """Dependency para obtener el servicio de recomendación"""
    if recommendation_service is None:
        raise HTTPException(status_code=500, detail="Servicio de recomendación no inicializado")
    return recommendation_service

# Endpoints
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Recomendación ML32M",
        "version": "2.0.0",
        "architecture": "FastAPI + gSASRec + MongoDB + Redis + FAISS",
        "model": "gSASRec ML32M (84436 items, embedding_dim=256)",
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
    rec_service = Depends(get_recommendation_service)
):
    """Obtiene recomendaciones para un usuario"""
    try:
        start_time = time.time()
        
        logger.info(f"Generando recomendaciones para usuario {request.user_id}")
        
        # Obtener recomendaciones
        recommendations = await rec_service.get_recommendations(
            user_id=request.user_id,
            k=request.k,
            method=request.method,
            filters=request.filters
        )
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        logger.info(f"Recomendaciones generadas en {latency:.2f}ms")
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations,
            "latency_ms": round(latency, 2),
            "method": request.method,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error en recomendación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend_batch")
async def recommend_batch(
    request: BatchRecommendationRequest,
    rec_service = Depends(get_recommendation_service)
):
    """Obtiene recomendaciones en lote para múltiples usuarios"""
    try:
        start_time = time.time()
        
        logger.info(f"Generando recomendaciones batch para {len(request.user_ids)} usuarios")
        
        # Obtener recomendaciones en lote
        batch_recommendations = await rec_service.get_batch_recommendations(
            user_ids=request.user_ids,
            k=request.k,
            method=request.method
        )
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        return {
            "user_ids": request.user_ids,
            "recommendations": batch_recommendations,
            "latency_ms": round(latency, 2),
            "method": request.method,
            "users_processed": len(batch_recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error en recomendación batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_user")
async def update_user(
    request: UserUpdateRequest,
    background_tasks: BackgroundTasks,
    db_mgr = Depends(get_db_manager)
):
    """Actualiza la calificación de un usuario"""
    try:
        # Actualizar rating en la base de datos
        await db_mgr.update_user_rating(
            user_id=request.user_id,
            movie_id=request.movie_id,
            rating=request.rating,
            timestamp=request.timestamp
        )
        
        # Programar recálculo de embeddings en segundo plano
        background_tasks.add_task(
            recalculate_user_embeddings,
            request.user_id
        )
        
        return {
            "message": "Rating actualizado correctamente",
            "user_id": request.user_id,
            "movie_id": request.movie_id,
            "rating": request.rating
        }
        
    except Exception as e:
        logger.error(f"Error actualizando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_movies")
async def search_movies(
    request: SearchRequest,
    db_mgr = Depends(get_db_manager)
):
    """Busca películas por término"""
    try:
        movies = await db_mgr.search_movies(
            query=request.query,
            limit=request.limit
        )
        
        return {
            "query": request.query,
            "movies": movies,
            "count": len(movies)
        }
        
    except Exception as e:
        logger.error(f"Error buscando películas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user_stats/{user_id}")
async def get_user_stats(
    user_id: int,
    db_mgr = Depends(get_db_manager)
):
    """Obtiene estadísticas de un usuario"""
    try:
        stats = await db_mgr.get_user_stats(user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/popular_movies")
async def get_popular_movies(
    limit: int = 100,
    db_mgr = Depends(get_db_manager)
):
    """Obtiene películas populares"""
    try:
        movies = await db_mgr.get_popular_movies(limit=limit)
        
        return {
            "movies": movies,
            "count": len(movies)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo películas populares: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Verifica el estado del sistema"""
    try:
        health_status = {
            "status": "healthy",
            "database": {"status": "unknown"},
            "model": {"status": "unknown"},
            "system": {
                "device": CONFIG_ML32M['device'],
                "embedding_dim": CONFIG_ML32M['embedding_dim'],
                "num_items": CONFIG_ML32M['num_items']
            }
        }
        
        # Verificar base de datos
        if db_manager:
            try:
                await db_manager.health_check()
                health_status["database"]["status"] = "healthy"
            except Exception as e:
                health_status["database"]["status"] = "unhealthy"
                health_status["database"]["error"] = str(e)
        
        # Verificar modelo
        if model:
            try:
                # Test inference
                test_sequence = torch.randint(1, 1000, (1, 10)).to(CONFIG_ML32M['device'])
                with torch.no_grad():
                    _ = model(test_sequence)
                health_status["model"]["status"] = "healthy"
                health_status["model"]["parameters"] = sum(p.numel() for p in model.parameters())
            except Exception as e:
                health_status["model"]["status"] = "unhealthy"
                health_status["model"]["error"] = str(e)
        
        # Determinar estado general
        if (health_status["database"]["status"] == "healthy" and 
            health_status["model"]["status"] == "healthy"):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/stats")
async def get_stats():
    """Obtiene estadísticas del sistema"""
    try:
        stats = {
            "model": {
                "name": "gSASRec ML32M",
                "embedding_dim": CONFIG_ML32M['embedding_dim'],
                "num_items": CONFIG_ML32M['num_items'],
                "num_blocks": CONFIG_ML32M['num_blocks'],
                "device": CONFIG_ML32M['device']
            },
            "system": {
                "pytorch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available()
            }
        }
        
        if model:
            stats["model"]["parameters"] = sum(p.numel() for p in model.parameters())
            stats["model"]["model_size_mb"] = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)
        
        if db_manager:
            db_stats = await db_manager.get_stats()
            stats["database"] = db_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Funciones auxiliares
async def recalculate_user_embeddings(user_id: int):
    """Recalcula embeddings del usuario en segundo plano"""
    try:
        if recommendation_service:
            await recommendation_service.update_user_embeddings(user_id)
            logger.info(f"Embeddings actualizados para usuario {user_id}")
    except Exception as e:
        logger.error(f"Error recalculando embeddings para usuario {user_id}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 