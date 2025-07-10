import faiss
import numpy as np
import json
import os
from typing import List, Tuple, Dict, Optional

class FAISSIndex:
    def __init__(self, embedding_dim: int = 128, index_type: str = "flat"):
        """
        Inicializa el índice FAISS
        
        Args:
            embedding_dim: Dimensión de los embeddings
            index_type: Tipo de índice ("flat", "ivf", "hnsw")
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.item_mapping = {}
        self.reverse_item_mapping = {}
        
    def create_index(self, embeddings: np.ndarray, item_mapping: Dict[int, int]):
        """
        Crea el índice FAISS con los embeddings de items
        
        Args:
            embeddings: Array de embeddings normalizados (N x embedding_dim)
            item_mapping: Mapeo de índices internos a movieId reales
        """
        self.item_mapping = item_mapping
        self.reverse_item_mapping = {v: k for k, v in item_mapping.items()}
        
        if self.index_type == "flat":
            # IndexFlatIP para similitud coseno (producto interno)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        elif self.index_type == "ivf":
            # IVF con PQ para mejor rendimiento en datasets grandes
            nlist = min(100, len(embeddings) // 10)  # Número de clusters
            quantizer = faiss.IndexFlatIP(self.embedding_dim)
            self.index = faiss.IndexIVFPQ(quantizer, self.embedding_dim, nlist, 8, 8)
            self.index.train(embeddings)
        elif self.index_type == "hnsw":
            # HNSW para búsqueda aproximada rápida
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)  # 32 vecinos
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 100
        
        # Agregar embeddings al índice
        self.index.add(embeddings.astype('float32'))
        
        print(f"Índice FAISS creado con {len(embeddings)} embeddings")
        print(f"Tipo de índice: {self.index_type}")
        
    def search(self, query_embedding: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """
        Busca los k items más similares
        
        Args:
            query_embedding: Embedding de consulta normalizado
            k: Número de recomendaciones a retornar
            
        Returns:
            Tuple de (movie_ids, scores)
        """
        if self.index is None:
            raise ValueError("Índice no inicializado. Llama a create_index() primero.")
        
        # Reshape para FAISS
        query = query_embedding.reshape(1, -1).astype('float32')
        
        # Realizar búsqueda
        scores, indices = self.index.search(query, k)
        
        # Convertir índices internos a movieId reales
        movie_ids = []
        for idx in indices[0]:
            if idx < len(self.item_mapping):
                movie_id = self.item_mapping.get(idx + 1, idx + 1)  # +1 porque los índices empiezan en 1
                movie_ids.append(movie_id)
            else:
                movie_ids.append(-1)  # Índice inválido
        
        return movie_ids, scores[0].tolist()
    
    def batch_search(self, query_embeddings: np.ndarray, k: int = 10) -> List[Tuple[List[int], List[float]]]:
        """
        Búsqueda en lote para múltiples consultas
        
        Args:
            query_embeddings: Array de embeddings de consulta (N x embedding_dim)
            k: Número de recomendaciones por consulta
            
        Returns:
            Lista de tuplas (movie_ids, scores) para cada consulta
        """
        if self.index is None:
            raise ValueError("Índice no inicializado. Llama a create_index() primero.")
        
        # Realizar búsqueda en lote
        scores, indices = self.index.search(query_embeddings.astype('float32'), k)
        
        results = []
        for i in range(len(indices)):
            movie_ids = []
            for idx in indices[i]:
                if idx < len(self.item_mapping):
                    movie_id = self.item_mapping.get(idx + 1, idx + 1)
                    movie_ids.append(movie_id)
                else:
                    movie_ids.append(-1)
            
            results.append((movie_ids, scores[i].tolist()))
        
        return results
    
    def save_index(self, directory: str):
        """Guarda el índice FAISS y los mapeos"""
        os.makedirs(directory, exist_ok=True)
        
        # Guardar índice FAISS
        faiss.write_index(self.index, os.path.join(directory, "faiss_index.bin"))
        
        # Guardar mapeos
        with open(os.path.join(directory, "item_mapping.json"), "w") as f:
            json.dump(self.item_mapping, f)
        
        print(f"Índice FAISS guardado en {directory}")
    
    def load_index(self, directory: str):
        """Carga el índice FAISS y los mapeos"""
        # Cargar índice FAISS
        index_path = os.path.join(directory, "faiss_index.bin")
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        else:
            raise FileNotFoundError(f"Índice FAISS no encontrado en {index_path}")
        
        # Cargar mapeos
        mapping_path = os.path.join(directory, "item_mapping.json")
        if os.path.exists(mapping_path):
            with open(mapping_path, "r") as f:
                self.item_mapping = json.load(f)
            self.reverse_item_mapping = {v: k for k, v in self.item_mapping.items()}
        else:
            raise FileNotFoundError(f"Mapeo de items no encontrado en {mapping_path}")
        
        print(f"Índice FAISS cargado desde {directory}")
    
    def get_index_stats(self) -> Dict:
        """Retorna estadísticas del índice"""
        if self.index is None:
            return {"error": "Índice no inicializado"}
        
        stats = {
            "total_items": self.index.ntotal,
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "is_trained": self.index.is_trained if hasattr(self.index, 'is_trained') else True
        }
        
        return stats

if __name__ == "__main__":
    # Ejemplo de uso
    from embedding_exporter import EmbeddingExporter
    
    # Exportar embeddings
    exporter = EmbeddingExporter("../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt")
    data = exporter.export_embeddings()
    
    # Crear índice FAISS
    faiss_index = FAISSIndex(embedding_dim=128, index_type="flat")
    faiss_index.create_index(data["item_embeddings"], data["item_mapping"])
    
    # Guardar índice
    faiss_index.save_index("faiss_index")
    
    print("Índice FAISS creado y guardado exitosamente") 