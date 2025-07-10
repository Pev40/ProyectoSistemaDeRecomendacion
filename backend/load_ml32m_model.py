#!/usr/bin/env python3
"""
Script para cargar el modelo ML32M actualizado
"""

import torch
import os
import sys
from pathlib import Path

# Solucionar advertencia de OpenMP
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Agregar el directorio del modelo al path
sys.path.append(str(Path(__file__).parent.parent / "modelo"))

def load_ml32m_model():
    """Cargar modelo ML32M actualizado"""
    print("Cargando modelo ML32M actualizado...")
    
    try:
        from gsasrec import GSASRec
        
        # Ruta al modelo ML32M
        model_path = "../modelo/models/gsasrec-ml32m-step_88576-t_0.75-negs_16-emb_256-dropout_0.2-metric_0.126124.pt"
        
        if not os.path.exists(model_path):
            print(f"ERROR: Modelo no encontrado en {model_path}")
            return None
        
        # Obtener tamaño del archivo
        file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        print(f"Tamaño del modelo: {file_size:.2f} MB")
        
        # Cargar checkpoint primero para obtener parámetros
        checkpoint = torch.load(model_path, map_location='cpu')
        
        # Obtener parámetros del checkpoint
        num_items = checkpoint['item_embedding.weight'].shape[0]
        embedding_dim = checkpoint['item_embedding.weight'].shape[1]
        
        # Contar bloques transformer
        num_blocks = 0
        for key in checkpoint.keys():
            if 'transformer_blocks.' in key and '.first_norm.weight' in key:
                num_blocks += 1
        
        print(f"Parámetros detectados:")
        print(f"  - Numero de items: {num_items}")
        print(f"  - Embedding dim: {embedding_dim}")
        print(f"  - Numero de bloques: {num_blocks}")
        
        # Crear modelo con parámetros correctos
        model = GSASRec(
            num_items=num_items,
            embedding_dim=embedding_dim,
            sequence_length=200,
            num_heads=8,  # Según config_ml32m.py
            num_blocks=num_blocks,
            dropout_rate=0.2,  # Según config_ml32m.py
            reuse_item_embeddings=False
        )
        
        print("Modelo creado correctamente")
        
        # Cargar state_dict
        model.load_state_dict(checkpoint)
        
        print("OK: Modelo cargado correctamente")
        
        # Mover a CPU para pruebas
        model.to('cpu')
        model.eval()
        
        # Probar inferencia
        test_sequence = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        with torch.no_grad():
            seq_emb, _ = model(test_sequence)
            predictions, scores = model.get_predictions(test_sequence, 5)
        
        print("OK: Inferencia exitosa")
        print(f"  - Embedding shape: {seq_emb.shape}")
        print(f"  - Predicciones: {predictions[0][:5].tolist()}")
        
        return model
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_model_performance():
    """Probar rendimiento del modelo"""
    print("\nProbando rendimiento del modelo...")
    
    model = load_ml32m_model()
    if model is None:
        return
    
    try:
        import time
        
        # Probar velocidad de inferencia
        test_sequences = torch.randint(1, 1000, (10, 200))  # 10 secuencias de 200 items
        
        start_time = time.time()
        with torch.no_grad():
            for i in range(10):
                seq_emb, _ = model(test_sequences[i:i+1])
                predictions, scores = model.get_predictions(test_sequences[i:i+1], 10)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        print(f"Rendimiento:")
        print(f"  - Tiempo promedio por inferencia: {avg_time:.4f} segundos")
        print(f"  - Inferencias por segundo: {1/avg_time:.2f}")
        
    except Exception as e:
        print(f"ERROR en prueba de rendimiento: {e}")

def main():
    """Función principal"""
    print("Cargador de modelo ML32M")
    print("=" * 50)
    
    # Cargar modelo
    model = load_ml32m_model()
    
    if model is not None:
        print("\n✓ Modelo ML32M cargado exitosamente")
        print("  - Listo para usar en el sistema")
        print("  - Parámetros actualizados para ML32M")
        
        # Probar rendimiento
        test_model_performance()
        
        print("\nPróximos pasos:")
        print("1. Actualizar api_v2.py para usar este modelo")
        print("2. Actualizar configuración de la base de datos")
        print("3. Probar el sistema completo")
    else:
        print("\n✗ Error cargando modelo")
        print("  - Verificar que el archivo existe")
        print("  - Verificar que los parámetros son correctos")

if __name__ == "__main__":
    main() 