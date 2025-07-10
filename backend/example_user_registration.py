#!/usr/bin/env python3
"""
Ejemplo de uso del Sistema de Registro de Usuarios
==================================================

Este script demuestra cómo usar los nuevos endpoints para:
1. Registrar un usuario
2. Obtener géneros disponibles
3. Obtener películas en tendencia
4. Configurar preferencias detalladas
5. Obtener recomendaciones personalizadas

Uso:
    python example_user_registration.py
"""

import requests
import json
import time

# Configuración de la API
API_BASE = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """Imprime una respuesta de la API de forma formateada"""
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)

def main():
    """Función principal que demuestra el flujo completo"""
    
    print("🎬 Demostración del Sistema de Registro de Usuarios")
    print("=" * 60)
    
    # 1. Obtener géneros disponibles
    print("\n1️⃣ Obteniendo géneros disponibles...")
    response = requests.get(f"{API_BASE}/genres")
    print_response("Géneros Disponibles", response)
    
    if response.status_code != 200:
        print("❌ Error obteniendo géneros. Verificar que la API esté ejecutándose.")
        return
    
    genres = response.json()["genres"]
    
    # 2. Obtener películas en tendencia
    print("\n2️⃣ Obteniendo películas en tendencia por género...")
    response = requests.get(f"{API_BASE}/trending_movies?limit_per_genre=5")
    print_response("Películas en Tendencia", response)
    
    # 3. Registrar un nuevo usuario
    print("\n3️⃣ Registrando nuevo usuario...")
    user_data = {
        "username": "usuario_demo",
        "email": f"demo_{int(time.time())}@ejemplo.com",  # Email único
        "preferred_genres": ["Action", "Comedy", "Sci-Fi"],
        "age_range": "young_adult",
        "country": "España"
    }
    
    response = requests.post(f"{API_BASE}/register_user", json=user_data)
    print_response("Registro de Usuario", response)
    
    if response.status_code != 200:
        print("❌ Error registrando usuario.")
        return
    
    user_id = response.json()["user_id"]
    print(f"\n✅ Usuario registrado con ID: {user_id}")
    
    # 4. Configurar preferencias detalladas
    print("\n4️⃣ Configurando preferencias detalladas...")
    
    # Simular selección de películas por género
    preferences_data = {
        "user_id": user_id,
        "movies_by_genre": {
            "Action": [1, 2, 3],  # IDs de películas de acción seleccionadas
            "Comedy": [4, 5, 6],  # IDs de películas de comedia seleccionadas
            "Sci-Fi": [7, 8, 9]   # IDs de películas de sci-fi seleccionadas
        }
    }
    
    response = requests.post(f"{API_BASE}/set_preferences", json=preferences_data)
    print_response("Configuración de Preferencias", response)
    
    # 5. Obtener perfil del usuario
    print("\n5️⃣ Obteniendo perfil del usuario...")
    response = requests.get(f"{API_BASE}/user_profile/{user_id}")
    print_response("Perfil de Usuario", response)
    
    # 6. Obtener recomendaciones personalizadas
    print("\n6️⃣ Obteniendo recomendaciones personalizadas...")
    recommendation_data = {
        "user_id": user_id,
        "k": 10,
        "method": "vectorial"
    }
    
    response = requests.post(f"{API_BASE}/recommend", json=recommendation_data)
    print_response("Recomendaciones Personalizadas", response)
    
    # 7. Verificar estado del sistema
    print("\n7️⃣ Verificando estado del sistema...")
    response = requests.get(f"{API_BASE}/health")
    print_response("Estado del Sistema", response)
    
    print(f"\n🎉 Demostración completada exitosamente!")
    print(f"Usuario creado: {user_id}")
    print("\nFlujo de registro:")
    print("1. ✅ Obtener géneros disponibles")
    print("2. ✅ Mostrar películas en tendencia")
    print("3. ✅ Registrar usuario con preferencias básicas")
    print("4. ✅ Configurar preferencias detalladas")
    print("5. ✅ Generar recomendaciones personalizadas")

def test_endpoints():
    """Función para probar endpoints individuales"""
    
    print("\n🧪 Probando endpoints individuales...")
    
    endpoints_to_test = [
        ("GET", "/", "Endpoint raíz"),
        ("GET", "/genres", "Géneros disponibles"),
        ("GET", "/trending_movies", "Películas en tendencia"),
        ("GET", "/health", "Estado del sistema"),
        ("GET", "/stats", "Estadísticas del sistema")
    ]
    
    for method, endpoint, description in endpoints_to_test:
        print(f"\n🔍 Probando: {description}")
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}")
            else:
                response = requests.post(f"{API_BASE}{endpoint}")
            
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error conectando a {endpoint}: {e}")

if __name__ == "__main__":
    try:
        # Verificar que la API esté disponible
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            main()
        else:
            print("❌ API no disponible. Verificar que esté ejecutándose en localhost:8000")
            test_endpoints()
    except Exception as e:
        print(f"❌ Error conectando a la API: {e}")
        print("\n💡 Asegúrate de que la API esté ejecutándose con:")
        print("   uvicorn api_ml32m_vectorial:app --reload --host 0.0.0.0 --port 8000") 