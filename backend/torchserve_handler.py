import os
import json
import torch
import numpy as np
from ts.torch_handler.base_handler import BaseHandler
import sys
from pathlib import Path

# Agregar el directorio del modelo al path
sys.path.append(str(Path(__file__).parent.parent / "modelo"))

from gsasrec import GSASRec
from dataset_utils import get_num_items

class GSASRecHandler(BaseHandler):
    """
    Handler personalizado para el modelo gSASRec en TorchServe
    """
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.device = None
        self.num_items = None
        self.embedding_dim = 128
        
    def initialize(self, context):
        """
        Inicializa el modelo gSASRec
        """
        try:
            # Configurar dispositivo
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Cargar configuración del modelo
            self.num_items = get_num_items("ml1m")
            
            # Crear modelo
            self.model = GSASRec(
                num_items=self.num_items,
                embedding_dim=self.embedding_dim,
                sequence_length=200,
                num_heads=4,
                num_blocks=3,
                dropout_rate=0.5,
                reuse_item_embeddings=False
            )
            
            # Cargar pesos del modelo
            model_path = "/app/modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
            
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                raise FileNotFoundError(f"Modelo no encontrado en {model_path}")
            
            self.model.to(self.device)
            self.model.eval()
            
            self.initialized = True
            print("Modelo gSASRec inicializado correctamente")
            
        except Exception as e:
            print(f"Error inicializando modelo: {e}")
            raise
    
    def preprocess(self, data):
        """
        Preprocesa los datos de entrada
        """
        try:
            # Obtener datos de entrada
            if isinstance(data, list):
                input_data = data[0]
            else:
                input_data = data
            
            # Decodificar JSON si es necesario
            if isinstance(input_data, bytes):
                input_data = input_data.decode('utf-8')
            
            if isinstance(input_data, str):
                input_data = json.loads(input_data)
            
            # Extraer secuencia de usuario y k
            user_sequence = input_data.get("user_sequence", [])
            k = input_data.get("k", 10)
            
            # Validar entrada
            if not user_sequence:
                raise ValueError("Secuencia de usuario vacía")
            
            if k <= 0 or k > 100:
                k = 10
            
            # Convertir a tensor
            sequence_tensor = torch.tensor([user_sequence], dtype=torch.long).to(self.device)
            
            return {
                "sequence": sequence_tensor,
                "k": k,
                "user_sequence": user_sequence
            }
            
        except Exception as e:
            print(f"Error en preprocesamiento: {e}")
            raise
    
    def inference(self, data):
        """
        Realiza la inferencia
        """
        try:
            sequence = data["sequence"]
            k = data["k"]
            
            with torch.no_grad():
                # Obtener embedding del usuario
                seq_emb, _ = self.model(sequence)
                user_embedding = seq_emb[0, -1, :].cpu().numpy()  # Último token
                
                # Normalizar embedding
                user_embedding = user_embedding / np.linalg.norm(user_embedding)
                
                # Obtener predicciones
                predictions, scores = self.model.get_predictions(sequence, k)
                
                # Convertir a lista
                movie_ids = predictions[0].cpu().numpy().tolist()
                scores = scores[0].cpu().numpy().tolist()
                
                return {
                    "user_embedding": user_embedding.tolist(),
                    "recommendations": [
                        {
                            "movie_id": int(movie_id),
                            "score": float(score)
                        }
                        for movie_id, score in zip(movie_ids, scores)
                    ]
                }
                
        except Exception as e:
            print(f"Error en inferencia: {e}")
            raise
    
    def handle(self, data, context):
        """
        Maneja la solicitud completa
        """
        try:
            # Preprocesamiento
            preprocessed_data = self.preprocess(data)
            
            # Inferencia
            result = self.inference(preprocessed_data)
            
            # Postprocesamiento
            return self.postprocess(result)
            
        except Exception as e:
            print(f"Error en handler: {e}")
            return [{"error": str(e)}]
    
    def postprocess(self, data):
        """
        Postprocesa los resultados
        """
        try:
            # Convertir a formato JSON
            return [data]
            
        except Exception as e:
            print(f"Error en postprocesamiento: {e}")
            return [{"error": str(e)}]

# Instancia del handler
_handler = GSASRecHandler()

def handle(data, context):
    """
    Función principal para TorchServe
    """
    return _handler.handle(data, context) 