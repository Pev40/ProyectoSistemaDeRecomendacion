# Conversión de Datos ML32M a Base Vectorizada
import os
import sys
import torch
import numpy as np
import asyncio
from pymongo import MongoClient
import redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import time
from tqdm import tqdm
import json

# Agregar paths
sys.path.append('../modelo')

def print_section(title):
    """Imprime sección"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

class ML32MDataConverter:
    """Conversor de datos ML32M a base vectorizada"""
    
    def __init__(self):
        self.model = None
        self.mongo_client = None
        self.redis_client = None
        self.qdrant_client = None
        self.db = None
        
        # Configuración
        self.embedding_dim = 256
        self.batch_size = 100
        self.max_sequence_length = 200
        
        # Mapeo de IDs de películas
        self.movie_id_mapping = {}  # movieId_real -> movieId_modelo
        self.reverse_movie_mapping = {}  # movieId_modelo -> movieId_real
        
        print("Inicializando conversor ML32M...")
    
    def load_model(self):
        """Cargar modelo ML32M"""
        print_section("CARGANDO MODELO ML32M")
        
        try:
            from fix_ml32m_model import load_ml32m_model_fixed
            
            print("Cargando modelo...")
            self.model = load_ml32m_model_fixed()
            
            if self.model is None:
                raise Exception("Error cargando modelo")
            
            self.model.eval()
            print("✓ Modelo ML32M cargado correctamente")
            
            # Estadísticas
            params = sum(p.numel() for p in self.model.parameters())
            print(f"  - Parámetros: {params:,}")
            print(f"  - Embedding dim: {self.embedding_dim}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error cargando modelo: {e}")
            return False
    
    def connect_databases(self):
        """Conectar a bases de datos"""
        print_section("CONECTANDO BASES DE DATOS")
        
        try:
            # MongoDB
            self.mongo_client = MongoClient('mongodb://localhost:27017/')
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
            print(f"✗ Error conectando bases de datos: {e}")
            return False
    
    def verify_data(self):
        """Verificar datos disponibles"""
        print_section("VERIFICANDO DATOS")
        
        try:
            # Verificar colecciones MongoDB
            collections = self.db.list_collection_names()
            print(f"Colecciones disponibles: {collections}")
            
            stats = {}
            
            if 'movies' in collections:
                stats['movies'] = self.db.movies.count_documents({})
                print(f"  - Películas: {stats['movies']:,}")
                
                # Muestra de película
                sample = self.db.movies.find_one()
                if sample:
                    print(f"  - Ejemplo: {sample.get('title', 'N/A')}")
            
            if 'ratings' in collections:
                stats['ratings'] = self.db.ratings.count_documents({})
                print(f"  - Ratings: {stats['ratings']:,}")
            
            if 'tags' in collections:
                stats['tags'] = self.db.tags.count_documents({})
                print(f"  - Tags: {stats['tags']:,}")
            
            # Verificar usuarios únicos
            if 'ratings' in collections:
                unique_users = len(self.db.ratings.distinct('userId'))
                stats['unique_users'] = unique_users
                print(f"  - Usuarios únicos: {unique_users:,}")
            
            # Guardar estadísticas en Redis
            self.redis_client.set('ml32m_stats', json.dumps(stats))
            
            return stats
            
        except Exception as e:
            print(f"✗ Error verificando datos: {e}")
            return None
    
    def create_qdrant_collections(self):
        """Crear colecciones en Qdrant"""
        print_section("CREANDO COLECCIONES QDRANT")
        
        try:
            # Configuración de colecciones
            collections_config = {
                'movie_embeddings': {
                    'vectors': VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                    'description': 'Embeddings de películas basados en secuencias de usuarios'
                },
                'user_embeddings': {
                    'vectors': VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                    'description': 'Embeddings de usuarios basados en sus secuencias'
                },
                'sequence_embeddings': {
                    'vectors': VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
                    'description': 'Embeddings de secuencias de interacción'
                }
            }
            
            for collection_name, config in collections_config.items():
                try:
                    # Verificar si existe
                    existing = self.qdrant_client.get_collections()
                    existing_names = [c.name for c in existing.collections]
                    
                    if collection_name in existing_names:
                        print(f"  - '{collection_name}' ya existe")
                        continue
                    
                    # Crear colección
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=config['vectors']
                    )
                    
                    print(f"✓ Colección '{collection_name}' creada")
                    
                except Exception as e:
                    print(f"  - Error con '{collection_name}': {e}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creando colecciones: {e}")
            return False
    
    def generate_movie_embeddings(self, limit=None):
        """Generar embeddings de películas"""
        print_section("GENERANDO EMBEDDINGS DE PELÍCULAS")
        
        try:
            # Verificar que tenemos el mapeo de IDs
            if not self.movie_id_mapping:
                print("✗ Error: Mapeo de IDs de películas no disponible")
                return False
            
            # Obtener ratings agrupados por película
            pipeline = [
                {
                    '$group': {
                        '_id': '$movieId',
                        'ratings': {
                            '$push': {
                                'userId': '$userId',
                                'rating': '$rating',
                                'timestamp': '$timestamp'
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$match': {'count': {'$gte': 10}}},  # Películas con al menos 10 ratings
                {'$sort': {'count': -1}}
            ]
            
            if limit:
                pipeline.append({'$limit': limit})
            
            print("Procesando películas...")
            movie_ratings = list(self.db.ratings.aggregate(pipeline))
            
            # Filtrar solo películas que están en nuestro mapeo
            valid_movies = []
            for movie_data in movie_ratings:
                real_movie_id = movie_data['_id']
                if real_movie_id in self.movie_id_mapping:
                    valid_movies.append(movie_data)
            
            print(f"Películas válidas a procesar: {len(valid_movies)}")
            
            movie_embeddings = []
            batch_count = 0
            processed = 0
            
            print(f"Iniciando procesamiento de {len(valid_movies)} películas...")
            
            for i, movie_data in enumerate(valid_movies):
                real_movie_id = movie_data['_id']
                model_movie_id = self.movie_id_mapping[real_movie_id]
                ratings = movie_data['ratings']
                
                # Validar que hay ratings
                if not ratings or len(ratings) == 0:
                    continue
                
                # Crear secuencia representativa de la película usando otras películas relacionadas
                # En lugar de usar IDs de usuarios, vamos a crear una secuencia de películas
                # basada en co-ocurrencias con otros usuarios
                
                # Obtener usuarios que han calificado esta película
                user_ids = [r['userId'] for r in ratings[:50]]  # Limitar a 50 usuarios
                
                # Para cada usuario, obtener otras películas que han calificado
                related_movies = []
                for user_id in user_ids[:10]:  # Limitar a 10 usuarios para eficiencia
                    user_movies = list(self.db.ratings.find(
                        {'userId': user_id, 'movieId': {'$ne': real_movie_id}},
                        {'movieId': 1, 'rating': 1}
                    ).sort('rating', -1).limit(5))
                    
                    for um in user_movies:
                        other_real_id = um['movieId']
                        if other_real_id in self.movie_id_mapping:
                            other_model_id = self.movie_id_mapping[other_real_id]
                            related_movies.append(other_model_id)
                
                # Si no tenemos suficientes películas relacionadas, usar una secuencia simple
                if len(related_movies) < 5:
                    movie_sequence = [model_movie_id] * self.max_sequence_length
                else:
                    # Usar películas relacionadas + la película actual
                    movie_sequence = related_movies[:self.max_sequence_length-1] + [model_movie_id]
                    
                    # Padding si es necesario
                    if len(movie_sequence) < self.max_sequence_length:
                        padding = [model_movie_id] * (self.max_sequence_length - len(movie_sequence))
                        movie_sequence = padding + movie_sequence
                    elif len(movie_sequence) > self.max_sequence_length:
                        movie_sequence = movie_sequence[-self.max_sequence_length:]
                
                # Validar que todos los IDs están en rango válido
                max_valid_id = len(self.movie_id_mapping)
                if any(mid > max_valid_id or mid <= 0 for mid in movie_sequence):
                    print(f"  - Película {real_movie_id}: IDs fuera de rango, saltando...")
                    continue
                
                try:
                    # Generar embedding
                    sequence_tensor = torch.tensor([movie_sequence], dtype=torch.long)
                    
                    with torch.no_grad():
                        seq_emb, _ = self.model(sequence_tensor)
                        
                        # Validar dimensiones del tensor
                        if seq_emb.dim() < 3 or seq_emb.size(1) == 0:
                            print(f"  - Película {real_movie_id}: tensor inválido {seq_emb.shape}, saltando...")
                            continue
                        
                        # Usar la representación del último elemento (la película target)
                        movie_embedding = seq_emb[:, -1, :].squeeze().numpy()
                        
                        # Validar embedding resultante
                        if movie_embedding.shape[0] != self.embedding_dim:
                            print(f"  - Película {real_movie_id}: embedding inválido {movie_embedding.shape}, saltando...")
                            continue
                            
                except Exception as e:
                    print(f"  - Película {real_movie_id}: error en embedding ({e}), saltando...")
                    continue
                
                # Preparar para Qdrant - usar real_movie_id como ID para consistencia
                point = PointStruct(
                    id=int(real_movie_id),
                    vector=movie_embedding.tolist(),
                    payload={
                        'movie_id': int(real_movie_id),
                        'model_movie_id': int(model_movie_id),
                        'rating_count': len(ratings),
                        'avg_rating': sum(r['rating'] for r in ratings) / len(ratings),
                        'type': 'movie'
                    }
                )
                
                movie_embeddings.append(point)
                processed += 1
                
                # Mostrar progreso cada 100 películas
                if processed % 100 == 0:
                    progress = (processed / len(valid_movies)) * 100
                    print(f"  - Progreso: {processed}/{len(valid_movies)} películas ({progress:.1f}%)")
                
                # Batch insert
                if len(movie_embeddings) >= self.batch_size:
                    self.qdrant_client.upsert(
                        collection_name='movie_embeddings',
                        points=movie_embeddings
                    )
                    batch_count += 1
                    print(f"  - Batch {batch_count}: {len(movie_embeddings)} embeddings insertados")
                    movie_embeddings = []
            
            # Insertar último batch
            if movie_embeddings:
                self.qdrant_client.upsert(
                    collection_name='movie_embeddings',
                    points=movie_embeddings
                )
                batch_count += 1
                print(f"  - Batch final {batch_count}: {len(movie_embeddings)} embeddings insertados")
            
            print(f"✓ Embeddings de películas generados: {processed} películas procesadas en {batch_count} batches")
            return True
            
        except Exception as e:
            print(f"✗ Error generando embeddings de películas: {e}")
            import traceback
            print(f"Detalles del error: {traceback.format_exc()}")
            return False
    
    def generate_user_embeddings(self, limit=None):
        """Generar embeddings de usuarios"""
        print_section("GENERANDO EMBEDDINGS DE USUARIOS")
        
        try:
            # Verificar que tenemos el mapeo de IDs
            if not self.movie_id_mapping:
                print("✗ Error: Mapeo de IDs de películas no disponible")
                return False
            
            max_valid_id = len(self.movie_id_mapping)
            print(f"Rango válido de IDs de película: 1 - {max_valid_id}")
            
            # Obtener secuencias de usuarios
            pipeline = [
                {
                    '$group': {
                        '_id': '$userId',
                        'movies': {
                            '$push': {
                                'movieId': '$movieId',
                                'rating': '$rating',
                                'timestamp': '$timestamp'
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$match': {'count': {'$gte': 20}}},  # Usuarios con al menos 20 ratings
                {'$sort': {'count': -1}}
            ]
            
            if limit:
                pipeline.append({'$limit': limit})
            
            print("Procesando usuarios...")
            user_sequences = list(self.db.ratings.aggregate(pipeline))
            
            print(f"Usuarios a procesar: {len(user_sequences)}")
            
            user_embeddings = []
            batch_count = 0
            processed = 0
            skipped_invalid_movies = 0
            skipped_short_sequences = 0
            
            print(f"Iniciando procesamiento de {len(user_sequences)} usuarios...")
            
            for i, user_data in enumerate(user_sequences):
                user_id = user_data['_id']
                movies = user_data['movies']
                
                # Validar que hay películas
                if not movies or len(movies) == 0:
                    continue
                
                # Ordenar por timestamp y crear secuencia
                movies_sorted = sorted(movies, key=lambda x: x.get('timestamp', 0))
                movie_sequence = []
                
                for movie in movies_sorted:
                    real_movie_id = movie.get('movieId', 0)
                    if real_movie_id > 0 and real_movie_id in self.movie_id_mapping:
                        model_movie_id = self.movie_id_mapping[real_movie_id]
                        # Validar que el ID mapeado está en rango
                        if 1 <= model_movie_id <= max_valid_id:
                            movie_sequence.append(model_movie_id)
                        else:
                            skipped_invalid_movies += 1
                    else:
                        skipped_invalid_movies += 1
                
                # Validar secuencia mínima
                if len(movie_sequence) < 5:
                    skipped_short_sequences += 1
                    continue
                
                # Padding/truncate
                if len(movie_sequence) > self.max_sequence_length:
                    movie_sequence = movie_sequence[-self.max_sequence_length:]  # Tomar los más recientes
                else:
                    movie_sequence = [0] * (self.max_sequence_length - len(movie_sequence)) + movie_sequence
                
                # Validar que la secuencia final es correcta
                if len(movie_sequence) != self.max_sequence_length:
                    print(f"  - Usuario {user_id}: error en padding, saltando...")
                    continue
                
                # Validar todos los IDs en la secuencia final
                invalid_ids = [mid for mid in movie_sequence if mid != 0 and (mid > max_valid_id or mid <= 0)]
                if invalid_ids:
                    print(f"  - Usuario {user_id}: IDs inválidos {invalid_ids[:3]}..., saltando...")
                    continue
                
                try:
                    # Generar embedding
                    sequence_tensor = torch.tensor([movie_sequence], dtype=torch.long)
                    
                    with torch.no_grad():
                        seq_emb, _ = self.model(sequence_tensor)
                        
                        # Validar dimensiones del tensor
                        if seq_emb.dim() < 3 or seq_emb.size(1) == 0:
                            print(f"  - Usuario {user_id}: tensor inválido {seq_emb.shape}, saltando...")
                            continue
                        
                        user_embedding = seq_emb[:, -1, :].squeeze().numpy()  # Usar último estado
                        
                        # Validar embedding resultante
                        if user_embedding.shape[0] != self.embedding_dim:
                            print(f"  - Usuario {user_id}: embedding inválido {user_embedding.shape}, saltando...")
                            continue
                            
                except Exception as e:
                    print(f"  - Usuario {user_id}: error en embedding ({e}), saltando...")
                    continue
                
                # Preparar para Qdrant
                point = PointStruct(
                    id=int(user_id),
                    vector=user_embedding.tolist(),
                    payload={
                        'user_id': int(user_id),
                        'movie_count': len(movies),
                        'valid_movie_count': len([m for m in movie_sequence if m != 0]),
                        'avg_rating': sum(m['rating'] for m in movies) / len(movies),
                        'type': 'user'
                    }
                )
                
                user_embeddings.append(point)
                processed += 1
                
                # Mostrar progreso cada 50 usuarios
                if processed % 50 == 0:
                    progress = (processed / len(user_sequences)) * 100
                    print(f"  - Progreso: {processed}/{len(user_sequences)} usuarios ({progress:.1f}%)")
                
                # Batch insert
                if len(user_embeddings) >= self.batch_size:
                    self.qdrant_client.upsert(
                        collection_name='user_embeddings',
                        points=user_embeddings
                    )
                    batch_count += 1
                    print(f"  - Batch {batch_count}: {len(user_embeddings)} embeddings insertados")
                    user_embeddings = []
            
            # Insertar último batch
            if user_embeddings:
                self.qdrant_client.upsert(
                    collection_name='user_embeddings',
                    points=user_embeddings
                )
                batch_count += 1
                print(f"  - Batch final {batch_count}: {len(user_embeddings)} embeddings insertados")
            
            # Mostrar estadísticas finales
            print(f"✓ Embeddings de usuarios generados: {processed} usuarios procesados en {batch_count} batches")
            if skipped_invalid_movies > 0:
                print(f"  - Películas inválidas saltadas: {skipped_invalid_movies}")
            if skipped_short_sequences > 0:
                print(f"  - Secuencias muy cortas saltadas: {skipped_short_sequences}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error generando embeddings de usuarios: {e}")
            import traceback
            print(f"Detalles del error: {traceback.format_exc()}")
            return False
    
    def cache_metadata(self):
        """Cachear metadata en Redis - versión optimizada"""
        print_section("CACHEANDO METADATA")
        
        try:
            print("Iniciando caché de metadata optimizado...")
            
            # 1. Cachear películas populares (método más eficiente)
            print("📊 Calculando películas populares...")
            
            # Usar ratings agregados en lugar de lookup pesado
            popular_ratings = list(self.db.ratings.aggregate([
                {
                    '$group': {
                        '_id': '$movieId',
                        'rating_count': {'$sum': 1},
                        'avg_rating': {'$avg': '$rating'}
                    }
                },
                {'$match': {'rating_count': {'$gte': 100}}},
                {'$sort': {'rating_count': -1}},
                {'$limit': 1000}
            ]))
            
            print(f"  - {len(popular_ratings)} películas populares encontradas")
            
            # Obtener información de películas por lotes
            popular_movies = []
            movie_ids = [item['_id'] for item in popular_ratings]
            
            print("  - Obteniendo detalles de películas...")
            batch_size = 100
            for i in range(0, len(movie_ids), batch_size):
                batch_ids = movie_ids[i:i+batch_size]
                
                # Buscar películas en lote
                movies_batch = list(self.db.movies.find(
                    {'movieId': {'$in': batch_ids}},
                    {'movieId': 1, 'title': 1, 'genres': 1}
                ))
                
                # Combinar con estadísticas de rating
                for movie in movies_batch:
                    movie_id = movie['movieId']
                    rating_info = next((r for r in popular_ratings if r['_id'] == movie_id), None)
                    
                    if rating_info:
                        movie['rating_count'] = rating_info['rating_count']
                        movie['avg_rating'] = rating_info['avg_rating']
                        popular_movies.append(movie)
                
                # Mostrar progreso
                progress = min((i + batch_size) / len(movie_ids) * 100, 100)
                print(f"    - Progreso: {progress:.1f}%")
            
            # Guardar en Redis
            self.redis_client.set('popular_movies', json.dumps(popular_movies, default=str))
            print(f"✓ {len(popular_movies)} películas populares cacheadas")
            
            # 2. Cachear géneros (método optimizado)
            print("🎭 Extrayendo géneros únicos...")
            
            # Usar agregación en lugar de iteración
            genres_pipeline = [
                {'$match': {'genres': {'$exists': True, '$ne': None}}},
                {'$project': {'genres': 1}},
                {'$limit': 10000}  # Limitar para evitar sobrecarga
            ]
            
            all_genres = set()
            movies_sample = list(self.db.movies.aggregate(genres_pipeline))
            
            for movie in movies_sample:
                if movie.get('genres'):
                    genres = movie['genres'].split('|') if isinstance(movie['genres'], str) else []
                    all_genres.update(g.strip() for g in genres if g.strip())
            
            self.redis_client.set('all_genres', json.dumps(list(all_genres)))
            print(f"✓ {len(all_genres)} géneros únicos cacheados")
            
            # 3. Estadísticas de conversión (optimizado)
            print("📈 Calculando estadísticas finales...")
            
            # Usar count estimado para colecciones grandes
            try:
                total_movies = self.db.movies.estimated_document_count()
                total_ratings = self.db.ratings.estimated_document_count()
                print("  - Usando conteos estimados (más rápido)")
            except:
                # Fallback a conteo exacto con timeout
                total_movies = self.db.movies.count_documents({})
                total_ratings = self.db.ratings.count_documents({})
                print("  - Usando conteos exactos")
            
            # Para usuarios únicos, usar un sample en lugar de distinct completo
            print("  - Estimando usuarios únicos...")
            sample_size = min(100000, total_ratings)  # Sample de max 100k registros
            sample_users = list(self.db.ratings.aggregate([
                {'$sample': {'size': sample_size}},
                {'$group': {'_id': '$userId'}},
                {'$count': 'unique_users'}
            ]))
            
            unique_users_sample = sample_users[0]['unique_users'] if sample_users else 0
            # Estimar total basado en el sample
            estimated_total_users = int(unique_users_sample * (total_ratings / sample_size))
            
            conversion_stats = {
                'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_movies': total_movies,
                'total_ratings': total_ratings,
                'estimated_users': estimated_total_users,
                'embedding_dim': self.embedding_dim,
                'model_params': sum(p.numel() for p in self.model.parameters()) if self.model else 0,
                'note': 'Usuarios estimados basado en sample para mejor rendimiento'
            }
            
            self.redis_client.set('conversion_stats', json.dumps(conversion_stats))
            print("✓ Estadísticas de conversión guardadas")
            
            # 4. Caché adicional útil
            print("💾 Cacheando información adicional...")
            
            # Cachear mapeo de IDs si existe
            if hasattr(self, 'movie_id_mapping') and self.movie_id_mapping:
                mapping_sample = dict(list(self.movie_id_mapping.items())[:1000])  # Sample del mapeo
                self.redis_client.set('movie_mapping_sample', json.dumps(mapping_sample))
                print(f"✓ Sample de mapeo de IDs cacheado ({len(mapping_sample)} items)")
            
            # Resumen de caché
            cache_summary = {
                'popular_movies_count': len(popular_movies),
                'genres_count': len(all_genres),
                'last_update': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.redis_client.set('cache_summary', json.dumps(cache_summary))
            
            print("✓ Metadata optimizada cacheada exitosamente")
            return True
            
        except Exception as e:
            print(f"✗ Error cacheando metadata: {e}")
            import traceback
            print(f"Detalles del error: {traceback.format_exc()}")
            return False
    
    def create_movie_id_mapping(self):
        """Crear mapeo de movieIds reales a índices del modelo"""
        print_section("CREANDO MAPEO DE IDS DE PELÍCULAS")
        
        try:
            # Primero intentar cargar mapeo desde archivo preprocesado si existe
            if self.load_preprocessing_mapping():
                return True
            
            # Si no existe, crear mapeo basado en popularidad (backup)
            print("⚠️ Archivo preprocesado no encontrado, creando mapeo basado en popularidad...")
            
            # Obtener películas ordenadas por popularidad (mismo criterio del preprocesamiento)
            popular_movies = list(self.db.ratings.aggregate([
                {'$group': {
                    '_id': '$movieId',
                    'count': {'$sum': 1}
                }},
                {'$match': {'count': {'$gte': 5}}},  # Mismo filtro del preprocesamiento
                {'$sort': {'count': -1}},
                {'$limit': 84432}  # Exactamente el número del dataset stats
            ]))
            
            print(f"Películas filtradas (≥5 ratings): {len(popular_movies)}")
            
            # Crear mapeo: movieId_real -> movieId_modelo (1 a N)
            self.movie_id_mapping = {}
            self.reverse_movie_mapping = {}
            
            for model_id, movie_data in enumerate(popular_movies, 1):
                real_id = movie_data['_id']
                self.movie_id_mapping[real_id] = model_id
                self.reverse_movie_mapping[model_id] = real_id
            
            print(f"✓ Mapeo creado: {len(self.movie_id_mapping)} películas")
            print(f"  - Rango modelo: 1 - {len(self.movie_id_mapping)}")
            
            # Guardar mapeo en Redis
            import json
            self.redis_client.set('movie_id_mapping', json.dumps(self.movie_id_mapping))
            self.redis_client.set('reverse_movie_mapping', json.dumps(self.reverse_movie_mapping))
            
            return True
            
        except Exception as e:
            print(f"✗ Error creando mapeo: {e}")
            return False
    
    def load_preprocessing_mapping(self):
        """Cargar mapeo desde archivo de preprocesamiento original"""
        try:
            # Buscar archivo train/input.txt del preprocesamiento de ml32m
            preprocessing_file = "../modelo/datasets/ml32m/train/input.txt"
            
            if not os.path.exists(preprocessing_file):
                print(f"Archivo preprocesado no encontrado: {preprocessing_file}")
                return False
            
            print(f"📁 Cargando mapeo desde: {preprocessing_file}")
            
            # Leer archivo preprocesado para obtener mapeo exacto
            item_to_model_id = {}
            model_id_to_item = {}
            items_seen = set()
            
            with open(preprocessing_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    # Cada línea contiene una secuencia de items
                    if parts:
                        for item_str in parts:
                            item_id = int(item_str)
                            items_seen.add(item_id)
            
            # Crear mapeo basado en orden de aparición (como en el preprocesamiento)
            sorted_items = sorted(list(items_seen))
            
            for model_id, real_item_id in enumerate(sorted_items, 1):
                item_to_model_id[real_item_id] = model_id
                model_id_to_item[model_id] = real_item_id
            
            self.movie_id_mapping = item_to_model_id
            self.reverse_movie_mapping = model_id_to_item
            
            print(f"✓ Mapeo cargado desde preprocesamiento")
            print(f"  - Items en archivo: {len(items_seen)}")
            print(f"  - Rango modelo: 1 - {len(self.movie_id_mapping)}")
            
            # Verificar que coincide con dataset stats
            expected_items = 84432
            if len(self.movie_id_mapping) != expected_items:
                print(f"⚠️ Advertencia: mapeo tiene {len(self.movie_id_mapping)} items, esperado {expected_items}")
            
            # Guardar en Redis
            import json
            self.redis_client.set('movie_id_mapping', json.dumps(self.movie_id_mapping))
            self.redis_client.set('reverse_movie_mapping', json.dumps(self.reverse_movie_mapping))
            
            return True
            
        except Exception as e:
            print(f"Error cargando mapeo del preprocesamiento: {e}")
            return False
    
    def run_conversion(self, movie_limit=None, user_limit=None):
        """Ejecutar conversión completa"""
        print("CONVERSION ML32M A BASE VECTORIZADA")
        print("="*60)
        
        start_time = time.time()
        
        # Paso 1: Cargar modelo
        if not self.load_model():
            return False
        
        # Paso 2: Conectar bases de datos
        if not self.connect_databases():
            return False
        
        # Paso 3: Verificar datos
        stats = self.verify_data()
        if not stats:
            return False
        
        # Paso 4: Crear colecciones Qdrant
        if not self.create_qdrant_collections():
            return False
        
        # Paso 5: Crear mapeo de IDs de películas
        if not self.create_movie_id_mapping():
            return False
        
        # Paso 6: Generar embeddings de películas
        if not self.generate_movie_embeddings(limit=movie_limit):
            return False
        
        # Paso 7: Generar embeddings de usuarios
        if not self.generate_user_embeddings(limit=user_limit):
            return False
        
        # Paso 8: Cachear metadata
        if not self.cache_metadata():
            return False
        
        # Resumen final
        elapsed_time = time.time() - start_time
        
        print_section("CONVERSION COMPLETADA")
        print(f"✓ Conversión exitosa en {elapsed_time:.1f} segundos")
        print(f"  - Películas: {stats.get('movies', 0):,}")
        print(f"  - Usuarios: {stats.get('unique_users', 0):,}")
        print(f"  - Ratings: {stats.get('ratings', 0):,}")
        print(f"  - Embedding dim: {self.embedding_dim}")
        
        print("\nSistema listo para:")
        print("1. Búsquedas vectoriales")
        print("2. Recomendaciones ML32M")
        print("3. API de producción")
        
        return True
    
    def cleanup(self):
        """Limpiar conexiones"""
        if self.mongo_client:
            self.mongo_client.close()

def main():
    """Función principal"""
    converter = ML32MDataConverter()
    
    try:
        # Opciones de conversión
        print("Opciones de conversión:")
        print("1. Conversión completa (puede tomar varias horas)")
        print("2. Conversión de prueba (1000 películas, 500 usuarios)")
        print("3. Solo película embeddings")
        print("4. Solo usuario embeddings")
        
        choice = input("\nSelecciona opción (1-4) [2]: ").strip() or "2"
        
        if choice == "1":
            success = converter.run_conversion()
        elif choice == "2":
            success = converter.run_conversion(movie_limit=1000, user_limit=500)
        elif choice == "3":
            success = (converter.load_model() and 
                      converter.connect_databases() and
                      converter.create_qdrant_collections() and
                      converter.create_movie_id_mapping() and
                      converter.generate_movie_embeddings(limit=1000))
        elif choice == "4":
            success = (converter.load_model() and 
                      converter.connect_databases() and
                      converter.create_qdrant_collections() and
                      converter.create_movie_id_mapping() and
                      converter.generate_user_embeddings(limit=500))
        else:
            print("Opción inválida")
            return
        
        if success:
            print("\n🎉 ¡Conversión completada exitosamente!")
        else:
            print("\n❌ Error en la conversión")
    
    except KeyboardInterrupt:
        print("\n⚠️ Conversión interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        converter.cleanup()

if __name__ == "__main__":
    main() 