from pydantic import BaseModel

class Order(BaseModel):
    restaurant_id: str
    dishes: list[dict]