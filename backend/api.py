from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import numpy as np
import time
import psutil
import os
import sys
from pathlib import Path

# Agregar el directorio del modelo al path
sys.path.append(str(Path(__file__).parent.parent / "modelo"))

from embedding_exporter import EmbeddingExporter
from faiss_index import FAISSIndex
from qdrant_service import QdrantService

# Modelos Pydantic
class RecommendationRequest(BaseModel):
    user_id: int
    k: int = 10
    filters: Optional[Dict[str, Any]] = None

class UserUpdateRequest(BaseModel):
    user_id: int
    movie_id: int
    rating: float

class BatchRecommendationRequest(BaseModel):
    user_ids: List[int]
    k: int = 10

class HealthResponse(BaseModel):
    status: str
    faiss_stats: Dict[str, Any]
    qdrant_stats: Dict[str, Any]
    system_stats: Dict[str, Any]

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Recomendación gSASRec",
    description="API para recomendaciones de películas basada en gSASRec + FAISS + Qdrant",
    version="1.0.0"
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
embedding_exporter = None
user_embeddings_cache = {}

def initialize_services():
    """Inicializa todos los servicios"""
    global faiss_index, qdrant_service, embedding_exporter
    
    try:
        # Inicializar exportador de embeddings
        model_path = "../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
        embedding_exporter = EmbeddingExporter(model_path)
        
        # Cargar o crear índice FAISS
        faiss_index = FAISSIndex(embedding_dim=128, index_type="flat")
        if os.path.exists("faiss_index/faiss_index.bin"):
            faiss_index.load_index("faiss_index")
            print("Índice FAISS cargado desde disco")
        else:
            # Crear nuevo índice
            data = embedding_exporter.export_embeddings()
            faiss_index.create_index(data["item_embeddings"], data["item_mapping"])
            faiss_index.save_index("faiss_index")
            print("Nuevo índice FAISS creado")
        
        # Inicializar servicio Qdrant
        qdrant_service = QdrantService()
        
        print("Todos los servicios inicializados correctamente")
        
    except Exception as e:
        print(f"Error inicializando servicios: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    initialize_services()

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Recomendación gSASRec API",
        "version": "1.0.0",
        "endpoints": [
            "/recommend_fast",
            "/recommend_filter",
            "/recommend_batch",
            "/update_user",
            "/health",
            "/stats"
        ]
    }

@app.post("/recommend_fast")
async def recommend_fast(request: RecommendationRequest):
    """
    Recomendación rápida usando FAISS (sin filtros)
    """
    try:
        start_time = time.time()
        
        # Obtener embedding del usuario
        user_embedding = get_user_embedding(request.user_id)
        
        # Buscar en FAISS
        movie_ids, scores = faiss_index.search(user_embedding, request.k)
        
        # Obtener metadata de Qdrant
        recommendations = []
        for movie_id, score in zip(movie_ids, scores):
            movie_info = qdrant_service.get_movie_by_id(movie_id)
            if movie_info:
                recommendations.append({
                    "movie_id": movie_id,
                    "title": movie_info["title"],
                    "genres": movie_info["genres"],
                    "year": movie_info["year"],
                    "score": float(score)
                })
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations,
            "latency_ms": latency,
            "method": "faiss_fast"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend_filter")
async def recommend_filter(request: RecommendationRequest):
    """
    Recomendación con filtros usando Qdrant
    """
    try:
        start_time = time.time()
        
        # Obtener embedding del usuario
        user_embedding = get_user_embedding(request.user_id)
        
        # Buscar en Qdrant con filtros
        results = qdrant_service.search_similar(
            user_embedding, 
            request.k, 
            request.filters
        )
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        return {
            "user_id": request.user_id,
            "recommendations": results,
            "latency_ms": latency,
            "method": "qdrant_filtered",
            "filters_applied": request.filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend_batch")
async def recommend_batch(request: BatchRecommendationRequest):
    """
    Recomendaciones en lote para múltiples usuarios
    """
    try:
        start_time = time.time()
        
        # Obtener embeddings de usuarios
        user_embeddings = []
        for user_id in request.user_ids:
            user_embedding = get_user_embedding(user_id)
            user_embeddings.append(user_embedding)
        
        user_embeddings = np.array(user_embeddings)
        
        # Búsqueda en lote con FAISS
        batch_results = faiss_index.batch_search(user_embeddings, request.k)
        
        # Formatear resultados
        all_recommendations = []
        for i, (movie_ids, scores) in enumerate(batch_results):
            user_recommendations = []
            for movie_id, score in zip(movie_ids, scores):
                movie_info = qdrant_service.get_movie_by_id(movie_id)
                if movie_info:
                    user_recommendations.append({
                        "movie_id": movie_id,
                        "title": movie_info["title"],
                        "genres": movie_info["genres"],
                        "year": movie_info["year"],
                        "score": float(score)
                    })
            
            all_recommendations.append({
                "user_id": request.user_ids[i],
                "recommendations": user_recommendations
            })
        
        latency = (time.time() - start_time) * 1000  # en ms
        
        return {
            "batch_results": all_recommendations,
            "total_users": len(request.user_ids),
            "latency_ms": latency,
            "method": "faiss_batch"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_user")
async def update_user(request: UserUpdateRequest, background_tasks: BackgroundTasks):
    """
    Actualiza el perfil del usuario después de una nueva calificación
    """
    try:
        # En un sistema real, aquí actualizarías la base de datos
        # y recalcularías el embedding del usuario
        
        # Por ahora, solo invalidamos el cache
        if request.user_id in user_embeddings_cache:
            del user_embeddings_cache[request.user_id]
        
        # Tarea en background para recalcular embedding
        background_tasks.add_task(recalculate_user_embedding, request.user_id)
        
        return {
            "message": "Usuario actualizado",
            "user_id": request.user_id,
            "movie_id": request.movie_id,
            "rating": request.rating
        }
        
    except Exception as e:
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
            "memory_available": psutil.virtual_memory().available // (1024**3),  # GB
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        # Estadísticas de FAISS
        faiss_stats = faiss_index.get_index_stats() if faiss_index else {"error": "No inicializado"}
        
        # Estadísticas de Qdrant
        qdrant_stats = qdrant_service.get_collection_stats() if qdrant_service else {"error": "No inicializado"}
        
        return HealthResponse(
            status="healthy",
            faiss_stats=faiss_stats,
            qdrant_stats=qdrant_stats,
            system_stats=system_stats
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            faiss_stats={"error": str(e)},
            qdrant_stats={"error": str(e)},
            system_stats={"error": str(e)}
        )

@app.get("/stats")
async def get_stats():
    """
    Estadísticas detalladas del sistema
    """
    try:
        return {
            "faiss": faiss_index.get_index_stats() if faiss_index else {"error": "No inicializado"},
            "qdrant": qdrant_service.get_collection_stats() if qdrant_service else {"error": "No inicializado"},
            "cache": {
                "cached_users": len(user_embeddings_cache),
                "total_users": 6040  # Para ML-1M
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_user_embedding(user_id: int) -> np.ndarray:
    """
    Obtiene el embedding de un usuario (con cache)
    """
    if user_id in user_embeddings_cache:
        return user_embeddings_cache[user_id]
    
    # En un sistema real, aquí cargarías la secuencia del usuario
    # y generarías el embedding usando el modelo
    # Por ahora, usamos un embedding aleatorio como placeholder
    
    # Simular secuencia de usuario (en producción, esto vendría de la BD)
    user_sequence = generate_user_sequence(user_id)
    
    # Generar embedding usando el modelo
    user_embedding = embedding_exporter.extract_user_embeddings([user_sequence])[0]
    
    # Cachear el resultado
    user_embeddings_cache[user_id] = user_embedding
    
    return user_embedding

def generate_user_sequence(user_id: int) -> List[int]:
    """
    Genera una secuencia de usuario (placeholder)
    En producción, esto vendría de la base de datos
    """
    # Simular una secuencia de películas vistas por el usuario
    # En un sistema real, esto se cargaría desde la BD
    np.random.seed(user_id)  # Para reproducibilidad
    num_movies = np.random.randint(5, 50)
    sequence = np.random.choice(range(1, 3417), num_movies, replace=False).tolist()
    return sequence

def recalculate_user_embedding(user_id: int):
    """
    Recalcula el embedding de un usuario (tarea en background)
    """
    try:
        # En un sistema real, aquí recalcularías el embedding
        # basado en las nuevas calificaciones del usuario
        
        # Por ahora, solo invalidamos el cache
        if user_id in user_embeddings_cache:
            del user_embeddings_cache[user_id]
        
        print(f"Embedding recalculado para usuario {user_id}")
        
    except Exception as e:
        print(f"Error recalculando embedding para usuario {user_id}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 