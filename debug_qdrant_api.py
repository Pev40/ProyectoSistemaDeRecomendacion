#!/usr/bin/env python3
"""
Script para diagnosticar el problema de conexión Qdrant-API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from qdrant_client import QdrantClient
from qdrant_service import QdrantService
import asyncio

def test_direct_qdrant():
    """Prueba conexión directa a Qdrant"""
    print("🔍 PRUEBA DIRECTA DE QDRANT")
    print("=" * 50)
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # Listar colecciones
        collections = client.get_collections()
        print(f"✅ Colecciones disponibles:")
        for col in collections.collections:
            try:
                info = client.get_collection(col.name)
                points_count = getattr(info, 'points_count', 0) or 0
                vectors_count = getattr(info, 'vectors_count', 0) or 0
                print(f"   📂 {col.name}: {points_count:,} puntos, {vectors_count:,} vectores")
            except Exception as e:
                print(f"   📂 {col.name}: Error obteniendo info - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en conexión directa: {e}")
        return False

def test_qdrant_service():
    """Prueba el servicio QdrantService como lo usa la API"""
    print(f"\n🔧 PRUEBA SERVICIO QDRANTSERVICE")
    print("=" * 50)
    
    try:
        # Test con collection por defecto
        print("📋 Test con colección por defecto ('movies'):")
        service_default = QdrantService()
        stats_default = service_default.get_collection_stats()
        print(f"   📊 Estadísticas: {stats_default}")
        
        # Test con movie_embeddings (como en la API)
        print("\n📋 Test con 'movie_embeddings' (como en la API):")
        service_movies = QdrantService(
            host="localhost", 
            port=6333, 
            collection_name="movie_embeddings"
        )
        stats_movies = service_movies.get_collection_stats()
        print(f"   📊 Estadísticas: {stats_movies}")
        
        # Test con user_embeddings
        print("\n📋 Test con 'user_embeddings':")
        service_users = QdrantService(
            host="localhost", 
            port=6333, 
            collection_name="user_embeddings"
        )
        stats_users = service_users.get_collection_stats()
        print(f"   📊 Estadísticas: {stats_users}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en servicio: {e}")
        return False

async def test_api_simulation():
    """Simula exactamente lo que hace la API"""
    print(f"\n🎭 SIMULACIÓN DE LA API")
    print("=" * 50)
    
    try:
        from database import DatabaseManager, MovieLensDatabase
        
        # Inicializar como en la API
        print("📊 Conectando a bases de datos...")
        db_manager = DatabaseManager()
        await db_manager.connect()
        movie_db = MovieLensDatabase(db_manager)
        
        print("🔍 Conectando a Qdrant...")
        qdrant_service = QdrantService(
            host="localhost", 
            port=6333, 
            collection_name="movie_embeddings"
        )
        
        # Verificar estado como en la API
        print("📈 Obteniendo estadísticas...")
        stats = qdrant_service.get_collection_stats()
        print(f"   📊 Estadísticas Qdrant: {stats}")
        
        # Estadísticas MongoDB como en la API
        db = db_manager.sync_mongo_client.movie_recommendations
        mongodb_stats = {
            "movies": db.movies.estimated_document_count(),
            "ratings": db.ratings.estimated_document_count(),
            "users": len(db.ratings.distinct("userId"))
        }
        print(f"   📊 Estadísticas MongoDB: {mongodb_stats}")
        
        # Estadísticas Redis
        redis_info = await db_manager.redis_client.info()
        redis_stats = {
            "connected_clients": redis_info.get("connected_clients", 0),
            "used_memory": redis_info.get("used_memory_human", "0B"),
            "keyspace_hits": redis_info.get("keyspace_hits", 0)
        }
        print(f"   📊 Estadísticas Redis: {redis_stats}")
        
        await db_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Error en simulación de API: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 DIAGNÓSTICO QDRANT-API")
    print("=" * 60)
    print("Investigando por qué la API reporta 0 puntos en Qdrant")
    print()
    
    # Test 1: Conexión directa
    success1 = test_direct_qdrant()
    
    # Test 2: Servicio QdrantService
    success2 = test_qdrant_service()
    
    # Test 3: Simulación completa de la API
    success3 = asyncio.run(test_api_simulation())
    
    print(f"\n" + "=" * 60)
    print("📋 RESUMEN DE DIAGNÓSTICO:")
    print(f"   • Conexión directa: {'✅ OK' if success1 else '❌ FALLO'}")
    print(f"   • Servicio QdrantService: {'✅ OK' if success2 else '❌ FALLO'}")
    print(f"   • Simulación API: {'✅ OK' if success3 else '❌ FALLO'}")
    
    if success1 and success2 and success3:
        print("\n🎉 TODO FUNCIONA - El problema puede estar en la API actual")
        print("💡 Sugerencia: Reinicia la API y vuelve a probar")
    elif not success1:
        print("\n❌ PROBLEMA DE CONEXIÓN A QDRANT")
        print("💡 Asegúrate de que Qdrant esté ejecutándose en localhost:6333")
    else:
        print("\n⚠️  PROBLEMA EN CONFIGURACIÓN")
        print("💡 Revisa los logs de la API para más detalles")

if __name__ == "__main__":
    main() 