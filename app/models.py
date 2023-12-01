from pydantic import BaseModel

class Order(BaseModel):
    restaurant_id: str
    dishes: list[dict]

class Pedido(BaseModel):
    pedido_id: str
    estado: bool

    
class User(BaseModel):
    user_id: str
    username: str
    email: str # cambiar a tipo email con alguna libreria como pydantic
    password: str
    role: str  # roles posibles: ["cliente", "administrador", "encargado_despacho", "dueÃ±o"]