#!/usr/bin/env python3
"""
Script para cargar el modelo correctamente
"""

import torch
import os
import sys
from pathlib import Path

# Solucionar advertencia de OpenMP
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Agregar el directorio del modelo al path
sys.path.append(str(Path(__file__).parent.parent / "modelo"))

def load_model(model_path="gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"):
    """Cargar modelo correctamente"""
    print(f"Cargando modelo: {model_path}")
    
    try:
        from gsasrec import GSASRec
        
        # Cargar checkpoint primero para obtener el número correcto de items
        full_path = f"../modelo/pre_trained/{model_path}"
        checkpoint = torch.load(full_path, map_location='cpu')
        
        # Obtener el número de items del checkpoint
        num_items = checkpoint['item_embedding.weight'].shape[0]
        print(f"Numero de items en checkpoint: {num_items}")
        
        # Crear modelo con el número correcto de items
        model = GSASRec(
            num_items=num_items,  # Usar el número exacto del checkpoint
            embedding_dim=128,
            sequence_length=200,
            num_heads=4,
            num_blocks=2,  # Según el checkpoint
            dropout_rate=0.5,
            reuse_item_embeddings=False
        )
        
        print("Checkpoint cargado correctamente")
        print(f"Claves en checkpoint: {list(checkpoint.keys())[:5]}...")
        
        # Cargar state_dict directo
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

def test_both_models():
    """Probar ambos modelos"""
    print("Probando ambos modelos...")
    
    # Modelos disponibles
    models = [
        "gsasrec-ml1m-step_47520-t_0.0-negs_1-emb_128-dropout_0.5-metric_0.1428058429831465.pt",  # SASRec
        "gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"  # gSASRec
    ]
    
    results = {}
    
    for model_path in models:
        print(f"\n{'='*50}")
        print(f"Probando: {model_path}")
        print(f"{'='*50}")
        
        model = load_model(model_path)
        if model is not None:
            results[model_path] = True
            print("✓ Modelo cargado exitosamente")
        else:
            results[model_path] = False
            print("✗ Error cargando modelo")
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN")
    print(f"{'='*50}")
    
    for model_path, success in results.items():
        status = "OK" if success else "ERROR"
        print(f"{model_path[:30]:<30} {status}")
    
    # Recomendación
    working_models = [path for path, success in results.items() if success]
    
    if working_models:
        recommended = working_models[0]  # Usar el primero que funcione
        print(f"\nRECOMENDACIÓN: Usar {recommended}")
        print("  - Modelo cargado correctamente")
        print("  - Listo para usar en el sistema")
    else:
        print("\nRECOMENDACIÓN: Usar sistema sin modelo")
        print("  - Solo FAISS/Qdrant")
        print("  - Funciona para recomendaciones básicas")

def main():
    """Función principal"""
    print("Cargador de modelos gSASRec")
    print("=" * 50)
    
    test_both_models()

if __name__ == "__main__":
    main() 