# Conversión Simplificada ML32M a Base Vectorizada
import os
import sys
import torch
import numpy as np
from pymongo import MongoClient
import redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import time
import json
from collections import defaultdict

# Agregar paths
sys.path.append('../modelo')

def print_section(title):
    """Imprime sección"""
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

class SimpleML32MConverter:
    """Conversor simplificado y eficiente"""
    
    def __init__(self):
        self.model = None
        self.mongo_client = None
        self.redis_client = None
        self.qdrant_client = None
        self.db = None
        
        # Configuración optimizada
        self.embedding_dim = 256
        self.batch_size = 50  # Reducido para mejor manejo
        self.max_sequence_length = 50  # Reducido para eficiencia
        
        print("Inicializando conversor simple ML32M...")
    
    def load_model(self):
        """Cargar modelo ML32M"""
        print_section("CARGANDO MODELO")
        
        try:
            from fix_ml32m_model import load_ml32m_model_fixed
            
            print("Cargando modelo...")
            self.model = load_ml32m_model_fixed()
            
            if self.model is None:
                raise Exception("Error cargando modelo")
            
            self.model.eval()
            print("✓ Modelo cargado")
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def connect_databases(self):
        """Conectar a bases de datos"""
        print_section("CONECTANDO BASES")
        
        try:
            # MongoDB con timeout
            self.mongo_client = MongoClient(
                'mongodb://localhost:27017/',
                serverSelectionTimeoutMS=5000
            )
            self.db = self.mongo_client['movie_recommendations']
            print("✓ MongoDB conectado")
            
            # Redis
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            print("✓ Redis conectado")
            
            # Qdrant
            self.qdrant_client = QdrantClient(host="localhost", port=6333)
            print("✓ Qdrant conectado")
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def create_collections(self):
        """Crear colecciones Qdrant"""
        print_section("CREANDO COLECCIONES")
        
        try:
            collections = ['movie_embeddings', 'user_embeddings']
            
            for collection_name in collections:
                try:
                    # Verificar si existe
                    existing = self.qdrant_client.get_collections()
                    existing_names = [c.name for c in existing.collections]
                    
                    if collection_name in existing_names:
                        print(f"  - '{collection_name}' existe")
                        continue
                    
                    # Crear
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.embedding_dim, 
                            distance=Distance.COSINE
                        )
                    )
                    
                    print(f"✓ '{collection_name}' creada")
                    
                except Exception as e:
                    print(f"  - Error con '{collection_name}': {e}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def process_movies_simple(self, limit=100):
        """Procesar películas de manera simple"""
        print_section(f"PROCESANDO {limit} PELÍCULAS")
        
        try:
            print("Obteniendo películas populares...")
            
            # Método simple: obtener películas y contar ratings uno por uno
            movie_stats = defaultdict(list)
            
            # Obtener muestra de ratings para películas populares
            print("Analizando ratings...")
            rating_cursor = self.db.ratings.find().limit(100000)  # Muestra de 100k ratings
            
            count = 0
            for rating in rating_cursor:
                movie_id = rating['movieId']
                user_id = rating['userId']
                rating_val = rating['rating']
                
                movie_stats[movie_id].append({
                    'userId': user_id,
                    'rating': rating_val
                })
                
                count += 1
                if count % 10000 == 0:
                    print(f"  - Procesados {count} ratings...")
            
            # Seleccionar películas con más ratings
            popular_movies = sorted(
                movie_stats.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:limit]
            
            print(f"Generando embeddings para {len(popular_movies)} películas...")
            
            movie_embeddings = []
            
            for i, (movie_id, ratings) in enumerate(popular_movies):
                try:
                    # Crear secuencia de usuarios
                    user_sequence = [r['userId'] for r in ratings[:self.max_sequence_length]]
                    
                    # Padding
                    while len(user_sequence) < self.max_sequence_length:
                        user_sequence.append(0)
                    
                    # Generar embedding
                    sequence_tensor = torch.tensor([user_sequence], dtype=torch.long)
                    
                    with torch.no_grad():
                        seq_emb, _ = self.model(sequence_tensor)
                        movie_embedding = seq_emb.mean(dim=1).squeeze().numpy()
                    
                    # Crear punto
                    point = PointStruct(
                        id=int(movie_id),
                        vector=movie_embedding.tolist(),
                        payload={
                            'movie_id': int(movie_id),
                            'rating_count': len(ratings),
                            'avg_rating': sum(r['rating'] for r in ratings) / len(ratings),
                            'type': 'movie'
                        }
                    )
                    
                    movie_embeddings.append(point)
                    
                    # Progreso
                    if (i + 1) % 10 == 0:
                        progress = ((i + 1) / len(popular_movies)) * 100
                        print(f"  - {i + 1}/{len(popular_movies)} películas ({progress:.1f}%)")
                    
                    # Batch insert
                    if len(movie_embeddings) >= self.batch_size:
                        self.qdrant_client.upsert(
                            collection_name='movie_embeddings',
                            points=movie_embeddings
                        )
                        print(f"  - Insertado batch de {len(movie_embeddings)} embeddings")
                        movie_embeddings = []
                
                except Exception as e:
                    print(f"  - Error con película {movie_id}: {e}")
                    continue
            
            # Insertar último batch
            if movie_embeddings:
                self.qdrant_client.upsert(
                    collection_name='movie_embeddings',
                    points=movie_embeddings
                )
                print(f"  - Insertado batch final de {len(movie_embeddings)} embeddings")
            
            print(f"✓ {len(popular_movies)} películas procesadas")
            return True
            
        except Exception as e:
            print(f"✗ Error procesando películas: {e}")
            return False
    
    def process_users_simple(self, limit=50):
        """Procesar usuarios de manera simple"""
        print_section(f"PROCESANDO {limit} USUARIOS")
        
        try:
            print("Obteniendo usuarios activos...")
            
            # Obtener usuarios con más ratings
            user_stats = defaultdict(list)
            
            # Muestra de ratings para usuarios activos
            rating_cursor = self.db.ratings.find().limit(50000)  # Muestra de 50k ratings
            
            count = 0
            for rating in rating_cursor:
                user_id = rating['userId']
                movie_id = rating['movieId']
                rating_val = rating['rating']
                timestamp = rating.get('timestamp', 0)
                
                user_stats[user_id].append({
                    'movieId': movie_id,
                    'rating': rating_val,
                    'timestamp': timestamp
                })
                
                count += 1
                if count % 5000 == 0:
                    print(f"  - Procesados {count} ratings...")
            
            # Seleccionar usuarios más activos
            active_users = sorted(
                user_stats.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:limit]
            
            print(f"Generando embeddings para {len(active_users)} usuarios...")
            
            user_embeddings = []
            
            for i, (user_id, movies) in enumerate(active_users):
                try:
                    # Ordenar por timestamp y crear secuencia
                    movies_sorted = sorted(movies, key=lambda x: x['timestamp'])
                    movie_sequence = [m['movieId'] for m in movies_sorted[-self.max_sequence_length:]]
                    
                    # Padding
                    while len(movie_sequence) < self.max_sequence_length:
                        movie_sequence.insert(0, 0)  # Padding al inicio
                    
                    # Generar embedding
                    sequence_tensor = torch.tensor([movie_sequence], dtype=torch.long)
                    
                    with torch.no_grad():
                        seq_emb, _ = self.model(sequence_tensor)
                        user_embedding = seq_emb[:, -1, :].squeeze().numpy()  # Último estado
                    
                    # Crear punto
                    point = PointStruct(
                        id=int(user_id),
                        vector=user_embedding.tolist(),
                        payload={
                            'user_id': int(user_id),
                            'movie_count': len(movies),
                            'avg_rating': sum(m['rating'] for m in movies) / len(movies),
                            'type': 'user'
                        }
                    )
                    
                    user_embeddings.append(point)
                    
                    # Progreso
                    if (i + 1) % 5 == 0:
                        progress = ((i + 1) / len(active_users)) * 100
                        print(f"  - {i + 1}/{len(active_users)} usuarios ({progress:.1f}%)")
                    
                    # Batch insert
                    if len(user_embeddings) >= self.batch_size:
                        self.qdrant_client.upsert(
                            collection_name='user_embeddings',
                            points=user_embeddings
                        )
                        print(f"  - Insertado batch de {len(user_embeddings)} embeddings")
                        user_embeddings = []
                
                except Exception as e:
                    print(f"  - Error con usuario {user_id}: {e}")
                    continue
            
            # Insertar último batch
            if user_embeddings:
                self.qdrant_client.upsert(
                    collection_name='user_embeddings',
                    points=user_embeddings
                )
                print(f"  - Insertado batch final de {len(user_embeddings)} embeddings")
            
            print(f"✓ {len(active_users)} usuarios procesados")
            return True
            
        except Exception as e:
            print(f"✗ Error procesando usuarios: {e}")
            return False
    
    def cache_stats(self):
        """Cachear estadísticas básicas"""
        print_section("CACHEANDO ESTADÍSTICAS")
        
        try:
            # Estadísticas básicas
            stats = {
                'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_movies': self.db.movies.count_documents({}),
                'total_ratings': self.db.ratings.count_documents({}),
                'embedding_dim': self.embedding_dim,
                'model_params': sum(p.numel() for p in self.model.parameters()) if self.model else 0
            }
            
            self.redis_client.set('ml32m_conversion_stats', json.dumps(stats))
            print("✓ Estadísticas guardadas")
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def run_simple_conversion(self, movie_limit=100, user_limit=50):
        """Ejecutar conversión simplificada"""
        print("CONVERSION SIMPLE ML32M")
        print("="*50)
        
        start_time = time.time()
        
        # Pasos
        if not self.load_model():
            return False
        
        if not self.connect_databases():
            return False
        
        if not self.create_collections():
            return False
        
        if not self.process_movies_simple(limit=movie_limit):
            return False
        
        if not self.process_users_simple(limit=user_limit):
            return False
        
        if not self.cache_stats():
            return False
        
        # Resumen
        elapsed = time.time() - start_time
        
        print_section("CONVERSION COMPLETADA")
        print(f"✓ Conversión exitosa en {elapsed:.1f} segundos")
        print(f"  - {movie_limit} películas procesadas")
        print(f"  - {user_limit} usuarios procesados")
        print(f"  - Embedding dim: {self.embedding_dim}")
        
        print("\nSistema listo para recomendaciones!")
        
        return True
    
    def cleanup(self):
        """Limpiar conexiones"""
        if self.mongo_client:
            self.mongo_client.close()

def main():
    """Función principal"""
    converter = SimpleML32MConverter()
    
    try:
        print("Conversión simplificada ML32M")
        print("Opciones:")
        print("1. Conversión pequeña (50 películas, 25 usuarios)")
        print("2. Conversión media (200 películas, 100 usuarios)")
        print("3. Conversión grande (500 películas, 250 usuarios)")
        
        choice = input("\nSelecciona opción (1-3) [1]: ").strip() or "1"
        
        if choice == "1":
            success = converter.run_simple_conversion(movie_limit=50, user_limit=25)
        elif choice == "2":
            success = converter.run_simple_conversion(movie_limit=200, user_limit=100)
        elif choice == "3":
            success = converter.run_simple_conversion(movie_limit=500, user_limit=250)
        else:
            print("Opción inválida")
            return
        
        if success:
            print("\n🎉 ¡Conversión completada!")
        else:
            print("\n❌ Error en conversión")
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        converter.cleanup()

if __name__ == "__main__":
    main() 