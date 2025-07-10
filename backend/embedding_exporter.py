import torch
import numpy as np
import json
import os
import sys
from pathlib import Path

# Agregar el directorio del modelo al path
sys.path.append(str(Path(__file__).parent.parent / "modelo"))

from gsasrec import GSASRec
from dataset_utils import get_num_items

class EmbeddingExporter:
    def __init__(self, model_path, dataset_name="ml1m", embedding_dim=128):
        self.model_path = model_path
        self.dataset_name = dataset_name
        self.embedding_dim = embedding_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Cargar estadísticas del dataset
        self.num_items = get_num_items(dataset_name)
        self.num_users = 6040  # Para ML-1M
        
        # Cargar el modelo
        self.model = self._load_model()
        
    def _load_model(self):
        """Carga el modelo gSASRec desde el checkpoint"""
        model = GSASRec(
            num_items=self.num_items,
            embedding_dim=self.embedding_dim,
            sequence_length=200,
            num_heads=4,
            num_blocks=3,
            dropout_rate=0.5,
            reuse_item_embeddings=False
        )
        
        # Cargar los pesos del modelo
        checkpoint = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        
        return model
    
    def extract_item_embeddings(self):
        """Extrae los embeddings de items del modelo"""
        with torch.no_grad():
            # Obtener embeddings de items (excluyendo padding y mask tokens)
            item_embeddings = self.model.get_output_embeddings().weight[1:self.num_items+1].cpu().numpy()
            
            # Normalizar para similitud coseno
            item_embeddings = item_embeddings / np.linalg.norm(item_embeddings, axis=1, keepdims=True)
            
            return item_embeddings
    
    def extract_user_embeddings(self, user_sequences):
        """Extrae embeddings de usuarios basados en sus secuencias"""
        user_embeddings = []
        
        with torch.no_grad():
            for user_seq in user_sequences:
                # Convertir secuencia a tensor
                seq_tensor = torch.tensor([user_seq], dtype=torch.long).to(self.device)
                
                # Obtener embedding del usuario
                seq_emb, _ = self.model(seq_tensor)
                user_emb = seq_emb[0, -1, :].cpu().numpy()  # Último token de la secuencia
                
                # Normalizar
                user_emb = user_emb / np.linalg.norm(user_emb)
                user_embeddings.append(user_emb)
        
        return np.array(user_embeddings)
    
    def create_item_mapping(self):
        """Crea mapeo de índices internos a movieId reales"""
        # Para ML-1M, los movieId van de 1 a 3952
        # Pero el modelo usa índices de 1 a num_items
        item_mapping = {}
        for i in range(1, self.num_items + 1):
            item_mapping[i] = i  # En este caso, el mapeo es directo
        
        return item_mapping
    
    def create_user_mapping(self):
        """Crea mapeo de índices internos a userId reales"""
        user_mapping = {}
        for i in range(1, self.num_users + 1):
            user_mapping[i] = i  # En este caso, el mapeo es directo
        
        return user_mapping
    
    def export_embeddings(self, output_dir="embeddings"):
        """Exporta todos los embeddings y mapeos"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Extraer embeddings de items
        print("Extrayendo embeddings de items...")
        item_embeddings = self.extract_item_embeddings()
        
        # Crear mapeos
        item_mapping = self.create_item_mapping()
        user_mapping = self.create_user_mapping()
        
        # Guardar embeddings y mapeos
        np.save(os.path.join(output_dir, "item_embeddings.npy"), item_embeddings)
        
        with open(os.path.join(output_dir, "item_mapping.json"), "w") as f:
            json.dump(item_mapping, f)
        
        with open(os.path.join(output_dir, "user_mapping.json"), "w") as f:
            json.dump(user_mapping, f)
        
        print(f"Embeddings exportados a {output_dir}")
        print(f"Dimensiones de embeddings de items: {item_embeddings.shape}")
        
        return {
            "item_embeddings": item_embeddings,
            "item_mapping": item_mapping,
            "user_mapping": user_mapping
        }

if __name__ == "__main__":
    # Usar el mejor modelo entrenado
    model_path = "../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
    
    exporter = EmbeddingExporter(model_path)
    exporter.export_embeddings() 