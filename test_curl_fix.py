#!/usr/bin/env python3
"""
Prueba del endpoint /similar_movies después del fix
"""

import requests
import json

def test_similar_movies():
    """Prueba el endpoint con diferentes casos"""
    
    API_BASE = "http://localhost:8000"
    
    print("🧪 Probando endpoint /similar_movies después del fix")
    print("=" * 60)
    
    # Caso 1: Con movie_id válido (como lo envía el frontend)
    print("\n1️⃣ Probando con movie_id válido (caso normal del frontend)...")
    test_data = {
        "movie_id": 1,  # Toy Story
        "k": 12
    }
    
    try:
        response = requests.post(f"{API_BASE}/similar_movies", json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Respuesta exitosa")
            print(f"Base movie: {data.get('base_movie', {}).get('title', 'N/A')}")
            print(f"Similar movies encontradas: {data.get('count', 0)}")
        else:
            print("❌ Error en respuesta:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error conectando: {e}")
    
    # Caso 2: Sin movie_id (debería fallar correctamente)
    print("\n2️⃣ Probando sin movie_id (debería devolver error 422)...")
    test_data_invalid = {"k": 12}
    
    try:
        response = requests.post(f"{API_BASE}/similar_movies", json=test_data_invalid)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Error 422 correcto (campo requerido faltante)")
            error_data = response.json()
            print(f"Error detalle: {error_data}")
        else:
            print(f"❌ Status code inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error conectando: {e}")
    
    # Caso 3: El curl original del usuario (debería fallar)
    print("\n3️⃣ Probando el curl original del usuario...")
    import subprocess
    
    curl_command = [
        'curl', '-X', 'POST',
        'http://localhost:8000/similar_movies',
        '-H', 'Content-Type: application/json',
        '-d', '{"k":12}'
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=10)
        print(f"Curl status code: {result.returncode}")
        print("Respuesta:")
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error ejecutando curl: {e}")
    
    print("\n🎯 Resumen:")
    print("- El endpoint requiere movie_id como campo obligatorio")
    print("- El frontend ya lo envía correctamente: movie_id + k")
    print("- Requests sin movie_id fallan con error 422 (correcto)")

if __name__ == "__main__":
    test_similar_movies() 