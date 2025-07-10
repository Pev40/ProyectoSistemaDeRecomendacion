#!/usr/bin/env python3
"""
Script para inspeccionar el contenido del archivo del modelo
"""

import torch
import os
from pathlib import Path

def inspect_model_file():
    """Inspeccionar el archivo del modelo"""
    print("Inspeccionando archivo del modelo...")
    
    # Ruta al archivo del modelo
    model_path = "../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
    
    if not os.path.exists(model_path):
        print(f"ERROR: Archivo no encontrado: {model_path}")
        return
    
    print(f"Archivo encontrado: {model_path}")
    
    # Obtener tamaño del archivo
    file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    print(f"Tamaño del archivo: {file_size:.2f} MB")
    
    try:
        # Cargar el checkpoint
        checkpoint = torch.load(model_path, map_location='cpu')
        
        print("\nEstructura del checkpoint:")
        print("=" * 40)
        
        if isinstance(checkpoint, dict):
            for key in checkpoint.keys():
                if isinstance(checkpoint[key], torch.Tensor):
                    print(f"  {key}: Tensor {list(checkpoint[key].shape)}")
                elif isinstance(checkpoint[key], dict):
                    print(f"  {key}: Dict con {len(checkpoint[key])} elementos")
                else:
                    print(f"  {key}: {type(checkpoint[key])} = {checkpoint[key]}")
        else:
            print(f"Checkpoint no es un dict: {type(checkpoint)}")
            print(f"Contenido: {checkpoint}")
        
        # Verificar si tiene model_state_dict
        if 'model_state_dict' in checkpoint:
            print("\nOK: model_state_dict encontrado")
            state_dict = checkpoint['model_state_dict']
            print(f"  Número de parámetros: {len(state_dict)}")
            
            # Mostrar algunos parámetros
            print("\nPrimeros 10 parámetros:")
            for i, (name, param) in enumerate(state_dict.items()):
                if i < 10:
                    print(f"  {name}: {list(param.shape)}")
                else:
                    break
        else:
            print("\nWARNING: model_state_dict no encontrado")
            print("Claves disponibles:")
            for key in checkpoint.keys():
                print(f"  - {key}")
        
        # Verificar otras claves comunes
        common_keys = ['epoch', 'optimizer_state_dict', 'loss', 'accuracy', 'step']
        print("\nVerificando claves comunes:")
        for key in common_keys:
            if key in checkpoint:
                print(f"  {key}: {checkpoint[key]}")
            else:
                print(f"  {key}: No encontrado")
                
    except Exception as e:
        print(f"ERROR: Error cargando modelo: {e}")
        print("Esto puede indicar que el archivo está corrupto o en formato incorrecto")

def try_load_model():
    """Intentar cargar el modelo de diferentes maneras"""
    print("\nIntentando cargar modelo...")
    
    model_path = "../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
    
    try:
        # Método 1: Cargar como checkpoint completo
        checkpoint = torch.load(model_path, map_location='cpu')
        
        if 'model_state_dict' in checkpoint:
            print("OK: Método 1 - model_state_dict encontrado")
            return True
        elif 'state_dict' in checkpoint:
            print("OK: Método 2 - state_dict encontrado")
            return True
        elif isinstance(checkpoint, dict) and any('weight' in key or 'bias' in key for key in checkpoint.keys()):
            print("OK: Método 3 - state_dict directo")
            return True
        else:
            print("WARNING: No se pudo identificar la estructura del modelo")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def create_simple_model():
    """Crear un modelo simple para pruebas"""
    print("\nCreando modelo simple para pruebas...")
    
    try:
        from gsasrec import GSASRec
        
        # Crear modelo
        model = GSASRec(
            num_items=3952,
            embedding_dim=128,
            sequence_length=200,
            num_heads=4,
            num_blocks=3,
            dropout_rate=0.5,
            reuse_item_embeddings=False
        )
        
        print("OK: Modelo creado correctamente")
        
        # Probar inferencia
        test_sequence = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
        with torch.no_grad():
            seq_emb, _ = model(test_sequence)
            predictions, scores = model.get_predictions(test_sequence, 5)
        
        print("OK: Inferencia exitosa")
        print(f"  - Embedding shape: {seq_emb.shape}")
        print(f"  - Predicciones: {predictions[0][:5].tolist()}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error creando modelo: {e}")
        return False

def main():
    """Función principal"""
    print("Inspector de modelo gSASRec")
    print("=" * 40)
    
    # Inspeccionar archivo
    inspect_model_file()
    
    # Intentar cargar modelo
    try_load_model()
    
    # Crear modelo simple
    create_simple_model()
    
    print("\nRecomendaciones:")
    print("1. Si el modelo no está entrenado, el sistema puede funcionar sin él")
    print("2. Usar solo FAISS/Qdrant para recomendaciones")
    print("3. O entrenar el modelo primero")

if __name__ == "__main__":
    main() 