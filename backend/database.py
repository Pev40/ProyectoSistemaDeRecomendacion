import os
import asyncio
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from pymongo import MongoClient
import structlog

logger = structlog.get_logger()

class DatabaseManager:
    """Gestor de conexiones a MongoDB y Redis"""
    
    def __init__(self):
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.sync_mongo_client: Optional[MongoClient] = None
        
    async def connect(self):
        """Conecta a MongoDB y Redis"""
        try:
            # MongoDB
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            self.mongo_client = AsyncIOMotorClient(mongo_uri)
            self.sync_mongo_client = MongoClient(mongo_uri)
            
            # Redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            
            # Verificar conexiones
            await self.mongo_client.admin.command('ping')
            await self.redis_client.ping()
            
            logger.info("Conexiones a base de datos establecidas")
            
        except Exception as e:
            logger.error(f"Error conectando a bases de datos: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta de las bases de datos"""
        if self.mongo_client:
            self.mongo_client.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.sync_mongo_client:
            self.sync_mongo_client.close()
        
        logger.info("Conexiones a base de datos cerradas")

class MovieLensDatabase:
    """Gestor específico para datos de MovieLens 32M"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db = self.db_manager.mongo_client.movie_recommendations
        self.sync_db = self.db_manager.sync_mongo_client.movie_recommendations
        
    async def get_user_sequence(self, user_id: int) -> List[int]:
        """Obtiene la secuencia de películas de un usuario"""
        try:
            # Buscar en cache primero
            cache_key = f"user_sequence:{user_id}"
            cached = await self.db_manager.redis_client.get(cache_key)
            
            if cached:
                import json
                return json.loads(cached)
            
            # Buscar en MongoDB
            user_data = await self.db.ratings.find_one(
                {"userId": user_id},
                sort=[("timestamp", 1)]
            )
            
            if not user_data:
                return []
            
            # Obtener todas las calificaciones del usuario ordenadas por timestamp
            cursor = self.db.ratings.find(
                {"userId": user_id}
            ).sort("timestamp", 1)
            
            sequence = []
            async for doc in cursor:
                sequence.append(doc["movieId"])
            
            # Cachear resultado
            await self.db_manager.redis_client.setex(
                cache_key, 3600, str(sequence)  # Cache por 1 hora
            )
            
            return sequence
            
        except Exception as e:
            logger.error(f"Error obteniendo secuencia de usuario {user_id}: {e}")
            return []
    
    async def get_movie_metadata(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene metadata de una película"""
        try:
            # Buscar en cache
            cache_key = f"movie_metadata:{movie_id}"
            cached = await self.db_manager.redis_client.get(cache_key)
            
            if cached:
                import json
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    # Cache corrupto, eliminar y continuar con MongoDB
                    logger.warning(f"Cache corrupto para película {movie_id}, eliminando...")
                    await self.db_manager.redis_client.delete(cache_key)
            
            # Buscar en MongoDB (excluir _id para evitar problemas de serialización)
            movie = await self.db.movies.find_one(
                {"movieId": movie_id},
                {"_id": 0}  # Excluir _id
            )
            
            if movie:
                # Limpiar y estructurar el resultado
                clean_movie = {
                    "movieId": movie.get("movieId"),
                    "title": movie.get("title"),
                    "genres": movie.get("genres"),
                    "year": movie.get("year")
                }
                
                # Cachear resultado como JSON válido
                import json
                await self.db_manager.redis_client.setex(
                    cache_key, 7200, json.dumps(clean_movie)  # Cache por 2 horas
                )
                return clean_movie
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo metadata de película {movie_id}: {e}")
            return None
    
    async def update_user_rating(self, user_id: int, movie_id: int, rating: float, timestamp: Optional[int] = None):
        """Actualiza o agrega una calificación de usuario"""
        try:
            if timestamp is None:
                import time
                timestamp = int(time.time())
            
            # Actualizar en MongoDB
            await self.db.ratings.update_one(
                {"userId": user_id, "movieId": movie_id},
                {
                    "$set": {
                        "rating": rating,
                        "timestamp": timestamp
                    }
                },
                upsert=True
            )
            
            # Invalidar cache
            cache_key = f"user_sequence:{user_id}"
            await self.db_manager.redis_client.delete(cache_key)
            
            logger.info(f"Calificación actualizada: usuario {user_id}, película {movie_id}, rating {rating}")
            
        except Exception as e:
            logger.error(f"Error actualizando calificación: {e}")
            raise
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de un usuario"""
        try:
            pipeline = [
                {"$match": {"userId": user_id}},
                {"$group": {
                    "_id": None,
                    "total_ratings": {"$sum": 1},
                    "avg_rating": {"$avg": "$rating"},
                    "min_rating": {"$min": "$rating"},
                    "max_rating": {"$max": "$rating"}
                }}
            ]
            
            result = await self.db.ratings.aggregate(pipeline).to_list(1)
            
            if result:
                # Limpiar resultado removiendo _id y redondeando valores
                stats = result[0]
                return {
                    "total_ratings": stats["total_ratings"],
                    "avg_rating": round(stats["avg_rating"], 2),
                    "min_rating": stats["min_rating"],
                    "max_rating": stats["max_rating"]
                }
            else:
                return {
                    "total_ratings": 0,
                    "avg_rating": 0,
                    "min_rating": 0,
                    "max_rating": 0
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de usuario {user_id}: {e}")
            return {}
    
    async def get_popular_movies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene las películas más populares"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$movieId",
                    "total_ratings": {"$sum": 1},
                    "avg_rating": {"$avg": "$rating"}
                }},
                {"$sort": {"total_ratings": -1}},
                {"$limit": limit}
            ]
            
            results = await self.db.ratings.aggregate(pipeline).to_list(limit)
            
            # Agregar metadata de películas y limpiar resultados
            movies_with_metadata = []
            for result in results:
                movie_id = result["_id"]
                metadata = await self.get_movie_metadata(movie_id)
                if metadata:
                    # Crear un resultado limpio sin ObjectId
                    clean_result = {
                        "movieId": movie_id,
                        "total_ratings": result["total_ratings"],
                        "avg_rating": round(result["avg_rating"], 2),
                        "title": metadata.get("title"),
                        "genres": metadata.get("genres"),
                        "year": metadata.get("year")
                    }
                    movies_with_metadata.append(clean_result)
            
            return movies_with_metadata
            
        except Exception as e:
            logger.error(f"Error obteniendo películas populares: {e}")
            return []
    
    async def search_movies(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca películas por título"""
        try:
            # Crear índice de texto usando cliente sincrónico
            try:
                self.sync_db.movies.create_index([("title", "text")], background=True)
            except Exception as index_error:
                # Índice ya existe, continuar
                logger.debug(f"Índice ya existe o error menor: {index_error}")
            
            # Intentar búsqueda con índice de texto
            try:
                cursor = self.db.movies.find(
                    {"$text": {"$search": query}},
                    {"score": {"$meta": "textScore"}, "_id": 0}  # Excluir _id
                ).sort([("score", {"$meta": "textScore"})]).limit(limit)
                
                results = await cursor.to_list(limit)
                
                if results:
                    # Convertir resultados para asegurar serialización JSON
                    clean_results = []
                    for doc in results:
                        clean_doc = {
                            "movieId": doc.get("movieId"),
                            "title": doc.get("title"),
                            "genres": doc.get("genres"),
                            "year": doc.get("year"),
                            "score": doc.get("score", 1.0)
                        }
                        clean_results.append(clean_doc)
                    return clean_results
                    
            except Exception as text_error:
                logger.warning(f"Búsqueda de texto falló: {text_error}")
            
            # Fallback: búsqueda con regex (más lenta pero más compatible)
            logger.info(f"Usando búsqueda regex como fallback para: {query}")
            cursor = self.db.movies.find(
                {"title": {"$regex": query, "$options": "i"}},
                {"title": 1, "movieId": 1, "genres": 1, "year": 1, "_id": 0}  # Excluir _id
            ).limit(limit)
            
            results = await cursor.to_list(limit)
            
            # Convertir resultados para asegurar serialización JSON
            clean_results = []
            for doc in results:
                clean_doc = {
                    "movieId": doc.get("movieId"),
                    "title": doc.get("title"),
                    "genres": doc.get("genres"),
                    "year": doc.get("year")
                }
                clean_results.append(clean_doc)
            
            return clean_results
            
        except Exception as e:
            logger.error(f"Error buscando películas: {e}")
            return []

# Instancia global
db_manager = DatabaseManager()
movielens_db = None

async def init_database():
    """Inicializa las conexiones de base de datos"""
    global movielens_db
    await db_manager.connect()
    movielens_db = MovieLensDatabase(db_manager)
    logger.info("Base de datos inicializada")

async def close_database():
    """Cierra las conexiones de base de datos"""
    await db_manager.disconnect()
    logger.info("Base de datos cerrada") 