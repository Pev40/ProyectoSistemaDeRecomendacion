#!/usr/bin/env python3
"""
Script de inicio rápido con todos los fixes
"""

import subprocess
import sys
import os
from pathlib import Path
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

def run_script(script_name, description):
    """Ejecutar un script y mostrar el resultado"""
    print(f"\n🔧 {description}...")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Completado exitosamente")
            if result.stdout:
                print(result.stdout)
        else:
            print("⚠️  Completado con advertencias")
            if result.stderr:
                print(result.stderr)
        
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando {script_name}: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Inicio rápido con fixes")
    print("=" * 50)
    
    # Solucionar problemas del modelo
    run_script("fix_model_paths.py", "Solucionando problemas del modelo")
    
    # Crear colección de Qdrant
    run_script("create_qdrant_collection.py", "Creando colección de Qdrant")
    
    # Cargar datos de prueba
    run_script("load_test_data.py", "Cargando datos de prueba")
    
    # Probar componentes
    run_script("test_components.py", "Probando componentes")
    
    print("\n" + "=" * 50)
    print("✅ Fixes aplicados")
    print("\nPróximos pasos:")
    print("1. Iniciar API: uvicorn api_v2:app --host 0.0.0.0 --port 8000 --reload")
    print("2. Probar API: python test_api.py")
    print("3. O usar inicio automático: python start_step_by_step.py")

if __name__ == "__main__":
    main() 