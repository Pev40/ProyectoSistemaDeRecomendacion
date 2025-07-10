#!/usr/bin/env python3
"""
Script para limpiar el cache corrupto de metadata de películas en Redis
"""

import asyncio
import redis.asyncio as redis
from structlog import get_logger

logger = get_logger()

async def clear_movie_cache():
    """Limpia el cache de metadata de películas"""
    try:
        # Conectar a Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Buscar todas las keys de movie_metadata
        pattern = "movie_metadata:*"
        keys = await redis_client.keys(pattern)
        
        if keys:
            print(f"🗑️  Encontradas {len(keys)} keys de cache de películas")
            
            # Eliminar keys en lotes
            for i in range(0, len(keys), 100):
                batch = keys[i:i+100]
                deleted = await redis_client.delete(*batch)
                print(f"   Eliminadas {deleted} keys (lote {i//100 + 1})")
            
            print("✅ Cache de metadata de películas limpiado exitosamente")
        else:
            print("ℹ️  No se encontraron keys de cache de películas")
        
        await redis_client.aclose()
        
    except Exception as e:
        print(f"❌ Error limpiando cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_movie_cache()) 