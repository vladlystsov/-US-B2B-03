from fastapi import FastAPI
from src.api import products
from src.api import skus
from src.api import invoices
from src.api import reserve
from src.api import moderation_events
from src.database import Base, engine
from src.exceptions import register_exception_handlers

app = FastAPI()

Base.metadata.create_all(bind=engine)

register_exception_handlers(app)

app.include_router(products.router)
app.include_router(skus.router)
app.include_router(invoices.router)
app.include_router(reserve.router)
app.include_router(moderation_events.router)

@app.get("/")
def root():
    return {"message": "B2B Service"}