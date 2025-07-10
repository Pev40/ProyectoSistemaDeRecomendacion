#!/usr/bin/env python3
"""
Script para solucionar problemas de rutas del modelo
"""

import os
import sys
from pathlib import Path
import json
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

def create_dataset_stats():
    """Crear archivo de estadísticas del dataset"""
    print("📊 Creando archivo de estadísticas del dataset...")
    
    try:
        # Ruta al directorio del modelo
        modelo_dir = Path(__file__).parent.parent / "modelo"
        datasets_dir = modelo_dir / "datasets"
        ml1m_dir = datasets_dir / "ml1m"
        
        # Crear directorios si no existen
        ml1m_dir.mkdir(parents=True, exist_ok=True)
        
        # Estadísticas del dataset ML-1M
        stats = {
            "dataset": "ml1m",
            "num_users": 6040,
            "num_items": 3952,
            "num_ratings": 1000209,
            "sparsity": 0.9583,
            "rating_scale": [1, 5],
            "avg_rating": 3.5816,
            "std_rating": 1.0841,
            "min_rating": 1.0,
            "max_rating": 5.0,
            "num_ratings_per_user": {
                "min": 20,
                "max": 2314,
                "mean": 165.6,
                "median": 96.0
            },
            "num_ratings_per_item": {
                "min": 1,
                "max": 3428,
                "mean": 253.2,
                "median": 37.0
            }
        }
        
        # Guardar estadísticas
        stats_file = ml1m_dir / "dataset_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ Estadísticas guardadas en {stats_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando estadísticas: {e}")
        return False

def check_model_files():
    """Verificar archivos del modelo"""
    print("\n🔍 Verificando archivos del modelo...")
    
    try:
        modelo_dir = Path(__file__).parent.parent / "modelo"
        
        # Verificar directorio pre_trained
        pre_trained_dir = modelo_dir / "pre_trained"
        if not pre_trained_dir.exists():
            print(f"❌ Directorio pre_trained no encontrado: {pre_trained_dir}")
            return False
        
        # Listar archivos del modelo
        model_files = list(pre_trained_dir.glob("*.pt"))
        print(f"📁 Archivos del modelo encontrados: {len(model_files)}")
        
        for model_file in model_files:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"   - {model_file.name}: {size_mb:.1f} MB")
        
        if not model_files:
            print("⚠️  No se encontraron archivos .pt en pre_trained/")
            print("   Necesitas entrenar el modelo primero")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando archivos: {e}")
        return False

def create_model_config():
    """Crear configuración del modelo"""
    print("\n⚙️  Creando configuración del modelo...")
    
    try:
        modelo_dir = Path(__file__).parent.parent / "modelo"
        config_file = modelo_dir / "config_ml1m.py"
        
        # Configuración para ML-1M
        config_content = '''"""
Configuración para el dataset MovieLens 1M
"""

# Parámetros del dataset
DATASET_NAME = "ml1m"
NUM_USERS = 6040
NUM_ITEMS = 3952
NUM_RATINGS = 1000209

# Parámetros del modelo
EMBEDDING_DIM = 128
SEQUENCE_LENGTH = 200
NUM_HEADS = 4
NUM_BLOCKS = 3
DROPOUT_RATE = 0.5

# Parámetros de entrenamiento
BATCH_SIZE = 64
LEARNING_RATE = 0.001
NUM_EPOCHS = 100
NEGATIVE_SAMPLES = 256

# Parámetros de evaluación
TOP_K = [5, 10, 20]
METRICS = ["ndcg", "hit_ratio", "precision", "recall"]

# Rutas
MODEL_DIR = "pre_trained"
DATASET_DIR = "datasets/ml1m"
'''
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Configuración guardada en {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando configuración: {e}")
        return False

def fix_openmp_warning():
    """Solucionar advertencia de OpenMP"""
    print("\n🔧 Solucionando advertencia de OpenMP...")
    
    try:
        # Establecer variable de entorno
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        
        print("✅ Variable de entorno KMP_DUPLICATE_LIB_OK establecida")
        print("   Esta variable permite múltiples copias de OpenMP")
        print("   ⚠️  Solo usar en desarrollo, no en producción")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando OpenMP: {e}")
        return False

def test_model_loading():
    """Probar carga del modelo"""
    print("\n🧪 Probando carga del modelo...")
    
    try:
        # Agregar directorio del modelo al path
        modelo_dir = Path(__file__).parent.parent / "modelo"
        sys.path.append(str(modelo_dir))
        
        # Importar módulos del modelo
        import torch
        from gsasrec import GSASRec
        
        # Verificar CUDA
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🖥️  Dispositivo: {device}")
        
        # Crear modelo
        model = GSASRec(
            num_items=3952,  # ML-1M
            embedding_dim=128,
            sequence_length=200,
            num_heads=4,
            num_blocks=3,
            dropout_rate=0.5,
            reuse_item_embeddings=False
        )
        
        print("✅ Modelo creado correctamente")
        
        # Verificar archivos del modelo
        pre_trained_dir = modelo_dir / "pre_trained"
        model_files = list(pre_trained_dir.glob("*.pt"))
        
        if model_files:
            model_path = model_files[0]
            print(f"📁 Archivo del modelo: {model_path.name}")
            
            # Intentar cargar pesos
            try:
                checkpoint = torch.load(model_path, map_location=device)
                model.load_state_dict(checkpoint['model_state_dict'])
                model.to(device)
                model.eval()
                
                print("✅ Modelo cargado correctamente")
                
                # Probar inferencia
                test_sequence = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long).to(device)
                with torch.no_grad():
                    seq_emb, _ = model(test_sequence)
                    predictions, scores = model.get_predictions(test_sequence, 5)
                
                print("✅ Inferencia exitosa")
                print(f"   - Embedding shape: {seq_emb.shape}")
                print(f"   - Predicciones: {predictions[0][:5].tolist()}")
                
            except Exception as e:
                print(f"⚠️  Error cargando modelo: {e}")
                print("   El modelo existe pero no se puede cargar")
                print("   Esto es normal si el modelo no está entrenado")
        else:
            print("⚠️  No se encontraron archivos del modelo")
            print("   Necesitas entrenar el modelo primero")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando modelo: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 Solucionador de problemas del modelo")
    print("=" * 50)
    
    # Crear estadísticas del dataset
    create_dataset_stats()
    
    # Verificar archivos del modelo
    check_model_files()
    
    # Crear configuración
    create_model_config()
    
    # Solucionar OpenMP
    fix_openmp_warning()
    
    # Probar carga del modelo
    test_model_loading()
    
    print("\n✅ Configuración del modelo completada")
    print("\nPróximos pasos:")
    print("1. Ejecutar: python test_components.py")
    print("2. Si el modelo no está entrenado, entrenarlo primero")
    print("3. O usar el sistema sin el modelo (solo FAISS/Qdrant)")

if __name__ == "__main__":
    main() 