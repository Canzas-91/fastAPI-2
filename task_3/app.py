from fastapi import FastAPI
from typing import Optional
from models import UserCreate

app = FastAPI()

sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case",  "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone",      "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones",  "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch",  "category": "Electronics", "price": 299.99},
]

@app.post("/create_user")
def create_user(user: UserCreate):
    return user

@app.get("/products/search")
def search_products(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    results = [
        p for p in sample_products
        if keyword.lower() in p["name"].lower()
    ]
    if category:
        results = [p for p in results if p["category"] == category]
    return results[:limit]

@app.get("/product/{product_id}")
def get_product(product_id: int):
    for p in sample_products:
        if p["product_id"] == product_id:
            return p
    return {"error": "Product not found"}
