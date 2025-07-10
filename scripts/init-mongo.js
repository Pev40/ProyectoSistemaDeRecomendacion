// Script de inicialización para MongoDB
// Este script se ejecuta automáticamente cuando se inicia el contenedor de MongoDB

// Crear base de datos
db = db.getSiblingDB('movielens_32m');

// Crear colecciones
db.createCollection('movies');
db.createCollection('ratings');
db.createCollection('users');

// Crear índices para optimizar consultas
db.ratings.createIndex({ "userId": 1 });
db.ratings.createIndex({ "movieId": 1 });
db.ratings.createIndex({ "userId": 1, "timestamp": 1 });
db.ratings.createIndex({ "movieId": 1, "rating": 1 });

db.movies.createIndex({ "movieId": 1 });
db.movies.createIndex({ "title": "text" });
db.movies.createIndex({ "genres": 1 });

db.users.createIndex({ "userId": 1 });

print("Base de datos movielens_32m inicializada correctamente");
print("Colecciones creadas: movies, ratings, users");
print("Índices creados para optimizar consultas"); 