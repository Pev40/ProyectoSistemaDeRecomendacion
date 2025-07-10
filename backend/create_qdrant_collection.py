#!/usr/bin/env python3
"""
Script para crear la colección de películas en Qdrant
"""

import asyncio
import sys
from pathlib import Path
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

# Configurar logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_movies_collection():
    """Crear colección de películas en Qdrant"""
    print("Creando colección de películas en Qdrant...")
    
    try:
        # Conectar a Qdrant
        client = QdrantClient(host="localhost", port=6333)
        
        # Verificar si la colección ya existe
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if "movies" in collection_names:
            print("OK: Colección 'movies' ya existe")
            collection_info = client.get_collection("movies")
            print(f"   - Puntos: {collection_info.points_count}")
            print(f"   - Vectores: {collection_info.vectors_count}")
            return True
        
        # Crear colección
        print("Creando colección 'movies'...")
        client.create_collection(
            collection_name="movies",
            vectors_config=VectorParams(
                size=128,  # Dimensiones del embedding
                distance=Distance.COSINE
            )
        )
        
        print("OK: Colección 'movies' creada exitosamente")
        
        # Crear algunos puntos de ejemplo
        print("Creando puntos de ejemplo...")
        
        # Crear embeddings de ejemplo (normalmente vendrían del modelo)
        num_movies = 100
        embeddings = np.random.random((num_movies, 128)).astype('float32')
        
        # Normalizar embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        # Crear puntos
        points = []
        for i in range(num_movies):
            point = PointStruct(
                id=i + 1,
                vector=embeddings[i].tolist(),
                payload={
                    "movieId": i + 1,
                    "title": f"Movie {i + 1}",
                    "genres": ["Action", "Adventure"],
                    "year": 2020
                }
            )
            points.append(point)
        
        # Insertar puntos
        client.upsert(
            collection_name="movies",
            points=points
        )
        
        print(f"OK: {len(points)} puntos insertados")
        
        # Verificar colección
        collection_info = client.get_collection("movies")
        print(f"Colección creada:")
        print(f"   - Puntos: {collection_info.points_count}")
        print(f"   - Vectores: {collection_info.vectors_count}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Error creando colección: {e}")
        return False

def test_collection():
    """Probar la colección creada"""
    print("\nProbando colección...")
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # Buscar puntos similares
        query_vector = np.random.random(128).astype('float32')
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        results = client.search(
            collection_name="movies",
            query_vector=query_vector.tolist(),
            limit=5
        )
        
        print("OK: Búsqueda exitosa")
        print(f"   - Resultados encontrados: {len(results)}")
        
        for i, result in enumerate(results[:3]):
            print(f"   {i+1}. Movie {result.payload.get('movieId')} - Score: {result.score:.3f}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Error probando colección: {e}")
        return False

def main():
    """Función principal"""
    print("Inicializador de Qdrant")
    print("=" * 40)
    
    # Crear colección
    success = create_movies_collection()
    
    if success:
        # Probar colección
        test_collection()
        print("\nOK: Qdrant inicializado correctamente")
    else:
        print("\nERROR: Error inicializando Qdrant")

if __name__ == "__main__":
    main() 