#!/usr/bin/env python3
"""
Script para verificar los datos almacenados en las colecciones de Qdrant
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import json
from typing import Dict, Any

def check_qdrant_collections():
    """
    Verifica el estado de las colecciones de Qdrant y muestra estadísticas
    """
    try:
        # Conectar a Qdrant
        print("🔍 Conectando a Qdrant en localhost:6333...")
        client = QdrantClient(host="localhost", port=6333)
        
        # Obtener lista de colecciones
        collections = client.get_collections()
        print(f"\n📊 ESTADÍSTICAS DE COLECCIONES QDRANT")
        print("=" * 60)
        
        # Colecciones objetivo
        target_collections = ["movie_embeddings", "user_embeddings", "sequence_embeddings"]
        
        for collection_name in target_collections:
            print(f"\n🗂️  COLECCIÓN: '{collection_name}'")
            print("-" * 40)
            
            # Verificar si la colección existe
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                print(f"   ❌ La colección '{collection_name}' NO EXISTE")
                continue
            
            try:
                # Obtener información de la colección
                collection_info = client.get_collection(collection_name)
                
                print(f"   ✅ Estado: EXISTE")
                print(f"   📈 Número de puntos: {collection_info.points_count:,}")
                print(f"   🎯 Número de vectores: {collection_info.vectors_count:,}")
                print(f"   📏 Dimensión de vectores: {collection_info.config.params.vectors.size}")
                print(f"   📐 Métrica de distancia: {collection_info.config.params.vectors.distance}")
                
                # Si hay datos, mostrar una muestra
                if collection_info.points_count > 0:
                    print(f"   ✨ CONTIENE DATOS: SÍ ({collection_info.points_count:,} puntos)")
                    
                    # Obtener algunos puntos de muestra
                    try:
                        sample_points = client.scroll(
                            collection_name=collection_name,
                            limit=3,
                            with_payload=True,
                            with_vectors=False
                        )[0]
                        
                        if sample_points:
                            print(f"   📋 Muestra de metadatos:")
                            for i, point in enumerate(sample_points[:2], 1):
                                print(f"      {i}. ID: {point.id}")
                                if point.payload:
                                    # Mostrar algunas claves del payload
                                    payload_keys = list(point.payload.keys())[:3]
                                    print(f"         Metadatos: {payload_keys}")
                                    
                    except Exception as e:
                        print(f"   ⚠️  No se pudo obtener muestra: {e}")
                        
                else:
                    print(f"   ⚠️  CONTIENE DATOS: NO (colección vacía)")
                    
            except Exception as e:
                print(f"   ❌ Error obteniendo información: {e}")
        
        print(f"\n" + "=" * 60)
        print("✅ Verificación completada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Qdrant: {e}")
        print("💡 Asegúrate de que Qdrant esté ejecutándose en localhost:6333")
        print("   Puedes iniciarlo con: docker run -p 6333:6333 qdrant/qdrant")
        return False

def check_collection_details(collection_name: str):
    """
    Obtiene detalles específicos de una colección
    """
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        print(f"\n🔍 DETALLES DE LA COLECCIÓN: '{collection_name}'")
        print("=" * 50)
        
        collection_info = client.get_collection(collection_name)
        
        # Información básica
        print(f"Puntos totales: {collection_info.points_count:,}")
        print(f"Vectores totales: {collection_info.vectors_count:,}")
        print(f"Dimensión: {collection_info.config.params.vectors.size}")
        print(f"Distancia: {collection_info.config.params.vectors.distance}")
        
        # Configuración del índice
        print(f"\nConfiguración HNSW:")
        hnsw = collection_info.config.hnsw_config
        print(f"  - M: {hnsw.m}")
        print(f"  - EF Construct: {hnsw.ef_construct}")
        print(f"  - En disco: {hnsw.on_disk}")
        
        # Obtener algunos ejemplos de puntos
        if collection_info.points_count > 0:
            print(f"\n📋 Ejemplos de puntos:")
            points = client.scroll(
                collection_name=collection_name,
                limit=5,
                with_payload=True,
                with_vectors=False
            )[0]
            
            for i, point in enumerate(points, 1):
                print(f"  {i}. ID: {point.id}")
                if point.payload:
                    print(f"     Metadatos: {json.dumps(point.payload, indent=6)}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 VERIFICADOR DE DATOS QDRANT")
    print("=" * 60)
    
    # Verificar todas las colecciones
    success = check_qdrant_collections()
    
    if success:
        print(f"\n💡 Para ver detalles de una colección específica:")
        print(f"   python check_qdrant_data.py <nombre_coleccion>") 