# Script de Prueba para API ML32M Vectorial
import requests
import json
import time
import asyncio
from typing import Dict, Any
import sys

class APITester:
    """Clase para testear todos los endpoints de la API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Headers por defecto
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        print(f"🔧 Configurando tester para API: {base_url}")
    
    def print_section(self, title: str):
        """Imprime una sección separada"""
        print("\n" + "="*70)
        print(f" {title}")
        print("="*70)
    
    def print_test(self, test_name: str, result: Dict[str, Any], success: bool = True):
        """Imprime resultado de un test"""
        status = "✅" if success else "❌"
        print(f"\n{status} {test_name}")
        
        if success:
            # Mostrar información relevante
            if 'processing_time' in result:
                print(f"   ⏱️  Tiempo: {result['processing_time']}s")
            if 'count' in result:
                print(f"   📊 Resultados: {result['count']}")
            if 'status' in result and result['status']:
                print(f"   🔄 Estado: {result['status']}")
        else:
            print(f"   ❌ Error: {result}")
    
    def test_health_check(self):
        """Test del endpoint de salud"""
        self.print_section("HEALTH CHECK")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Health Check", data, True)
                
                # Detalles de componentes
                if 'components' in data:
                    print("\n   📋 Estado de componentes:")
                    for component, status in data['components'].items():
                        component_status = "🟢" if status.get('status') == 'ok' else "🟡" if status.get('status') == 'warning' else "🔴"
                        print(f"      {component_status} {component}: {status.get('status', 'unknown')}")
                
                return data['status'] in ['healthy', 'partial']
            else:
                self.print_test("Health Check", {"error": f"HTTP {response.status_code}"}, False)
                return False
                
        except Exception as e:
            self.print_test("Health Check", {"error": str(e)}, False)
            return False
    
    def test_root_endpoint(self):
        """Test del endpoint raíz"""
        self.print_section("ROOT ENDPOINT")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Endpoint Raíz", data, True)
                print(f"   📝 Versión: {data.get('version', 'N/A')}")
                print(f"   🔗 Endpoints disponibles: {len(data.get('endpoints', {}))}")
                return True
            else:
                self.print_test("Endpoint Raíz", {"error": f"HTTP {response.status_code}"}, False)
                return False
                
        except Exception as e:
            self.print_test("Endpoint Raíz", {"error": str(e)}, False)
            return False
    
    def test_user_stats(self, user_id: int = 1):
        """Test de estadísticas de usuario"""
        self.print_section(f"USER STATS - Usuario {user_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/user_stats/{user_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.print_test(f"Estadísticas Usuario {user_id}", data, True)
                
                if 'stats' in data:
                    stats = data['stats']
                    print(f"   📊 Total ratings: {stats.get('total_ratings', 0)}")
                    print(f"   ⭐ Rating promedio: {stats.get('avg_rating', 0):.2f}")
                    print(f"   📝 Secuencia: {data.get('sequence_length', 0)} películas")
                
                return True
            elif response.status_code == 404:
                print(f"   ⚠️  Usuario {user_id} no encontrado")
                return True  # Es un resultado válido
            else:
                self.print_test(f"Estadísticas Usuario {user_id}", {"error": f"HTTP {response.status_code}"}, False)
                return False
                
        except Exception as e:
            self.print_test(f"Estadísticas Usuario {user_id}", {"error": str(e)}, False)
            return False
    
    def test_popular_movies(self, limit: int = 5):
        """Test de películas populares"""
        self.print_section("PELÍCULAS POPULARES")
        
        try:
            response = self.session.get(f"{self.base_url}/popular_movies?limit={limit}")
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Películas Populares", data, True)
                
                if 'popular_movies' in data and data['popular_movies']:
                    print(f"\n   🎬 Top {min(limit, len(data['popular_movies']))} películas:")
                    for i, movie in enumerate(data['popular_movies'][:limit], 1):
                        title = movie.get('title', 'Sin título')[:50]
                        rating = movie.get('avg_rating', 0)
                        count = movie.get('total_ratings', 0)
                        print(f"      {i}. {title} - ⭐{rating:.1f} ({count} ratings)")
                
                return True
            else:
                self.print_test("Películas Populares", {"error": f"HTTP {response.status_code}"}, False)
                return False
                
        except Exception as e:
            self.print_test("Películas Populares", {"error": str(e)}, False)
            return False
    
    def test_search_movies(self, query: str = "matrix"):
        """Test de búsqueda de películas"""
        self.print_section(f"BÚSQUEDA DE PELÍCULAS - '{query}'")
        
        try:
            payload = {
                "query": query,
                "limit": 5
            }
            
            response = self.session.post(f"{self.base_url}/search_movies", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_test(f"Búsqueda '{query}'", data, True)
                
                if 'results' in data and data['results']:
                    print(f"\n   🔍 Resultados para '{query}':")
                    for i, movie in enumerate(data['results'][:5], 1):
                        title = movie.get('title', 'Sin título')[:50]
                        year = movie.get('year', 'N/A')
                        print(f"      {i}. {title} ({year})")
                else:
                    print(f"   📭 No se encontraron resultados para '{query}'")
                
                return True
            else:
                self.print_test(f"Búsqueda '{query}'", {"error": f"HTTP {response.status_code}"}, False)
                return False
                
        except Exception as e:
            self.print_test(f"Búsqueda '{query}'", {"error": str(e)}, False)
            return False
    
    def test_recommendations(self, user_id: int = 1, k: int = 5):
        """Test de recomendaciones"""
        self.print_section(f"RECOMENDACIONES - Usuario {user_id}")
        
        try:
            payload = {
                "user_id": user_id,
                "k": k,
                "method": "vectorial"
            }
            
            response = self.session.post(f"{self.base_url}/recommend", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_test(f"Recomendaciones Usuario {user_id}", data, True)
                
                if 'recommendations' in data and data['recommendations']:
                    print(f"\n   🎯 Recomendaciones para usuario {user_id}:")
                    for i, movie in enumerate(data['recommendations'][:k], 1):
                        title = movie.get('title', 'Sin título')[:50]
                        score = movie.get('score', 0)
                        genres = movie.get('genres', [])
                        if isinstance(genres, list):
                            genres_str = ', '.join(genres[:2])  # Primeros 2 géneros
                        else:
                            genres_str = str(genres)[:30] if genres else "N/A"
                        print(f"      {i}. {title}")
                        print(f"         Score: {score:.3f} | Géneros: {genres_str}")
                
                print(f"\n   📊 Historial del usuario: {data.get('user_history_size', 0)} películas")
                
                return True
            elif response.status_code == 404:
                print(f"   ⚠️  Usuario {user_id} no encontrado o sin historial")
                return True  # Es un resultado válido
            else:
                error_detail = response.json().get('detail', f'HTTP {response.status_code}') if response.headers.get('content-type', '').startswith('application/json') else f'HTTP {response.status_code}'
                self.print_test(f"Recomendaciones Usuario {user_id}", {"error": error_detail}, False)
                return False
                
        except Exception as e:
            self.print_test(f"Recomendaciones Usuario {user_id}", {"error": str(e)}, False)
            return False
    
    def test_similar_movies(self, movie_id: int = 1, k: int = 5):
        """Test de películas similares"""
        self.print_section(f"PELÍCULAS SIMILARES - Película {movie_id}")
        
        try:
            payload = {
                "movie_id": movie_id,
                "k": k
            }
            
            response = self.session.post(f"{self.base_url}/similar_movies", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_test(f"Similares a Película {movie_id}", data, True)
                
                # Información de película base
                if 'base_movie' in data:
                    base = data['base_movie']
                    print(f"\n   🎬 Película base: {base.get('title', 'N/A')}")
                    print(f"      Géneros: {base.get('genres', 'N/A')}")
                
                # Películas similares
                if 'similar_movies' in data and data['similar_movies']:
                    print(f"\n   🎭 Películas similares:")
                    for i, movie in enumerate(data['similar_movies'][:k], 1):
                        title = movie.get('title', 'Sin título')[:50]
                        score = movie.get('score', 0)
                        year = movie.get('year', 'N/A')
                        print(f"      {i}. {title} ({year}) - Score: {score:.3f}")
                
                return True
            elif response.status_code == 404:
                print(f"   ⚠️  Película {movie_id} no encontrada en base vectorial")
                return True  # Es un resultado válido
            else:
                error_detail = response.json().get('detail', f'HTTP {response.status_code}') if response.headers.get('content-type', '').startswith('application/json') else f'HTTP {response.status_code}'
                self.print_test(f"Similares a Película {movie_id}", {"error": error_detail}, False)
                return False
                
        except Exception as e:
            self.print_test(f"Similares a Película {movie_id}", {"error": str(e)}, False)
            return False
    
    def test_update_user(self, user_id: int = 999, movie_id: int = 1, rating: float = 4.5):
        """Test de actualización de usuario"""
        self.print_section(f"ACTUALIZAR USUARIO - Usuario {user_id}")
        
        try:
            payload = {
                "user_id": user_id,
                "movie_id": movie_id,
                "rating": rating
            }
            
            response = self.session.post(f"{self.base_url}/update_user", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_test(f"Actualizar Usuario {user_id}", data, True)
                print(f"   📝 Calificación: Película {movie_id} → {rating}⭐")
                return True
            else:
                error_detail = response.json().get('detail', f'HTTP {response.status_code}') if response.headers.get('content-type', '').startswith('application/json') else f'HTTP {response.status_code}'
                self.print_test(f"Actualizar Usuario {user_id}", {"error": error_detail}, False)
                return False
                
        except Exception as e:
            self.print_test(f"Actualizar Usuario {user_id}", {"error": str(e)}, False)
            return False
    
    def test_system_stats(self):
        """Test de estadísticas del sistema"""
        self.print_section("ESTADÍSTICAS DEL SISTEMA")
        
        try:
            response = self.session.get(f"{self.base_url}/stats")
            
            if response.status_code == 200:
                data = response.json()
                self.print_test("Estadísticas del Sistema", data, True)
                
                if 'system_stats' in data:
                    stats = data['system_stats']
                    print("\n   📊 Estadísticas por componente:")
                    
                    # MongoDB
                    if 'mongodb' in stats:
                        mongo = stats['mongodb']
                        print(f"      🍃 MongoDB:")
                        print(f"         Películas: {mongo.get('movies', 0):,}")
                        print(f"         Ratings: {mongo.get('ratings', 0):,}")
                        print(f"         Usuarios: {mongo.get('users', 0):,}")
                    
                    # Qdrant
                    if 'qdrant' in stats:
                        qdrant = stats['qdrant']
                        print(f"      🔍 Qdrant:")
                        print(f"         Vectores: {qdrant.get('vectors_count', 0):,}")
                        print(f"         Puntos: {qdrant.get('points_count', 0):,}")
                    
                    # Redis
                    if 'redis' in stats:
                        redis = stats['redis']
                        print(f"      📦 Redis:")
                        print(f"         Memoria: {redis.get('used_memory', 'N/A')}")
                        print(f"         Hits: {redis.get('keyspace_hits', 0):,}")
                
                return True
            else:
                self.print_test("Estadísticas del Sistema", {"error": f"HTTP {response.status_code}"}, False)
                return False
                
        except Exception as e:
            self.print_test("Estadísticas del Sistema", {"error": str(e)}, False)
            return False
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🧪 INICIANDO SUITE DE PRUEBAS API ML32M VECTORIAL")
        print(f"🌐 URL Base: {self.base_url}")
        print(f"⏰ Tiempo: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Root Endpoint", self.test_root_endpoint),
            ("System Stats", self.test_system_stats),
            ("Popular Movies", self.test_popular_movies),
            ("Search Movies", self.test_search_movies),
            ("User Stats", lambda: self.test_user_stats(1)),
            ("Recommendations", lambda: self.test_recommendations(1)),
            ("Similar Movies", lambda: self.test_similar_movies(1)),
            ("Update User", lambda: self.test_update_user(999, 1, 4.5))
        ]
        
        results = {}
        start_time = time.time()
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                time.sleep(0.5)  # Pausa entre tests
            except Exception as e:
                print(f"❌ Error en test {test_name}: {e}")
                results[test_name] = False
        
        # Resumen
        elapsed_time = time.time() - start_time
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        self.print_section("RESUMEN DE PRUEBAS")
        print(f"✅ Tests pasados: {passed}/{total}")
        print(f"⏱️  Tiempo total: {elapsed_time:.2f}s")
        print(f"📊 Tasa de éxito: {(passed/total)*100:.1f}%")
        
        # Detalles
        print("\n📋 Detalles por test:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
        
        return passed == total

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tester para API ML32M Vectorial")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base de la API")
    parser.add_argument("--test", choices=[
        "all", "health", "root", "stats", "popular", "search", 
        "recommendations", "similar", "update", "user_stats"
    ], default="all", help="Test específico a ejecutar")
    parser.add_argument("--user-id", type=int, default=1, help="ID de usuario para tests")
    parser.add_argument("--movie-id", type=int, default=1, help="ID de película para tests")
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    
    if args.test == "all":
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    elif args.test == "health":
        success = tester.test_health_check()
    elif args.test == "root":
        success = tester.test_root_endpoint()
    elif args.test == "stats":
        success = tester.test_system_stats()
    elif args.test == "popular":
        success = tester.test_popular_movies()
    elif args.test == "search":
        success = tester.test_search_movies()
    elif args.test == "recommendations":
        success = tester.test_recommendations(args.user_id)
    elif args.test == "similar":
        success = tester.test_similar_movies(args.movie_id)
    elif args.test == "update":
        success = tester.test_update_user(args.user_id, args.movie_id, 4.5)
    elif args.test == "user_stats":
        success = tester.test_user_stats(args.user_id)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 