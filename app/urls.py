from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/{restaurant}")
def add(request, restaurant: str):
    return {"result": restaurant}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
