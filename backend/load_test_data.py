#!/usr/bin/env python3
"""
Script para cargar datos de prueba en MongoDB
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
import structlog

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

def create_test_movies():
    """Crear películas de prueba"""
    movies = []
    
    # Lista de películas populares para prueba
    movie_titles = [
        "The Shawshank Redemption", "The Godfather", "The Dark Knight",
        "Pulp Fiction", "Fight Club", "Forrest Gump", "Inception",
        "The Matrix", "Goodfellas", "The Silence of the Lambs",
        "Interstellar", "The Departed", "The Green Mile", "Gladiator",
        "The Lion King", "Titanic", "Avatar", "Jurassic Park",
        "Back to the Future", "E.T. the Extra-Terrestrial"
    ]
    
    genres = [
        "Action", "Adventure", "Animation", "Comedy", "Crime",
        "Documentary", "Drama", "Family", "Fantasy", "Horror",
        "Mystery", "Romance", "Sci-Fi", "Thriller", "War"
    ]
    
    for i, title in enumerate(movie_titles):
        movie = {
            "movieId": i + 1,
            "title": title,
            "genres": random.sample(genres, random.randint(1, 3)),
            "year": random.randint(1990, 2020),
            "rating": round(random.uniform(6.0, 9.5), 1),
            "votes": random.randint(1000, 100000)
        }
        movies.append(movie)
    
    return movies

def create_test_users():
    """Crear usuarios de prueba"""
    users = []
    
    for i in range(1, 101):  # 100 usuarios de prueba
        user = {
            "userId": i,
            "age": random.randint(18, 65),
            "gender": random.choice(["M", "F"]),
            "occupation": random.choice([
                "student", "engineer", "teacher", "doctor", "lawyer",
                "artist", "writer", "scientist", "business", "other"
            ]),
            "zipcode": f"{random.randint(10000, 99999)}"
        }
        users.append(user)
    
    return users

def create_test_ratings(movies, users):
    """Crear ratings de prueba"""
    ratings = []
    
    # Generar ratings aleatorios
    for user in users:
        # Cada usuario califica entre 5 y 20 películas
        num_ratings = random.randint(5, 20)
        rated_movies = random.sample(movies, num_ratings)
        
        for movie in rated_movies:
            # Generar timestamp aleatorio en los últimos 2 años
            days_ago = random.randint(0, 730)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            rating = {
                "userId": user["userId"],
                "movieId": movie["movieId"],
                "rating": random.randint(1, 5),
                "timestamp": timestamp
            }
            ratings.append(rating)
    
    return ratings

def create_test_embeddings(movies):
    """Crear embeddings de prueba para películas"""
    embeddings = []
    
    for movie in movies:
        # Crear embedding aleatorio de 128 dimensiones
        embedding = {
            "movieId": movie["movieId"],
            "embedding": [random.uniform(-1, 1) for _ in range(128)],
            "created_at": datetime.now()
        }
        embeddings.append(embedding)
    
    return embeddings

def load_test_data():
    """Cargar datos de prueba en MongoDB"""
    print("🚀 Cargando datos de prueba en MongoDB...")
    
    try:
        # Conectar a MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client.movie_recommendations
        
        # Limpiar datos existentes
        print("🧹 Limpiando datos existentes...")
        db.movies.delete_many({})
        db.users.delete_many({})
        db.ratings.delete_many({})
        db.embeddings.delete_many({})
        
        # Crear datos de prueba
        print("📝 Creando datos de prueba...")
        movies = create_test_movies()
        users = create_test_users()
        ratings = create_test_ratings(movies, users)
        embeddings = create_test_embeddings(movies)
        
        # Insertar datos
        print("💾 Insertando datos...")
        
        if movies:
            db.movies.insert_many(movies)
            print(f"✅ {len(movies)} películas insertadas")
        
        if users:
            db.users.insert_many(users)
            print(f"✅ {len(users)} usuarios insertados")
        
        if ratings:
            db.ratings.insert_many(ratings)
            print(f"✅ {len(ratings)} ratings insertados")
        
        if embeddings:
            db.embeddings.insert_many(embeddings)
            print(f"✅ {len(embeddings)} embeddings insertados")
        
        # Crear índices
        print("🔍 Creando índices...")
        db.movies.create_index("movieId")
        db.users.create_index("userId")
        db.ratings.create_index([("userId", 1), ("movieId", 1)])
        db.embeddings.create_index("movieId")
        
        print("✅ Índices creados")
        
        # Verificar datos
        print("\n📊 Estadísticas de datos:")
        print(f"   - Películas: {db.movies.count_documents({})}")
        print(f"   - Usuarios: {db.users.count_documents({})}")
        print(f"   - Ratings: {db.ratings.count_documents({})}")
        print(f"   - Embeddings: {db.embeddings.count_documents({})}")
        
        client.close()
        print("\n🎉 ¡Datos de prueba cargados exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 Cargador de datos de prueba")
    print("=" * 40)
    
    success = load_test_data()
    
    if success:
        print("\n✅ Datos listos para pruebas")
        print("Ahora puedes ejecutar:")
        print("   python backend/test_components.py")
    else:
        print("\n❌ Error cargando datos")

if __name__ == "__main__":
    main() 