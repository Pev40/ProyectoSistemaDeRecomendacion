import os
import json
import asyncio
import grpc
import numpy as np
from typing import List, Dict, Any, Optional
import structlog
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()

class TorchServeClient:
    """Cliente para TorchServe para servir el modelo gSASRec"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, grpc_port: int = 8081):
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.model_name = "gsasrec"
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def predict(self, user_sequence: List[int], k: int = 10) -> List[Dict[str, Any]]:
        """
        Realiza predicción usando TorchServe
        
        Args:
            user_sequence: Secuencia de películas del usuario
            k: Número de recomendaciones a retornar
            
        Returns:
            Lista de recomendaciones con scores
        """
        try:
            # Preparar datos para el modelo
            input_data = {
                "user_sequence": user_sequence,
                "k": k
            }
            
            # Realizar predicción de forma asíncrona
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._predict_sync,
                input_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error en predicción TorchServe: {e}")
            return []
    
    def _predict_sync(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predicción síncrona usando requests"""
        try:
            import requests
            
            url = f"http://{self.host}:{self.port}/predictions/{self.model_name}"
            
            response = requests.post(
                url,
                json=input_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error en predicción: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error en predicción síncrona: {e}")
            return []
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo"""
        try:
            import requests
            
            url = f"http://{self.host}:{self.port}/models/{self.model_name}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error obteniendo información del modelo: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Verifica la salud del servicio TorchServe"""
        try:
            import requests
            
            url = f"http://{self.host}:{self.port}/ping"
            
            response = requests.get(url, timeout=5)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error en health check de TorchServe: {e}")
            return False

class ModelManager:
    """Gestor de modelos para diferentes estrategias de recomendación"""
    
    def __init__(self):
        self.torchserve_client = TorchServeClient()
        self.faiss_index = None
        self.qdrant_service = None
        
    async def get_user_embedding(self, user_sequence: List[int]) -> Optional[np.ndarray]:
        """
        Obtiene el embedding de un usuario usando TorchServe
        
        Args:
            user_sequence: Secuencia de películas del usuario
            
        Returns:
            Embedding del usuario o None si hay error
        """
        try:
            # Usar TorchServe para obtener embedding
            result = await self.torchserve_client.predict(user_sequence, k=1)
            
            if result and len(result) > 0:
                # Extraer embedding del resultado
                embedding = result[0].get("user_embedding")
                if embedding:
                    return np.array(embedding)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo embedding de usuario: {e}")
            return None
    
    async def get_recommendations(self, user_sequence: List[int], k: int = 10, 
                                 method: str = "torchserve") -> List[Dict[str, Any]]:
        """
        Obtiene recomendaciones usando diferentes métodos
        
        Args:
            user_sequence: Secuencia de películas del usuario
            k: Número de recomendaciones
            method: Método a usar ("torchserve", "faiss", "qdrant")
            
        Returns:
            Lista de recomendaciones
        """
        try:
            if method == "torchserve":
                return await self.torchserve_client.predict(user_sequence, k)
            
            elif method == "faiss":
                if not self.faiss_index:
                    raise ValueError("Índice FAISS no inicializado")
                
                user_embedding = await self.get_user_embedding(user_sequence)
                if user_embedding is None:
                    return []
                
                movie_ids, scores = self.faiss_index.search(user_embedding, k)
                
                recommendations = []
                for movie_id, score in zip(movie_ids, scores):
                    recommendations.append({
                        "movie_id": movie_id,
                        "score": float(score)
                    })
                
                return recommendations
            
            elif method == "qdrant":
                if not self.qdrant_service:
                    raise ValueError("Servicio Qdrant no inicializado")
                
                user_embedding = await self.get_user_embedding(user_sequence)
                if user_embedding is None:
                    return []
                
                return self.qdrant_service.search_similar(user_embedding, k)
            
            else:
                raise ValueError(f"Método no soportado: {method}")
                
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones: {e}")
            return []
    
    async def batch_recommendations(self, user_sequences: List[List[int]], 
                                  k: int = 10, method: str = "torchserve") -> List[List[Dict[str, Any]]]:
        """
        Obtiene recomendaciones en lote
        
        Args:
            user_sequences: Lista de secuencias de usuarios
            k: Número de recomendaciones por usuario
            method: Método a usar
            
        Returns:
            Lista de listas de recomendaciones
        """
        try:
            if method == "torchserve":
                # TorchServe puede manejar lotes directamente
                tasks = [self.torchserve_client.predict(seq, k) for seq in user_sequences]
                return await asyncio.gather(*tasks)
            
            elif method == "faiss":
                if not self.faiss_index:
                    raise ValueError("Índice FAISS no inicializado")
                
                # Obtener embeddings de usuarios
                user_embeddings = []
                for seq in user_sequences:
                    embedding = await self.get_user_embedding(seq)
                    if embedding is not None:
                        user_embeddings.append(embedding)
                
                if not user_embeddings:
                    return []
                
                user_embeddings = np.array(user_embeddings)
                
                # Búsqueda en lote
                batch_results = self.faiss_index.batch_search(user_embeddings, k)
                
                return batch_results
            
            else:
                raise ValueError(f"Método no soportado para lotes: {method}")
                
        except Exception as e:
            logger.error(f"Error en recomendaciones en lote: {e}")
            return []

# Instancia global
model_manager = ModelManager()

async def init_model_manager():
    """Inicializa el gestor de modelos"""
    global model_manager
    
    # Verificar que TorchServe esté disponible
    if await model_manager.torchserve_client.health_check():
        logger.info("TorchServe disponible")
    else:
        logger.warning("TorchServe no disponible")
    
    logger.info("Gestor de modelos inicializado")

async def close_model_manager():
    """Cierra el gestor de modelos"""
    if model_manager.executor:
        model_manager.executor.shutdown(wait=True)
    logger.info("Gestor de modelos cerrado") 