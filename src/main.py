from fastapi import FastAPI
from src.api import products
from src.database import Base, engine
from src.exceptions import register_exception_handlers

app = FastAPI()

Base.metadata.create_all(bind=engine)

register_exception_handlers(app)

app.include_router(products.router)
app.include_router(skus.router)

@app.get("/")
def root():
    return {"message": "B2B Service"}