#!/usr/bin/env python3
"""
Script simple para acceder a los datos almacenados en Qdrant
"""

from qdrant_client import QdrantClient
import json

def access_qdrant_data():
    """
    Accede y muestra datos de las colecciones de Qdrant
    """
    try:
        # Conectar a Qdrant
        print("🔍 Conectando a Qdrant...")
        client = QdrantClient(host="localhost", port=6333)
        
        # Verificar colecciones con datos
        collections_with_data = []
        
        print("\n📊 VERIFICANDO DATOS EN QDRANT")
        print("=" * 50)
        
        for collection_name in ["movie_embeddings", "user_embeddings", "sequence_embeddings"]:
            try:
                info = client.get_collection(collection_name)
                points_count = info.points_count
                
                print(f"\n🗂️  {collection_name}:")
                print(f"   📈 Puntos: {points_count:,}")
                
                if points_count > 0:
                    collections_with_data.append(collection_name)
                    print(f"   ✅ Estado: CONTIENE DATOS")
                    
                    # Obtener una muestra de datos
                    sample = client.scroll(
                        collection_name=collection_name,
                        limit=2,
                        with_payload=True,
                        with_vectors=True
                    )[0]
                    
                    if sample:
                        print(f"   📋 Muestra de datos:")
                        for i, point in enumerate(sample, 1):
                            print(f"      {i}. ID: {point.id}")
                            if point.payload:
                                # Mostrar payload de forma más legible
                                payload_preview = {}
                                for key, value in list(point.payload.items())[:3]:
                                    payload_preview[key] = value
                                print(f"         Metadatos: {payload_preview}")
                            
                            # Mostrar info del vector
                            if hasattr(point, 'vector') and point.vector:
                                if hasattr(point.vector, '__len__'):
                                    vector_dim = len(point.vector)
                                else:
                                    vector_dim = "N/A"
                                print(f"         Vector: {vector_dim} dimensiones")
                else:
                    print(f"   ⚠️  Estado: VACÍA")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Mostrar resumen
        print(f"\n" + "=" * 50)
        print(f"📈 RESUMEN:")
        print(f"   • Colecciones con datos: {len(collections_with_data)}")
        print(f"   • Colecciones: {', '.join(collections_with_data) if collections_with_data else 'Ninguna'}")
        
        return collections_with_data
        
    except Exception as e:
        print(f"❌ Error conectando a Qdrant: {e}")
        return []

def search_movies(query_text=""):
    """
    Busca películas en la colección movie_embeddings
    """
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        print(f"\n🎬 BUSCANDO PELÍCULAS...")
        print("-" * 30)
        
        # Obtener algunas películas al azar
        movies = client.scroll(
            collection_name="movie_embeddings",
            limit=5,
            with_payload=True,
            with_vectors=False
        )[0]
        
        if movies:
            print(f"📽️  Ejemplos de películas en la base de datos:")
            for i, movie in enumerate(movies, 1):
                print(f"   {i}. ID: {movie.id}")
                if movie.payload:
                    # Extraer información relevante
                    title = movie.payload.get('title', 'Sin título')
                    genres = movie.payload.get('genres', [])
                    avg_rating = movie.payload.get('avg_rating', 'N/A')
                    rating_count = movie.payload.get('rating_count', 'N/A')
                    year = movie.payload.get('year', 'N/A')
                    
                    print(f"      Título: {title}")
                    print(f"      Géneros: {genres}")
                    print(f"      Rating promedio: {avg_rating}")
                    print(f"      Número de ratings: {rating_count}")
                    print(f"      Año: {year}")
                print()
        else:
            print("   No se encontraron películas")
            
    except Exception as e:
        print(f"❌ Error buscando películas: {e}")

def search_users():
    """
    Busca usuarios en la colección user_embeddings
    """
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        print(f"\n👥 BUSCANDO USUARIOS...")
        print("-" * 30)
        
        # Obtener algunos usuarios
        users = client.scroll(
            collection_name="user_embeddings",
            limit=5,
            with_payload=True,
            with_vectors=False
        )[0]
        
        if users:
            print(f"👤 Ejemplos de usuarios en la base de datos:")
            for i, user in enumerate(users, 1):
                print(f"   {i}. ID: {user.id}")
                if user.payload:
                    # Mostrar información del usuario
                    user_id = user.payload.get('user_id', 'N/A')
                    movie_count = user.payload.get('movie_count', 'N/A')
                    avg_rating = user.payload.get('avg_rating', 'N/A')
                    min_rating = user.payload.get('min_rating', 'N/A')
                    max_rating = user.payload.get('max_rating', 'N/A')
                    
                    print(f"      Usuario ID: {user_id}")
                    print(f"      Películas calificadas: {movie_count}")
                    print(f"      Rating promedio: {avg_rating}")
                    print(f"      Rating min/max: {min_rating}/{max_rating}")
                print()
        else:
            print("   No se encontraron usuarios")
            
    except Exception as e:
        print(f"❌ Error buscando usuarios: {e}")

if __name__ == "__main__":
    print("🚀 ACCESO A DATOS QDRANT")
    print("=" * 50)
    
    # Verificar datos
    collections_with_data = access_qdrant_data()
    
    # Si hay datos, mostrar ejemplos
    if "movie_embeddings" in collections_with_data:
        search_movies()
    
    if "user_embeddings" in collections_with_data:
        search_users()
    
    print(f"\n✅ ¡SÍ puedes acceder a los datos en Qdrant!")
    print(f"💡 Tienes {len(collections_with_data)} colecciones con información lista para usar.") 