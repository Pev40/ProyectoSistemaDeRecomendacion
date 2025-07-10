#!/usr/bin/env python3
"""
Script para diagnosticar el problema de búsqueda de películas
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from database import DatabaseManager, MovieLensDatabase

async def test_search_movies():
    """Prueba la búsqueda de películas directamente"""
    print("🔍 DIAGNÓSTICO DE BÚSQUEDA DE PELÍCULAS")
    print("=" * 60)
    
    try:
        # Conectar a base de datos
        print("📊 Conectando a MongoDB...")
        db_manager = DatabaseManager()
        await db_manager.connect()
        movie_db = MovieLensDatabase(db_manager)
        
        # Probar búsqueda directa en MongoDB
        print("\n📋 Prueba 1: Búsqueda directa en MongoDB")
        db = db_manager.mongo_client.movie_recommendations
        
        # Verificar que existe la colección movies
        collections = db.list_collection_names()
        print(f"   📂 Colecciones disponibles: {collections}")
        
        if "movies" in collections:
            movies_count = db.movies.count_documents({})
            print(f"   📊 Total de películas: {movies_count:,}")
            
            # Mostrar algunos títulos de ejemplo
            print(f"   📝 Ejemplos de títulos:")
            sample_movies = list(db.movies.find({}, {"title": 1, "movieId": 1}).limit(5))
            for movie in sample_movies:
                print(f"      • {movie.get('movieId')}: {movie.get('title', 'Sin título')}")
        
        # Probar búsqueda sin índice de texto
        print(f"\n📋 Prueba 2: Búsqueda simple (sin índice de texto)")
        try:
            # Búsqueda con regex (no requiere índice)
            query = "matrix"
            regex_results = list(db.movies.find(
                {"title": {"$regex": query, "$options": "i"}},
                {"title": 1, "movieId": 1, "genres": 1}
            ).limit(5))
            
            print(f"   ✅ Búsqueda regex exitosa: {len(regex_results)} resultados")
            for movie in regex_results:
                print(f"      • {movie.get('title')} ({movie.get('movieId')})")
        
        except Exception as e:
            print(f"   ❌ Error en búsqueda regex: {e}")
        
        # Probar crear índice de texto
        print(f"\n📋 Prueba 3: Crear índice de texto")
        try:
            # Verificar índices existentes
            indexes = list(db.movies.list_indexes())
            print(f"   📑 Índices existentes: {[idx['name'] for idx in indexes]}")
            
            # Crear índice de texto
            db.movies.create_index([("title", "text")], background=True)
            print(f"   ✅ Índice de texto creado exitosamente")
            
        except Exception as e:
            print(f"   ⚠️  Error/advertencia creando índice: {e}")
        
        # Probar búsqueda con índice de texto
        print(f"\n📋 Prueba 4: Búsqueda con índice de texto")
        try:
            text_results = list(db.movies.find(
                {"$text": {"$search": "matrix"}},
                {"score": {"$meta": "textScore"}, "title": 1, "movieId": 1, "genres": 1}
            ).sort([("score", {"$meta": "textScore"})]).limit(5))
            
            print(f"   ✅ Búsqueda con texto exitosa: {len(text_results)} resultados")
            for movie in text_results:
                score = movie.get('score', 0)
                print(f"      • {movie.get('title')} (Score: {score:.3f})")
        
        except Exception as e:
            print(f"   ❌ Error en búsqueda con texto: {e}")
        
        # Probar la función search_movies del MovieLensDatabase
        print(f"\n📋 Prueba 5: Función search_movies de la API")
        try:
            api_results = await movie_db.search_movies("matrix", 5)
            print(f"   ✅ API search_movies exitosa: {len(api_results)} resultados")
            for movie in api_results:
                print(f"      • {movie.get('title')} (ID: {movie.get('movieId', 'N/A')})")
        
        except Exception as e:
            print(f"   ❌ Error en API search_movies: {e}")
            import traceback
            traceback.print_exc()
        
        await db_manager.disconnect()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_search_movies()

if __name__ == "__main__":
    asyncio.run(main()) 