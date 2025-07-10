# Script para verificar datos disponibles en la base de datos
import asyncio
from database import DatabaseManager, MovieLensDatabase
from qdrant_service import QdrantService
import json

async def check_database():
    """Verifica qué datos están disponibles"""
    print("🔍 VERIFICANDO DATOS DISPONIBLES")
    print("="*50)
    
    # Conectar a la base de datos
    db_manager = DatabaseManager()
    await db_manager.connect()
    movie_db = MovieLensDatabase(db_manager)
    
    try:
        # Verificar MongoDB
        print("\n📊 ESTADÍSTICAS MONGODB:")
        
        # Contar documentos
        movies_count = await movie_db.db.movies.count_documents({})
        ratings_count = await movie_db.db.ratings.count_documents({})
        
        print(f"   Películas: {movies_count:,}")
        print(f"   Ratings: {ratings_count:,}")
        
        if ratings_count > 0:
            # Obtener algunos usuarios de ejemplo
            users_sample = await movie_db.db.ratings.distinct("userId")
            print(f"   Usuarios únicos: {len(users_sample):,}")
            print(f"   Primeros 10 usuarios: {users_sample[:10]}")
            
            # Verificar un usuario específico
            if users_sample:
                user_id = users_sample[0]
                user_sequence = await movie_db.get_user_sequence(user_id)
                print(f"   Usuario {user_id} tiene {len(user_sequence)} ratings")
                
        if movies_count > 0:
            # Muestra de películas
            movies_sample = await movie_db.db.movies.find({}).limit(5).to_list(5)
            print(f"   Ejemplo de películas:")
            for movie in movies_sample:
                print(f"      ID {movie.get('movieId')}: {movie.get('title', 'Sin título')}")
        
        # Verificar Qdrant
        print("\n🔍 ESTADÍSTICAS QDRANT:")
        qdrant_service = QdrantService(collection_name="movie_embeddings")
        
        try:
            stats = qdrant_service.get_collection_stats()
            print(f"   Colección: {stats.get('name', 'N/A')}")
            print(f"   Vectores: {stats.get('vectors_count', 0):,}")
            print(f"   Puntos: {stats.get('points_count', 0):,}")
            
            # Verificar que hay embeddings
            if stats.get('points_count', 0) > 0:
                print(f"   ✅ Embeddings disponibles para búsqueda")
                
                # Probar obtener una película específica
                test_movie = qdrant_service.get_movie_by_id(1)
                if test_movie:
                    print(f"   ✅ Película 1 encontrada en Qdrant")
                    print(f"      Vector shape: {len(test_movie.get('vector', []))}")
                else:
                    print(f"   ⚠️ Película 1 NO encontrada en Qdrant")
            else:
                print(f"   ❌ No hay embeddings en Qdrant")
                
        except Exception as e:
            print(f"   ❌ Error conectando a Qdrant: {e}")
        
        # Verificar Redis
        print("\n📦 VERIFICANDO REDIS:")
        try:
            await db_manager.redis_client.ping()
            print(f"   ✅ Redis conectado")
            
            # Verificar cache
            cache_keys = await db_manager.redis_client.keys("*")
            print(f"   Claves en cache: {len(cache_keys)}")
            
        except Exception as e:
            print(f"   ❌ Error con Redis: {e}")
        
        # Recomendaciones
        print("\n🎯 PRUEBA DE RECOMENDACIONES:")
        if users_sample and len(users_sample) > 0:
            test_user = users_sample[0]
            sequence = await movie_db.get_user_sequence(test_user)
            
            if sequence:
                print(f"   Usuario {test_user}:")
                print(f"      Secuencia: {len(sequence)} películas")
                print(f"      Últimas 5: {sequence[-5:]}")
                
                # Verificar si hay metadata para las películas
                for movie_id in sequence[-3:]:
                    metadata = await movie_db.get_movie_metadata(movie_id)
                    if metadata:
                        print(f"      Película {movie_id}: {metadata.get('title', 'Sin título')}")
                    else:
                        print(f"      Película {movie_id}: Sin metadata")
            else:
                print(f"   ⚠️ Usuario {test_user} sin secuencia")
        
        print("\n✅ VERIFICACIÓN COMPLETADA")
        
    except Exception as e:
        print(f"❌ Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(check_database()) 