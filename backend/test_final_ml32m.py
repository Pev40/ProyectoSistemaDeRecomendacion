# Test Final Sistema ML32M
import os
import sys
import torch
from pymongo import MongoClient
import redis
from qdrant_client import QdrantClient

# Agregar path
sys.path.append('../modelo')

def test_infrastructure():
    """Test componentes de infraestructura"""
    print("=" * 50)
    print("TEST INFRAESTRUCTURA")
    print("=" * 50)
    
    results = {}
    
    # MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['movielens32m']
        collections = db.list_collection_names()
        
        if 'movies' in collections:
            movies = db.movies.count_documents({})
            print(f"✓ MongoDB: {movies:,} películas")
        else:
            print("⚠️  MongoDB: Sin datos de películas")
        
        client.close()
        results['mongodb'] = True
    except:
        print("✗ MongoDB: No conecta")
        results['mongodb'] = False
    
    # Redis
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✓ Redis: Conectado")
        results['redis'] = True
    except:
        print("✗ Redis: No conecta")
        results['redis'] = False
    
    # Qdrant
    try:
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print(f"✓ Qdrant: {len(collections.collections)} colecciones")
        results['qdrant'] = True
    except:
        print("✗ Qdrant: No conecta")
        results['qdrant'] = False
    
    return results

def test_model():
    """Test modelo ML32M"""
    print("\n" + "=" * 50)
    print("TEST MODELO ML32M")
    print("=" * 50)
    
    try:
        from fix_ml32m_model import load_ml32m_model_fixed
        
        print("Cargando modelo ML32M...")
        model = load_ml32m_model_fixed()
        
        if model is None:
            print("✗ Error cargando modelo")
            return False
        
        # Estadísticas
        params = sum(p.numel() for p in model.parameters())
        size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**2)
        
        print(f"✓ Modelo cargado")
        print(f"  - Parámetros: {params:,}")
        print(f"  - Tamaño: {size_mb:.1f} MB")
        
        # Test inferencia rápida
        test_input = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        with torch.no_grad():
            _ = model(test_input)
        
        print("✓ Inferencia OK")
        return True
        
    except Exception as e:
        print(f"✗ Error modelo: {e}")
        return False

def main():
    """Test principal"""
    print("SISTEMA ML32M - VERIFICACION FINAL")
    
    # Test infraestructura
    infra_results = test_infrastructure()
    
    # Test modelo
    model_ok = test_model()
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN FINAL")
    print("=" * 50)
    
    total_components = len(infra_results) + 1  # +1 para el modelo
    passed_components = sum(infra_results.values()) + (1 if model_ok else 0)
    
    for component, status in infra_results.items():
        print(f"{component:10}: {'✓' if status else '✗'}")
    
    print(f"{'modelo':10}: {'✓' if model_ok else '✗'}")
    
    print(f"\nResultado: {passed_components}/{total_components} componentes OK")
    
    if passed_components >= 3:  # Necesitamos al menos 3 componentes básicos
        print("\n🎉 SISTEMA LISTO!")
        print("Puedes proceder con:")
        print("1. Iniciar API: python api_v2_ml32m.py")
        print("2. Conversión de datos vectoriales")
        print("3. Pruebas de recomendación")
        return True
    else:
        print("\n⚠️  Sistema no listo")
        print("Verificar componentes antes de continuar")
        return False

if __name__ == "__main__":
    main() 