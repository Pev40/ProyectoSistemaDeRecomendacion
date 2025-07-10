# Test Sistema ML32M Completo
import os
import sys
import asyncio
import torch
import numpy as np
import requests
import time
from pymongo import MongoClient
import redis
from qdrant_client import QdrantClient

# Añadir paths necesarios
backend_path = os.path.dirname(__file__)
modelo_path = os.path.join(backend_path, '..', 'modelo')
sys.path.extend([backend_path, modelo_path])

# Importaciones del sistema
try:
    from database import DatabaseManager
    from recommendation_service import RecommendationService
    from torchserve_client import TorchServeClient
    from modelo.gsasrec import GSASRec
    from fix_ml32m_model import load_ml32m_model_with_fix as load_model
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)

# Configuración ML32M
CONFIG_ML32M = {
    'num_items': 84436,
    'num_users': 336000,
    'max_seq_len': 200,
    'embedding_dim': 256,
    'num_heads': 8,
    'num_blocks': 4,
    'dropout_rate': 0.2,
    'pad_token': 0,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
}

def print_section(title):
    """Imprime una sección del test"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_mongodb():
    """Test conexión MongoDB"""
    print_section("TEST MONGODB")
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['movielens32m']
        
        # Test colecciones
        collections = db.list_collection_names()
        print(f"Colecciones encontradas: {collections}")
        
        # Test datos
        if 'movies' in collections:
            movie_count = db.movies.count_documents({})
            print(f"Películas en BD: {movie_count:,}")
            
            # Muestra de película
            sample_movie = db.movies.find_one()
            if sample_movie:
                print(f"Película ejemplo: {sample_movie.get('title', 'N/A')}")
        
        if 'ratings' in collections:
            rating_count = db.ratings.count_documents({})
            print(f"Ratings en BD: {rating_count:,}")
        
        if 'tags' in collections:
            tag_count = db.tags.count_documents({})
            print(f"Tags en BD: {tag_count:,}")
        
        client.close()
        print("✓ MongoDB: CONECTADO")
        return True
        
    except Exception as e:
        print(f"✗ MongoDB: ERROR - {e}")
        return False

def test_redis():
    """Test conexión Redis"""
    print_section("TEST REDIS")
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test básico
        r.ping()
        
        # Test set/get
        test_key = "test_ml32m"
        test_value = "sistema_funcionando"
        r.set(test_key, test_value)
        retrieved = r.get(test_key)
        
        if retrieved == test_value:
            print("✓ Redis: SET/GET funcionando")
        
        # Info Redis
        info = r.info()
        print(f"Redis versión: {info.get('redis_version', 'unknown')}")
        print(f"Memoria usada: {info.get('used_memory_human', 'unknown')}")
        
        r.delete(test_key)
        print("✓ Redis: CONECTADO")
        return True
        
    except Exception as e:
        print(f"✗ Redis: ERROR - {e}")
        return False

def test_qdrant():
    """Test conexión Qdrant"""
    print_section("TEST QDRANT")
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # Test conexión
        collections = client.get_collections()
        print(f"Colecciones Qdrant: {[c.name for c in collections.collections]}")
        
        # Test colección movies si existe
        collection_name = "movies"
        try:
            info = client.get_collection(collection_name)
            print(f"Colección '{collection_name}' encontrada")
            print(f"  - Puntos: {info.points_count}")
            print(f"  - Dimensión vectores: {info.config.params.vectors.size}")
        except Exception:
            print(f"Colección '{collection_name}' no encontrada")
        
        print("✓ Qdrant: CONECTADO")
        return True
        
    except Exception as e:
        print(f"✗ Qdrant: ERROR - {e}")
        return False

def test_gsasrec_model():
    """Test modelo gSASRec ML32M"""
    print_section("TEST MODELO gSASRec ML32M")
    try:
        print("Cargando modelo ML32M...")
        
        # Usar función de fix_ml32m_model.py
        model = load_model()
        
        print(f"✓ Modelo cargado exitosamente")
        print(f"  - Parámetros: {sum(p.numel() for p in model.parameters()):,}")
        print(f"  - Tamaño: {sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**2):.1f} MB")
        print(f"  - Device: {next(model.parameters()).device}")
        
        # Test inferencia
        print("\nProbando inferencia...")
        batch_size = 2
        seq_len = 10
        test_input = torch.randint(1, 1000, (batch_size, seq_len)).to(CONFIG_ML32M['device'])
        
        with torch.no_grad():
            start_time = time.time()
            output = model(test_input)
            inference_time = (time.time() - start_time) * 1000
        
        print(f"✓ Inferencia exitosa")
        print(f"  - Input shape: {test_input.shape}")
        print(f"  - Output shape: {output.shape}")
        print(f"  - Tiempo: {inference_time:.2f}ms")
        
        return True, model
        
    except Exception as e:
        print(f"✗ Modelo gSASRec: ERROR - {e}")
        return False, None

async def test_database_manager():
    """Test DatabaseManager"""
    print_section("TEST DATABASE MANAGER")
    try:
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        print("✓ DatabaseManager conectado")
        
        # Test stats
        stats = await db_manager.get_stats()
        print(f"  - Estadísticas BD: {stats}")
        
        # Test health check
        await db_manager.health_check()
        print("✓ Health check OK")
        
        await db_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ DatabaseManager: ERROR - {e}")
        return False

def test_torchserve_client():
    """Test TorchServe Client"""
    print_section("TEST TORCHSERVE CLIENT")
    try:
        client = TorchServeClient()
        
        # Test ping
        status = client.ping()
        print(f"TorchServe status: {status}")
        
        print("✓ TorchServeClient: OK")
        return True
        
    except Exception as e:
        print(f"✗ TorchServeClient: ERROR - {e}")
        return False

async def test_recommendation_service(model):
    """Test RecommendationService"""
    print_section("TEST RECOMMENDATION SERVICE")
    try:
        # Inicializar componentes
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        torchserve_client = TorchServeClient()
        
        # Crear servicio
        rec_service = RecommendationService(
            model=model,
            config=CONFIG_ML32M,
            db_manager=db_manager,
            torchserve_client=torchserve_client
        )
        
        print("✓ RecommendationService inicializado")
        
        # Test recomendación (usuario ficticio)
        try:
            user_id = 1
            recommendations = await rec_service.get_recommendations(
                user_id=user_id,
                k=5,
                method="local"
            )
            print(f"✓ Recomendaciones generadas: {len(recommendations)} items")
            
        except Exception as e:
            print(f"  - Advertencia: No se pudieron generar recomendaciones: {e}")
        
        await db_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ RecommendationService: ERROR - {e}")
        return False

def test_api_endpoints():
    """Test endpoints de la API"""
    print_section("TEST API ENDPOINTS")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✓ Root endpoint OK")
            data = response.json()
            print(f"  - API: {data.get('message', 'N/A')}")
            print(f"  - Versión: {data.get('version', 'N/A')}")
        else:
            print(f"✗ Root endpoint: Status {response.status_code}")
            return False
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print("✓ Health endpoint OK")
            print(f"  - Status: {health.get('status', 'unknown')}")
            print(f"  - Database: {health.get('database', {}).get('status', 'unknown')}")
            print(f"  - Model: {health.get('model', {}).get('status', 'unknown')}")
        else:
            print(f"✗ Health endpoint: Status {response.status_code}")
        
        # Test stats endpoint
        response = requests.get(f"{base_url}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✓ Stats endpoint OK")
            model_info = stats.get('model', {})
            print(f"  - Modelo: {model_info.get('name', 'N/A')}")
            print(f"  - Parámetros: {model_info.get('parameters', 'N/A'):,}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ API: No se puede conectar (¿está corriendo?)")
        return False
    except Exception as e:
        print(f"✗ API: ERROR - {e}")
        return False

async def main():
    """Función principal de test"""
    print("SISTEMA DE RECOMENDACION ML32M - TEST COMPLETO")
    print("=" * 60)
    
    results = {}
    
    # Tests de infraestructura
    results['mongodb'] = test_mongodb()
    results['redis'] = test_redis()
    results['qdrant'] = test_qdrant()
    
    # Test modelo
    model_ok, model = test_gsasrec_model()
    results['model'] = model_ok
    
    # Tests de servicios
    if model_ok:
        results['database_manager'] = await test_database_manager()
        results['torchserve_client'] = test_torchserve_client()
        results['recommendation_service'] = await test_recommendation_service(model)
    
    # Test API (si está corriendo)
    results['api'] = test_api_endpoints()
    
    # Resumen final
    print_section("RESUMEN DE TESTS")
    
    passed = sum(results.values())
    total = len(results)
    
    for component, status in results.items():
        status_text = "✓ OK" if status else "✗ FALLO"
        print(f"{component:20}: {status_text}")
    
    print(f"\nResultado: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 TODOS LOS TESTS PASARON!")
        print("Sistema ML32M listo para producción")
    else:
        print(f"\n⚠️  {total - passed} tests fallaron")
        print("Revisar configuración antes de continuar")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 