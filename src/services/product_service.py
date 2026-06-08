from sqlalchemy.orm import Session
from uuid import UUID
from src.models.product import Product
from src.schemas.product import ProductCreateRequest

class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_product(self, seller_id: UUID, product_data: ProductCreateRequest) -> Product:
        slug = product_data.slug or product_data.title.lower().replace(" ", "-")[:255]
        
        product = Product(
            seller_id=seller_id,
            category_id=product_data.category_id,
            title=product_data.title,
            slug=slug,
            description=product_data.description,
            status="CREATED",
            deleted=False,
            blocked=False,
            moderator_comment="",
            images=[img.model_dump() for img in product_data.images],
            characteristics=[char.model_dump() for char in product_data.characteristics] if product_data.characteristics else [],
            skus=[]
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def update_product(self, product_id: UUID, seller_id: UUID, update_data: dict) -> Product:
        from src.models.product import Product

        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.seller_id == seller_id
        ).first()
        
        if not product:
            raise HTTPException(404, "Product not found")

        if product.status == "HARD_BLOCKED":
            raise HTTPException(403, "Hard blocked product cannot be edited")
 
        old_status = product.status

        for key, value in update_data.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        
        if old_status in ["MODERATED", "BLOCKED"]:
            product.status = "ON_MODERATION"
        
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update_sku(self, sku_id: UUID, seller_id: UUID, update_data: dict) -> SKU:

        from src.models.product import SKU, Product
        
        sku = self.db.query(SKU).join(Product).filter(
            SKU.id == sku_id,
            Product.seller_id == seller_id
        ).first()
        
        if not sku:
            raise HTTPException(404, "SKU not found")

        if sku.product.status == "HARD_BLOCKED":
            raise HTTPException(403, "Product is hard blocked")

        original_reserved = sku.reserved_quantity
        
        for key, value in update_data.items():
            if hasattr(sku, key) and value is not None:
                setattr(sku, key, value)

        sku.reserved_quantity = original_reserved

        if sku.product.status in ["MODERATED", "BLOCKED"]:
            sku.product.status = "ON_MODERATION"
        
        self.db.commit()
        self.db.refresh(sku)
        return sku