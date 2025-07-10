import schedule
import time
import threading
import logging
from datetime import datetime
import os
import sys
from pathlib import Path

# Agregar el directorio del modelo al path
sys.path.append(str(Path(__file__).parent.parent / "modelo"))

from embedding_exporter import EmbeddingExporter
from faiss_index import FAISSIndex
from qdrant_service import QdrantService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, model_path: str, sync_interval_hours: int = 6):
        """
        Servicio de sincronización entre FAISS y Qdrant
        
        Args:
            model_path: Ruta al modelo entrenado
            sync_interval_hours: Intervalo de sincronización en horas
        """
        self.model_path = model_path
        self.sync_interval_hours = sync_interval_hours
        self.embedding_exporter = None
        self.faiss_index = None
        self.qdrant_service = None
        self.is_running = False
        
    def initialize_services(self):
        """Inicializa todos los servicios"""
        try:
            logger.info("Inicializando servicios de sincronización...")
            
            # Inicializar exportador de embeddings
            self.embedding_exporter = EmbeddingExporter(self.model_path)
            
            # Inicializar índice FAISS
            self.faiss_index = FAISSIndex(embedding_dim=128, index_type="flat")
            
            # Inicializar servicio Qdrant
            self.qdrant_service = QdrantService()
            
            logger.info("Servicios inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando servicios: {e}")
            raise
    
    def sync_embeddings(self):
        """
        Sincroniza embeddings entre FAISS y Qdrant
        """
        try:
            logger.info("Iniciando sincronización de embeddings...")
            start_time = time.time()
            
            # Exportar embeddings del modelo
            data = self.embedding_exporter.export_embeddings()
            
            # Actualizar índice FAISS
            logger.info("Actualizando índice FAISS...")
            self.faiss_index.create_index(data["item_embeddings"], data["item_mapping"])
            self.faiss_index.save_index("faiss_index")
            
            # Actualizar Qdrant
            logger.info("Actualizando Qdrant...")
            self.qdrant_service.create_collection()
            
            # Cargar metadata de películas
            from qdrant_service import load_movie_metadata
            metadata = load_movie_metadata("../modelo/datasets/ml1m/ml-1m.txt")
            
            # Insertar en Qdrant
            self.qdrant_service.insert_movies(data["item_embeddings"], metadata)
            
            sync_time = time.time() - start_time
            logger.info(f"Sincronización completada en {sync_time:.2f} segundos")
            
            # Registrar métricas
            self._log_metrics()
            
        except Exception as e:
            logger.error(f"Error durante la sincronización: {e}")
    
    def _log_metrics(self):
        """Registra métricas del sistema"""
        try:
            # Estadísticas de FAISS
            faiss_stats = self.faiss_index.get_index_stats()
            logger.info(f"FAISS stats: {faiss_stats}")
            
            # Estadísticas de Qdrant
            qdrant_stats = self.qdrant_service.get_collection_stats()
            logger.info(f"Qdrant stats: {qdrant_stats}")
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
    
    def start_sync_scheduler(self):
        """Inicia el programador de sincronización"""
        try:
            logger.info(f"Programando sincronización cada {self.sync_interval_hours} horas")
            
            # Programar sincronización
            schedule.every(self.sync_interval_hours).hours.do(self.sync_embeddings)
            
            # Sincronización inicial
            logger.info("Ejecutando sincronización inicial...")
            self.sync_embeddings()
            
            self.is_running = True
            
            # Bucle principal
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
                
        except KeyboardInterrupt:
            logger.info("Deteniendo servicio de sincronización...")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error en el programador: {e}")
            self.is_running = False
    
    def stop_sync_scheduler(self):
        """Detiene el programador de sincronización"""
        self.is_running = False
        logger.info("Servicio de sincronización detenido")
    
    def manual_sync(self):
        """Ejecuta una sincronización manual"""
        logger.info("Ejecutando sincronización manual...")
        self.sync_embeddings()

class MonitoringService:
    def __init__(self):
        """Servicio de monitoreo del sistema"""
        self.metrics = {}
    
    def collect_metrics(self):
        """Recopila métricas del sistema"""
        try:
            import psutil
            
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas de archivos
            faiss_size = 0
            if os.path.exists("faiss_index/faiss_index.bin"):
                faiss_size = os.path.getsize("faiss_index/faiss_index.bin") / (1024**2)  # MB
            
            self.metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent
                },
                "storage": {
                    "faiss_index_size_mb": faiss_size
                }
            }
            
            logger.info(f"Métricas recopiladas: CPU={cpu_percent}%, RAM={memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error recopilando métricas: {e}")
    
    def get_metrics(self):
        """Retorna las métricas actuales"""
        return self.metrics

def main():
    """Función principal"""
    try:
        # Configurar ruta del modelo
        model_path = "../modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
        
        # Inicializar servicio de sincronización
        sync_service = SyncService(model_path, sync_interval_hours=6)
        sync_service.initialize_services()
        
        # Inicializar servicio de monitoreo
        monitoring_service = MonitoringService()
        
        # Programar recolección de métricas
        schedule.every(5).minutes.do(monitoring_service.collect_metrics)
        
        logger.info("Servicio de sincronización iniciado")
        logger.info("Presiona Ctrl+C para detener")
        
        # Iniciar sincronización
        sync_service.start_sync_scheduler()
        
    except Exception as e:
        logger.error(f"Error en el servicio principal: {e}")

if __name__ == "__main__":
    main() 