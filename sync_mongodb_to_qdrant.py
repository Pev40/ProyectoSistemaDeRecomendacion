#!/usr/bin/env python3
"""
Script para sincronizar metadatos de MongoDB a Qdrant
Actualiza los puntos existentes en Qdrant con metadatos completos de MongoDB
"""

from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import json
from typing import Dict, Any, List

def sync_mongodb_to_qdrant():
    """
    Sincroniza metadatos de MongoDB a las colecciones de Qdrant
    """
    try:
        print("🔄 SINCRONIZANDO METADATOS DE MONGODB A QDRANT")
        print("=" * 60)
        
        # Conectar a MongoDB
        print("🔍 Conectando a MongoDB...")
        mongo_client = MongoClient("mongodb://localhost:27017/")
        
        # Conectar a Qdrant
        print("🔍 Conectando a Qdrant...")
        qdrant_client = QdrantClient(host="localhost", port=6333)
        
        # Detectar base de datos de MongoDB
        db_name = detect_mongodb_database(mongo_client)
        if not db_name:
            print("❌ No se encontró base de datos con datos de películas")
            return False
        
        print(f"✅ Usando base de datos: {db_name}")
        db = mongo_client[db_name]
        
        # Sincronizar movie_embeddings
        success_movies = sync_movie_embeddings(db, qdrant_client)
        
        # Sincronizar user_embeddings
        success_users = sync_user_embeddings(db, qdrant_client)
        
        print(f"\n" + "=" * 60)
        if success_movies and success_users:
            print("✅ SINCRONIZACIÓN COMPLETADA EXITOSAMENTE")
            print("💡 Ahora los metadatos deberían aparecer correctamente en Qdrant")
        else:
            print("⚠️  SINCRONIZACIÓN PARCIAL - Revisar errores arriba")
        
        return success_movies and success_users
        
    except Exception as e:
        print(f"❌ Error en sincronización: {e}")
        return False

def detect_mongodb_database(mongo_client: MongoClient) -> str:
    """
    Detecta automáticamente la base de datos correcta
    """
    # Posibles nombres de base de datos
    possible_names = ["movie_recommendations", "movielens_32m", "movielens"]
    
    for db_name in possible_names:
        try:
            db = mongo_client[db_name]
            collections = db.list_collection_names()
            
            # Verificar si tiene las colecciones esperadas
            if any(col in collections for col in ["movies", "ratings", "users"]):
                movies_count = db.movies.count_documents({}) if "movies" in collections else 0
                if movies_count > 0:
                    print(f"   📁 Encontrada BD '{db_name}' con {movies_count} películas")
                    return db_name
        except:
            continue
    
    return None

def sync_movie_embeddings(db, qdrant_client: QdrantClient) -> bool:
    """
    Sincroniza metadatos de películas de MongoDB a Qdrant
    """
    try:
        print(f"\n🎬 SINCRONIZANDO PELÍCULAS...")
        print("-" * 40)
        
        # Obtener información de la colección en Qdrant
        collection_info = qdrant_client.get_collection("movie_embeddings")
        points_count = collection_info.points_count
        print(f"   📊 Puntos en Qdrant: {points_count:,}")
        
        if points_count == 0:
            print("   ⚠️  No hay puntos para actualizar")
            return True
        
        # Obtener películas de MongoDB
        movies_collection = db.movies
        movies_count = movies_collection.count_documents({})
        print(f"   📊 Películas en MongoDB: {movies_count:,}")
        
        if movies_count == 0:
            print("   ❌ No hay películas en MongoDB")
            return False
        
        # Crear mapa de metadatos por movie_id
        print("   📋 Cargando metadatos de MongoDB...")
        movie_metadata = {}
        
        for movie in movies_collection.find():
            movie_id = movie.get("movieId") or movie.get("movie_id") or movie.get("id")
            if movie_id:
                movie_metadata[movie_id] = {
                    "title": movie.get("title", "Sin título"),
                    "genres": movie.get("genres", []),
                    "year": movie.get("year", 0),
                    "rating": movie.get("rating", 0.0),
                    "imdb_id": movie.get("imdbId", ""),
                    "tmdb_id": movie.get("tmdbId", "")
                }
        
        print(f"   ✅ Cargados metadatos de {len(movie_metadata)} películas")
        
        # Obtener puntos existentes de Qdrant
        print("   🔍 Obteniendo puntos de Qdrant...")
        points_to_update = []
        offset = None
        
        while True:
            # Obtener lote de puntos
            result = qdrant_client.scroll(
                collection_name="movie_embeddings",
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            # Actualizar cada punto con metadatos
            for point in points:
                movie_id = point.payload.get("movie_id")
                if movie_id and movie_id in movie_metadata:
                    # Combinar payload existente con nuevos metadatos
                    updated_payload = {**point.payload, **movie_metadata[movie_id]}
                    
                    # Crear punto actualizado
                    updated_point = PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=updated_payload
                    )
                    points_to_update.append(updated_point)
            
            offset = next_offset
            if offset is None:
                break
        
        # Actualizar puntos en Qdrant
        if points_to_update:
            print(f"   🔄 Actualizando {len(points_to_update)} puntos...")
            
            # Actualizar en lotes
            batch_size = 100
            for i in range(0, len(points_to_update), batch_size):
                batch = points_to_update[i:i + batch_size]
                qdrant_client.upsert(
                    collection_name="movie_embeddings",
                    points=batch
                )
                print(f"   ✅ Actualizado lote {i//batch_size + 1}/{(len(points_to_update)-1)//batch_size + 1}")
            
            print(f"   🎉 ¡{len(points_to_update)} películas actualizadas exitosamente!")
        else:
            print("   ⚠️  No se encontraron puntos para actualizar")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error sincronizando películas: {e}")
        return False

def sync_user_embeddings(db, qdrant_client: QdrantClient) -> bool:
    """
    Sincroniza metadatos de usuarios de MongoDB a Qdrant
    """
    try:
        print(f"\n👥 SINCRONIZANDO USUARIOS...")
        print("-" * 40)
        
        # Obtener información de la colección en Qdrant
        collection_info = qdrant_client.get_collection("user_embeddings")
        points_count = collection_info.points_count
        print(f"   📊 Puntos en Qdrant: {points_count:,}")
        
        if points_count == 0:
            print("   ⚠️  No hay puntos para actualizar")
            return True
        
        # Calcular estadísticas de usuarios desde ratings
        print("   📋 Calculando estadísticas de usuarios...")
        user_stats = {}
        
        # Pipeline de agregación para estadísticas de usuarios
        pipeline = [
            {
                "$group": {
                    "_id": "$userId",
                    "movie_count": {"$sum": 1},
                    "avg_rating": {"$avg": "$rating"},
                    "min_rating": {"$min": "$rating"},
                    "max_rating": {"$max": "$rating"},
                    "total_rating": {"$sum": "$rating"}
                }
            }
        ]
        
        ratings_collection = db.ratings
        for user_stat in ratings_collection.aggregate(pipeline):
            user_id = user_stat["_id"]
            user_stats[user_id] = {
                "movie_count": user_stat["movie_count"],
                "avg_rating": round(user_stat["avg_rating"], 3),
                "min_rating": user_stat["min_rating"],
                "max_rating": user_stat["max_rating"],
                "total_rating": user_stat["total_rating"]
            }
        
        print(f"   ✅ Calculadas estadísticas de {len(user_stats)} usuarios")
        
        # Actualizar puntos de usuarios en Qdrant
        print("   🔍 Obteniendo puntos de usuarios de Qdrant...")
        points_to_update = []
        offset = None
        
        while True:
            result = qdrant_client.scroll(
                collection_name="user_embeddings",
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            # Actualizar cada punto con estadísticas
            for point in points:
                user_id = point.payload.get("user_id")
                if user_id and user_id in user_stats:
                    # Combinar payload existente con nuevas estadísticas
                    updated_payload = {**point.payload, **user_stats[user_id]}
                    
                    updated_point = PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=updated_payload
                    )
                    points_to_update.append(updated_point)
            
            offset = next_offset
            if offset is None:
                break
        
        # Actualizar puntos en Qdrant
        if points_to_update:
            print(f"   🔄 Actualizando {len(points_to_update)} puntos de usuarios...")
            
            batch_size = 100
            for i in range(0, len(points_to_update), batch_size):
                batch = points_to_update[i:i + batch_size]
                qdrant_client.upsert(
                    collection_name="user_embeddings",
                    points=batch
                )
                print(f"   ✅ Actualizado lote {i//batch_size + 1}/{(len(points_to_update)-1)//batch_size + 1}")
            
            print(f"   🎉 ¡{len(points_to_update)} usuarios actualizados exitosamente!")
        else:
            print("   ⚠️  No se encontraron puntos de usuarios para actualizar")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error sincronizando usuarios: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SINCRONIZADOR MONGODB → QDRANT")
    print("=" * 60)
    print("Este script actualiza los metadatos en Qdrant con datos de MongoDB")
    print()
    
    success = sync_mongodb_to_qdrant()
    
    if success:
        print(f"\n🎯 PRÓXIMOS PASOS:")
        print(f"   1. Ejecuta: python access_qdrant_data.py")
        print(f"   2. Verifica que los títulos aparezcan correctamente")
        print(f"   3. Prueba la API nuevamente")
    else:
        print(f"\n💡 Si hay errores:")
        print(f"   1. Verifica que MongoDB esté corriendo")
        print(f"   2. Verifica que Qdrant esté corriendo") 
        print(f"   3. Ejecuta: python check_mongodb_data.py") 