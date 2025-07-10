#!/usr/bin/env python3
"""
Script principal para ejecutar el sistema de recomendación completo
"""

import os
import sys
import subprocess
import time
import signal
import argparse
from pathlib import Path

def print_banner():
    """Imprime el banner del sistema"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    Sistema de Recomendación gSASRec + FAISS + Qdrant       ║
║                                                              ║
║    Backend escalable para recomendaciones de películas      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def check_system_requirements():
    """Verifica los requisitos del sistema"""
    print("🔍 Verificando requisitos del sistema...")
    
    # Verificar directorios necesarios
    required_dirs = ["modelo", "backend"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ Directorio '{dir_name}' no encontrado")
            return False
    
    # Verificar modelo entrenado
    model_path = "modelo/pre_trained/gsasrec-ml1m-step_86064-t_0.75-negs_256-emb_128-dropout_0.5-metric_0.1974453226738962.pt"
    if not os.path.exists(model_path):
        print(f"❌ Modelo no encontrado en {model_path}")
        return False
    
    print("✅ Requisitos del sistema verificados")
    return True

def start_qdrant():
    """Inicia el servicio Qdrant"""
    print("🚀 Iniciando Qdrant...")
    
    try:
        # Verificar si Qdrant ya está ejecutándose
        result = subprocess.run(["docker", "ps", "--filter", "name=qdrant"], 
                              capture_output=True, text=True)
        
        if "qdrant" in result.stdout:
            print("✅ Qdrant ya está ejecutándose")
            return True
        
        # Iniciar Qdrant
        subprocess.run([
            "docker", "run", "-d", "--name", "qdrant",
            "-p", "6333:6333", "-p", "6334:6334",
            "-v", "qdrant_storage:/qdrant/storage",
            "qdrant/qdrant:latest"
        ], check=True)
        
        print("⏳ Esperando a que Qdrant esté listo...")
        time.sleep(10)
        
        print("✅ Qdrant iniciado correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error iniciando Qdrant: {e}")
        return False

def run_backend():
    """Ejecuta el backend"""
    print("🚀 Iniciando backend...")
    
    try:
        # Cambiar al directorio backend
        os.chdir("backend")
        
        # Ejecutar el backend
        process = subprocess.Popen([sys.executable, "api.py"])
        
        print("✅ Backend iniciado correctamente")
        print("📊 API disponible en: http://localhost:8000")
        print("📚 Documentación en: http://localhost:8000/docs")
        
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando backend: {e}")
        return None

def run_sync_service():
    """Ejecuta el servicio de sincronización"""
    print("🔄 Iniciando servicio de sincronización...")
    
    try:
        # Cambiar al directorio backend
        os.chdir("backend")
        
        # Ejecutar el servicio de sincronización
        process = subprocess.Popen([sys.executable, "sync_service.py"])
        
        print("✅ Servicio de sincronización iniciado")
        
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando servicio de sincronización: {e}")
        return None

def test_api():
    """Prueba la API"""
    print("🧪 Probando la API...")
    
    try:
        import requests
        
        # Esperar a que la API esté lista
        time.sleep(5)
        
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ API funcionando correctamente")
            return True
        else:
            print(f"❌ API respondió con código {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando a la API: {e}")
        return False
    except ImportError:
        print("⚠️  requests no instalado, saltando prueba de API")
        return True

def print_usage_instructions():
    """Imprime instrucciones de uso"""
    print("""
📖 INSTRUCCIONES DE USO:

1. **Probar la API:**
   curl http://localhost:8000/health

2. **Obtener recomendaciones rápidas:**
   curl -X POST "http://localhost:8000/recommend_fast" \\
     -H "Content-Type: application/json" \\
     -d '{"user_id": 1, "k": 10}'

3. **Obtener recomendaciones con filtros:**
   curl -X POST "http://localhost:8000/recommend_filter" \\
     -H "Content-Type: application/json" \\
     -d '{"user_id": 1, "k": 10, "filters": {"genres": ["Action"]}}'

4. **Recomendaciones en lote:**
   curl -X POST "http://localhost:8000/recommend_batch" \\
     -H "Content-Type: application/json" \\
     -d '{"user_ids": [1, 2, 3], "k": 5}'

5. **Actualizar usuario:**
   curl -X POST "http://localhost:8000/update_user" \\
     -H "Content-Type: application/json" \\
     -d '{"user_id": 1, "movie_id": 123, "rating": 4.5}'

6. **Ver estadísticas:**
   curl http://localhost:8000/stats

📚 Documentación completa: http://localhost:8000/docs
""")

def signal_handler(signum, frame):
    """Maneja señales de interrupción"""
    print("\n🛑 Deteniendo el sistema...")
    
    # Detener procesos
    try:
        subprocess.run(["docker", "stop", "qdrant"], check=False)
        subprocess.run(["docker", "rm", "qdrant"], check=False)
    except:
        pass
    
    print("✅ Sistema detenido")
    sys.exit(0)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Sistema de Recomendación gSASRec")
    parser.add_argument("--mode", choices=["docker", "local"], default="local",
                       help="Modo de ejecución (docker o local)")
    parser.add_argument("--setup", action="store_true",
                       help="Ejecutar setup automático")
    parser.add_argument("--test", action="store_true",
                       help="Ejecutar tests después del inicio")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.mode == "docker":
        print("🐳 Ejecutando en modo Docker...")
        
        if args.setup:
            print("🔧 Ejecutando setup...")
            subprocess.run(["python", "backend/setup.py"], check=True)
        
        print("🚀 Iniciando con Docker Compose...")
        subprocess.run(["docker-compose", "up", "--build"])
        
    else:
        print("💻 Ejecutando en modo local...")
        
        if args.setup:
            print("🔧 Ejecutando setup...")
            subprocess.run(["python", "backend/setup.py"], check=True)
        
        # Verificar requisitos
        if not check_system_requirements():
            print("❌ Requisitos del sistema no cumplidos")
            return 1
        
        # Iniciar Qdrant
        if not start_qdrant():
            print("❌ Error iniciando Qdrant")
            return 1
        
        # Ejecutar backend
        backend_process = run_backend()
        if not backend_process:
            print("❌ Error iniciando backend")
            return 1
        
        # Ejecutar servicio de sincronización
        sync_process = run_sync_service()
        if not sync_process:
            print("⚠️  Error iniciando servicio de sincronización")
        
        # Probar API
        if args.test:
            if test_api():
                print_usage_instructions()
            else:
                print("❌ Error probando API")
        
        print("\n🎉 Sistema iniciado correctamente!")
        print("Presiona Ctrl+C para detener")
        
        try:
            # Mantener el sistema ejecutándose
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo el sistema...")
            
            # Detener procesos
            if backend_process:
                backend_process.terminate()
            if sync_process:
                sync_process.terminate()
            
            # Detener Qdrant
            try:
                subprocess.run(["docker", "stop", "qdrant"], check=False)
                subprocess.run(["docker", "rm", "qdrant"], check=False)
            except:
                pass
            
            print("✅ Sistema detenido")

if __name__ == "__main__":
    sys.exit(main()) 