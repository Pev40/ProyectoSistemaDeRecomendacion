import numpy as np
import json
import os
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range, MatchValue
)
import time

class QdrantService:
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "movies"):
        """
        Inicializa el servicio Qdrant
        
        Args:
            host: Host de Qdrant
            port: Puerto de Qdrant
            collection_name: Nombre de la colección
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embedding_dim = 128
        
    def create_collection(self, embedding_dim: int = 128):
        """Crea la colección en Qdrant"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE
                )
            )
            print(f"Colección '{self.collection_name}' creada exitosamente")
        except Exception as e:
            print(f"La colección ya existe o error: {e}")
    
    def insert_movies(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Inserta películas con embeddings y metadata
        
        Args:
            embeddings: Array de embeddings (N x embedding_dim)
            metadata: Lista de diccionarios con metadata de cada película
        """
        points = []
        
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            point = PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={
                    "movie_id": meta.get("movie_id", i),
                    "title": meta.get("title", f"Movie {i}"),
                    "genres": meta.get("genres", []),
                    "year": meta.get("year", 0),
                    "rating": meta.get("rating", 0.0),
                    "num_ratings": meta.get("num_ratings", 0)
                }
            )
            points.append(point)
        
        # Insertar en lotes para mejor rendimiento
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        print(f"Insertadas {len(points)} películas en Qdrant")
    
    def search_similar(self, query_embedding: np.ndarray, k: int = 10, 
                      filters: Optional[Dict] = None) -> List[Dict]:
        """
        Busca películas similares con filtros opcionales
        
        Args:
            query_embedding: Embedding de consulta
            k: Número de resultados
            filters: Filtros opcionales (género, año, etc.)
            
        Returns:
            Lista de resultados con metadata
        """
        # Construir filtros
        search_filter = None
        if filters:
            conditions = []
            
            if "genres" in filters:
                conditions.append(
                    FieldCondition(
                        key="genres",
                        match=MatchValue(value=filters["genres"])
                    )
                )
            
            if "year_min" in filters or "year_max" in filters:
                year_range = {}
                if "year_min" in filters:
                    year_range["gte"] = filters["year_min"]
                if "year_max" in filters:
                    year_range["lte"] = filters["year_max"]
                
                conditions.append(
                    FieldCondition(
                        key="year",
                        range=Range(**year_range)
                    )
                )
            
            if "rating_min" in filters:
                conditions.append(
                    FieldCondition(
                        key="rating",
                        range=Range(gte=filters["rating_min"])
                    )
                )
            
            if conditions:
                search_filter = Filter(must=conditions)
        
        # Realizar búsqueda
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=k,
            query_filter=search_filter,
            with_payload=True
        )
        
        # Formatear resultados
        formatted_results = []
        for result in results:
            formatted_results.append({
                "movie_id": result.payload.get("movie_id"),
                "title": result.payload.get("title"),
                "genres": result.payload.get("genres", []),
                "year": result.payload.get("year"),
                "rating": result.payload.get("rating"),
                "score": result.score
            })
        
        return formatted_results
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        """Obtiene una película específica por ID"""
        try:
            # Usar scroll con with_vectors=True para obtener el vector
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="movie_id",
                            match=MatchValue(value=movie_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=True  # Importante para obtener el vector
            )
            
            # Verificar que hay resultados
            if results and len(results) >= 2 and results[0] and len(results[0]) > 0:
                result = results[0][0]  # results es (records, next_page_offset)
                
                # Verificar que el vector existe
                if hasattr(result, 'vector') and result.vector is not None:
                    return {
                        "movie_id": result.payload.get("movie_id"),
                        "title": result.payload.get("title"),
                        "genres": result.payload.get("genres", []),
                        "year": result.payload.get("year"),
                        "rating": result.payload.get("rating"),
                        "vector": result.vector
                    }
                else:
                    print(f"Película {movie_id} encontrada pero sin vector")
                    return None
            else:
                print(f"Película {movie_id} no encontrada en Qdrant")
                return None
                
        except Exception as e:
            print(f"Error obteniendo película {movie_id}: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def update_movie_rating(self, movie_id: int, new_rating: float):
        """Actualiza el rating de una película"""
        try:
            self.client.set_payload(
                collection_name=self.collection_name,
                payload={"rating": new_rating},
                points=[movie_id]
            )
            print(f"Rating actualizado para película {movie_id}")
        except Exception as e:
            print(f"Error actualizando rating: {e}")
    
    def get_collection_stats(self) -> Dict:
        """Obtiene estadísticas de la colección"""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "collection_name": self.collection_name,
                "status": info.status,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "distance": info.config.params.vectors.distance if info.config.params.vectors else "unknown",
                "vector_size": info.config.params.vectors.size if info.config.params.vectors else 0
            }
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e)
            }
    
    def save_user_embedding(self, user_id: int, embedding: np.ndarray):
        """
        Guarda o actualiza el embedding de un usuario en la colección de usuarios
        
        Args:
            user_id: ID del usuario
            embedding: Embedding del usuario
        """
        try:
            user_collection = "user_embeddings"
            
            # Verificar si la colección de usuarios existe
            try:
                self.client.get_collection(collection_name=user_collection)
            except:
                # Crear colección si no existe
                self.client.create_collection(
                    collection_name=user_collection,
                    vectors_config=VectorParams(
                        size=len(embedding),
                        distance=Distance.COSINE
                    )
                )
                print(f"Colección '{user_collection}' creada para embeddings de usuarios")
            
            # Crear point para el usuario
            point = PointStruct(
                id=user_id,
                vector=embedding.tolist(),
                payload={
                    "user_id": user_id,
                    "created_at": int(time.time()) if 'time' in globals() else None
                }
            )
            
            # Insertar o actualizar
            self.client.upsert(
                collection_name=user_collection,
                points=[point]
            )
            
            print(f"Embedding guardado para usuario {user_id}")
            
        except Exception as e:
            print(f"Error guardando embedding de usuario {user_id}: {e}")
            raise
    
    def get_user_embedding(self, user_id: int) -> Optional[np.ndarray]:
        """
        Obtiene el embedding de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Embedding del usuario o None si no existe
        """
        try:
            user_collection = "user_embeddings"
            
            # Obtener el point del usuario
            result = self.client.retrieve(
                collection_name=user_collection,
                ids=[user_id],
                with_vectors=True
            )
            
            if result and len(result) > 0 and result[0].vector is not None:
                return np.array(result[0].vector)
            else:
                return None
                
        except Exception as e:
            print(f"Error obteniendo embedding de usuario {user_id}: {e}")
            return None
    
    def find_similar_users(self, user_id: int, k: int = 10) -> List[Dict]:
        """
        Encuentra usuarios similares basado en embeddings
        
        Args:
            user_id: ID del usuario de referencia
            k: Número de usuarios similares a retornar
            
        Returns:
            Lista de usuarios similares con scores
        """
        try:
            user_collection = "user_embeddings"
            
            # Obtener embedding del usuario de referencia
            user_embedding = self.get_user_embedding(user_id)
            if user_embedding is None:
                return []
            
            # Buscar usuarios similares
            results = self.client.search(
                collection_name=user_collection,
                query_vector=user_embedding.tolist(),
                limit=k + 1,  # +1 porque incluirá al propio usuario
                with_payload=True
            )
            
            # Filtrar el propio usuario y formatear resultados
            similar_users = []
            for result in results:
                if result.payload.get("user_id") != user_id:
                    similar_users.append({
                        "user_id": result.payload.get("user_id"),
                        "similarity_score": result.score,
                        "created_at": result.payload.get("created_at")
                    })
            
            return similar_users[:k]
            
        except Exception as e:
            print(f"Error buscando usuarios similares: {e}")
            return []
    
    def delete_collection(self):
        """Elimina la colección"""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Colección '{self.collection_name}' eliminada")
        except Exception as e:
            print(f"Error eliminando colección: {e}")

def load_movie_metadata(movies_file: str) -> List[Dict]:
    """Carga metadata de películas desde archivo"""
    metadata = []
    
    try:
        with open(movies_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('::')
                if len(parts) >= 3:
                    movie_id = int(parts[0])
                    title = parts[1]
                    genres = parts[2].split('|')
                    
                    # Extraer año del título si está disponible
                    year = 0
                    if '(' in title and ')' in title:
                        try:
                            year_str = title.split('(')[-1].split(')')[0]
                            year = int(year_str)
                        except:
                            pass
                    
                    metadata.append({
                        "movie_id": movie_id,
                        "title": title,
                        "genres": genres,
                        "year": year,
                        "rating": 0.0,
                        "num_ratings": 0
                    })
    except FileNotFoundError:
        print(f"Archivo de metadata no encontrado: {movies_file}")
        # Crear metadata básica
        for i in range(1, 3417):  # Para ML-1M
            metadata.append({
                "movie_id": i,
                "title": f"Movie {i}",
                "genres": ["Unknown"],
                "year": 0,
                "rating": 0.0,
                "num_ratings": 0
            })
    
    return metadata

if __name__ == "__main__":
    # Ejemplo de uso
    from embedding_exporter import EmbeddingExporter
    
    # Inicializar servicio Qdrant
    qdrant_service = QdrantService()
    
    # Crear colección
    qdrant_service.create_collection()
    
    # Exportar embeddings
    exporter = EmbeddingExporter("../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt")
    data = exporter.export_embeddings()
    
    # Cargar metadata (si está disponible)
    metadata = load_movie_metadata("../modelo/datasets/ml1m/ml-1m.txt")
    
    # Insertar películas
    qdrant_service.insert_movies(data["item_embeddings"], metadata)
    
    print("Servicio Qdrant configurado exitosamente") 