db = db.getSiblingDB('restaurants');

db.createCollection('restaurants');
db.createCollection('images');

db.createCollection('usuarios');
db.createCollection('clientes');
db.createCollection('administradores');
db.createCollection('encargados_despacho');
db.createCollection('duenos');
db.createCollection('pedidos');
