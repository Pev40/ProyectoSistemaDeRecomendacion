#!/usr/bin/env python3
"""
Script para verificar los datos almacenados en MongoDB
"""

from pymongo import MongoClient
import json
from typing import Dict, Any

def check_mongodb_data():
    """
    Verifica el estado de las colecciones de MongoDB
    """
    try:
        # Conectar a MongoDB
        print("🔍 Conectando a MongoDB en localhost:27017...")
        client = MongoClient("mongodb://localhost:27017/")
        
        # Probar diferentes nombres de base de datos
        db_names = ["movie_recommendations"]
        
        print(f"\n📊 VERIFICANDO DATOS EN MONGODB")
        print("=" * 60)
        
        # Listar todas las bases de datos
        all_dbs = client.list_database_names()
        print(f"\n🗄️  Bases de datos disponibles:")
        for db_name in all_dbs:
            if db_name not in ["admin", "config", "local"]:
                print(f"   - {db_name}")
        
        # Verificar cada base de datos objetivo
        for db_name in db_names:
            if db_name in all_dbs:
                print(f"\n📁 BASE DE DATOS: '{db_name}'")
                print("-" * 40)
                
                db = client[db_name]
                collections = db.list_collection_names()
                
                if collections:
                    print(f"   ✅ Colecciones encontradas: {len(collections)}")
                    for collection_name in collections:
                        collection = db[collection_name]
                        count = collection.count_documents({})
                        print(f"      📋 {collection_name}: {count:,} documentos")
                        
                        # Mostrar muestra de datos para colecciones importantes
                        if collection_name in ["movies", "users", "ratings"] and count > 0:
                            print(f"         📝 Muestra de datos:")
                            sample = list(collection.find().limit(2))
                            for i, doc in enumerate(sample, 1):
                                # Eliminar _id para mejor legibilidad
                                doc_clean = {k: v for k, v in doc.items() if k != '_id'}
                                print(f"            {i}. {json.dumps(doc_clean, indent=8, default=str)}")
                else:
                    print(f"   ⚠️  No se encontraron colecciones")
            else:
                print(f"\n❌ Base de datos '{db_name}' no encontrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        print("💡 Asegúrate de que MongoDB esté ejecutándose en localhost:27017")
        return False

def check_specific_collection(db_name: str, collection_name: str):
    """
    Verifica una colección específica en detalle
    """
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client[db_name]
        collection = db[collection_name]
        
        print(f"\n🔍 DETALLES DE COLECCIÓN: {db_name}.{collection_name}")
        print("=" * 50)
        
        # Estadísticas básicas
        count = collection.count_documents({})
        print(f"📊 Total de documentos: {count:,}")
        
        if count > 0:
            # Primer documento
            first_doc = collection.find_one()
            if first_doc:
                print(f"\n📋 Estructura del primer documento:")
                first_doc_clean = {k: v for k, v in first_doc.items() if k != '_id'}
                print(json.dumps(first_doc_clean, indent=2, default=str))
            
            # Campos únicos
            if collection_name == "movies":
                print(f"\n🎬 Análisis de películas:")
                # Contar géneros únicos
                pipeline = [
                    {"$unwind": "$genres"},
                    {"$group": {"_id": "$genres"}},
                    {"$count": "unique_genres"}
                ]
                try:
                    result = list(collection.aggregate(pipeline))
                    if result:
                        print(f"   📝 Géneros únicos: {result[0]['unique_genres']}")
                except:
                    pass
                
                # Rango de años
                try:
                    years = list(collection.find({}, {"year": 1}).sort("year", 1))
                    if years:
                        min_year = min(doc.get("year", 0) for doc in years if doc.get("year", 0) > 0)
                        max_year = max(doc.get("year", 0) for doc in years)
                        print(f"   📅 Rango de años: {min_year} - {max_year}")
                except:
                    pass
            
            elif collection_name == "ratings":
                print(f"\n⭐ Análisis de ratings:")
                try:
                    # Estadísticas de ratings
                    pipeline = [
                        {"$group": {
                            "_id": None,
                            "avg_rating": {"$avg": "$rating"},
                            "min_rating": {"$min": "$rating"},
                            "max_rating": {"$max": "$rating"},
                            "total_ratings": {"$sum": 1}
                        }}
                    ]
                    result = list(collection.aggregate(pipeline))
                    if result:
                        stats = result[0]
                        print(f"   📊 Rating promedio: {stats['avg_rating']:.2f}")
                        print(f"   📊 Rating mínimo: {stats['min_rating']}")
                        print(f"   📊 Rating máximo: {stats['max_rating']}")
                        print(f"   📊 Total ratings: {stats['total_ratings']:,}")
                except:
                    pass
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 VERIFICADOR DE DATOS MONGODB")
    print("=" * 60)
    
    # Verificar todas las bases de datos
    success = check_mongodb_data()
    
    if success:
        print(f"\n💡 Para ver detalles de una colección específica:")
        print(f"   python check_mongodb_data.py <db_name> <collection_name>") 