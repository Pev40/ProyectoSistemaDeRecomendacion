#!/usr/bin/env python3
"""
Script simple para verificar Qdrant sin problemas de versión de API
"""

from qdrant_client import QdrantClient

def check_qdrant_simple():
    """Verificación simple de Qdrant"""
    try:
        print("🔍 VERIFICACIÓN SIMPLE DE QDRANT")
        print("=" * 50)
        
        # Conectar
        client = QdrantClient(host="localhost", port=6333)
        
        # Listar colecciones
        collections = client.get_collections()
        print(f"✅ Qdrant conectado exitosamente")
        print(f"📂 Colecciones encontradas: {len(collections.collections)}")
        
        for col in collections.collections:
            print(f"   • {col.name}")
            
            # Intentar obtener información básica
            try:
                # Usar scroll para contar puntos de forma confiable
                result = client.scroll(
                    collection_name=col.name,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                
                # Contar total de puntos
                total_points = 0
                offset = None
                
                while True:
                    result = client.scroll(
                        collection_name=col.name,
                        limit=100,
                        offset=offset,
                        with_payload=False,
                        with_vectors=False
                    )
                    
                    points, next_offset = result
                    total_points += len(points)
                    
                    if next_offset is None:
                        break
                    offset = next_offset
                
                print(f"     📊 Puntos: {total_points:,}")
                
            except Exception as e:
                print(f"     ❌ Error obteniendo stats: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ No se puede conectar a Qdrant: {e}")
        print("💡 Verificaciones:")
        print("   1. ¿Está Qdrant ejecutándose?")
        print("   2. ¿Está en el puerto 6333?")
        print("   3. Intenta: docker run -p 6333:6333 qdrant/qdrant")
        return False

if __name__ == "__main__":
    check_qdrant_simple() 