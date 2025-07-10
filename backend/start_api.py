# Script de Inicio para API ML32M Vectorial
import os
import sys
import time
import subprocess
import importlib.util

def check_dependency(package_name, import_name=None):
    """Verifica si una dependencia está instalada"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    return spec is not None

def check_service(host, port, service_name):
    """Verifica si un servicio está corriendo"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def print_section(title):
    """Imprime sección"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def validate_environment():
    """Valida el entorno antes de iniciar"""
    print_section("VALIDANDO ENTORNO")
    
    # Verificar Python
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Se requiere Python 3.8 o superior")
        return False
    
    # Verificar dependencias críticas
    critical_deps = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        ("torch", "torch"),
        ("numpy", "numpy"),
        ("motor", "motor"),
        ("redis", "redis"),
        ("qdrant-client", "qdrant_client"),
        ("requests", "requests")
    ]
    
    print("\n📦 Verificando dependencias:")
    missing_deps = []
    
    for package, import_name in critical_deps:
        if check_dependency(package, import_name):
            print(f"   ✅ {package}")
        else:
            print(f"   ❌ {package} - FALTANTE")
            missing_deps.append(package)
    
    if missing_deps:
        print(f"\n❌ Dependencias faltantes: {', '.join(missing_deps)}")
        print("💡 Instalar con: pip install " + " ".join(missing_deps))
        return False
    
    # Verificar servicios
    print("\n🔌 Verificando servicios:")
    services = [
        ("MongoDB", "localhost", 27017),
        ("Redis", "localhost", 6379),
        ("Qdrant", "localhost", 6333)
    ]
    
    service_issues = []
    for service_name, host, port in services:
        if check_service(host, port, service_name):
            print(f"   ✅ {service_name} ({host}:{port})")
        else:
            print(f"   ⚠️  {service_name} ({host}:{port}) - NO DISPONIBLE")
            service_issues.append(service_name)
    
    if service_issues:
        print(f"\n⚠️ Servicios no disponibles: {', '.join(service_issues)}")
        print("💡 La API funcionará con funcionalidad limitada")
    
    # Verificar archivos críticos
    print("\n📁 Verificando archivos:")
    critical_files = [
        ("database.py", "Servicio de base de datos"),
        ("qdrant_service.py", "Servicio de Qdrant"),
        ("fix_ml32m_model.py", "Cargador de modelo ML32M")
    ]
    
    file_issues = []
    for filename, description in critical_files:
        if os.path.exists(filename):
            print(f"   ✅ {filename} - {description}")
        else:
            print(f"   ❌ {filename} - FALTANTE")
            file_issues.append(filename)
    
    if file_issues:
        print(f"\n❌ Archivos críticos faltantes: {', '.join(file_issues)}")
        return False
    
    print("\n✅ Validación completada - Entorno listo")
    return True

def start_api(host="0.0.0.0", port=8000, reload=True):
    """Inicia la API"""
    print_section("INICIANDO API ML32M VECTORIAL")
    
    try:
        print(f"🚀 Iniciando servidor en http://{host}:{port}")
        print(f"📝 Modo reload: {'Habilitado' if reload else 'Deshabilitado'}")
        print("\n🔗 Endpoints disponibles:")
        print(f"   • Documentación: http://{host}:{port}/docs")
        print(f"   • Health Check: http://{host}:{port}/health")
        print(f"   • Recomendaciones: http://{host}:{port}/recommend")
        print(f"   • Similares: http://{host}:{port}/similar_movies")
        
        print("\n💡 Comandos útiles:")
        print(f"   • Ctrl+C para detener")
        print(f"   • python test_api_endpoints.py para testear")
        
        print("\n" + "="*60)
        
        # Importar y ejecutar
        import uvicorn
        uvicorn.run(
            "api_ml32m_vectorial:app", 
            host=host, 
            port=port, 
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 API detenida por usuario")
    except Exception as e:
        print(f"\n❌ Error iniciando API: {e}")
        return False
    
    return True

def quick_test():
    """Ejecuta una prueba rápida de la API"""
    print_section("PRUEBA RÁPIDA")
    
    try:
        import requests
        import time
        
        base_url = "http://localhost:8000"
        
        print("⏳ Esperando que la API se inicie...")
        time.sleep(3)
        
        # Test básico
        print("🔍 Probando endpoint de salud...")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcionando - Estado: {data.get('status', 'unknown')}")
            
            # Mostrar componentes
            if 'components' in data:
                print("\n📋 Estado de componentes:")
                for comp, status in data['components'].items():
                    print(f"   • {comp}: {status.get('status', 'unknown')}")
            
            return True
        else:
            print(f"❌ API no responde correctamente: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Iniciador para API ML32M Vectorial")
    parser.add_argument("--host", default="0.0.0.0", help="Host para la API")
    parser.add_argument("--port", type=int, default=8000, help="Puerto para la API")
    parser.add_argument("--no-reload", action="store_true", help="Deshabilitar auto-reload")
    parser.add_argument("--skip-validation", action="store_true", help="Omitir validación de entorno")
    parser.add_argument("--test-only", action="store_true", help="Solo ejecutar prueba rápida")
    
    args = parser.parse_args()
    
    print("🎬 INICIADOR API ML32M VECTORIAL")
    print("="*60)
    print(f"⏰ Tiempo: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Solo prueba
    if args.test_only:
        success = quick_test()
        sys.exit(0 if success else 1)
    
    # Validación
    if not args.skip_validation:
        if not validate_environment():
            print("\n❌ Validación falló. Usar --skip-validation para omitir.")
            sys.exit(1)
    
    # Iniciar API
    try:
        success = start_api(
            host=args.host,
            port=args.port,
            reload=not args.no_reload
        )
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Iniciador detenido por usuario")
        sys.exit(0)

if __name__ == "__main__":
    main() 