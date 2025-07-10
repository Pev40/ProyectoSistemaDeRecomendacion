#!/usr/bin/env python3
"""
Script rápido para probar el arreglo de búsqueda de películas
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
from database import DatabaseManager, MovieLensDatabase

async def test_search_fix():
    """Prueba rápida del arreglo de búsqueda"""
    print("🧪 PRUEBA RÁPIDA DEL ARREGLO DE BÚSQUEDA")
    print("=" * 50)
    
    try:
        # Conectar
        print("📊 Conectando...")
        db_manager = DatabaseManager()
        await db_manager.connect()
        movie_db = MovieLensDatabase(db_manager)
        
        # Probar búsquedas
        queries = ["matrix", "toy story", "star wars", "batman"]
        
        for query in queries:
            print(f"\n🔍 Buscando: '{query}'")
            try:
                results = await movie_db.search_movies(query, 3)
                print(f"   ✅ {len(results)} resultados encontrados")
                for movie in results[:2]:
                    title = movie.get('title', 'Sin título')
                    movie_id = movie.get('movieId', 'N/A')
                    print(f"      • {title} (ID: {movie_id})")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        await db_manager.disconnect()
        print(f"\n✅ Prueba completada - El arreglo funciona!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_fix()) 