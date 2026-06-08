from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.product import Product
from src.schemas.product import ProductCreateRequest


class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_product(self, seller_id: str, product_data: ProductCreateRequest) -> Product:
        slug = product_data.slug or product_data.title.lower().replace(" ", "-")[:255]
        
        category_id_str = str(product_data.category_id)

        images_json = []
        for img in product_data.images:
            images_json.append({
                "id": str(img.id),
                "url": img.url,
                "ordering": img.ordering
            })
        
        characteristics_json = []
        if product_data.characteristics:
            for char in product_data.characteristics:
                characteristics_json.append({
                    "id": str(char.id),
                    "name": char.name,
                    "value": char.value
                })
        
        product = Product(
            seller_id=seller_id,
            category_id=category_id_str,
            title=product_data.title,
            slug=slug,
            description=product_data.description,
            status="CREATED",
            deleted=False,
            blocked=False,
            moderator_comment="",
            images=images_json,
            characteristics=characteristics_json,
            skus=[]
        )
        
        print(f"DEBUG CREATE: product object - seller_id={product.seller_id}, category_id={product.category_id}")
        
        self.db.add(product)
        
        try:
            self.db.commit()
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            raise
        
        self.db.refresh(product)
        return product
    
    def update_product(self, product_id: str, seller_id: str, update_data: dict) -> Product:
        product = self.db.query(Product).filter(
            Product.id == product_id
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product.seller_id != seller_id:
            raise HTTPException(status_code=403, detail="Access denied: you are not the owner of this product")

        if product.status == "HARD_BLOCKED":
            raise HTTPException(status_code=403, detail="Hard blocked product cannot be edited")

        old_status = product.status

        for key, value in update_data.items():
            if hasattr(product, key) and value is not None:
                if key == "category_id" and value:
                    value = str(value)
                elif key == "images" and value:
                    value = [{"id": str(img.id), "url": img.url, "ordering": img.ordering} for img in value]
                elif key == "characteristics" and value:
                    value = [{"id": str(char.id), "name": char.name, "value": char.value} for char in value]
                setattr(product, key, value)

        if old_status in ["MODERATED", "BLOCKED"]:
            product.status = "ON_MODERATION"

        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update_sku(self, sku_id: str, seller_id: str, update_data: dict) -> dict:
        products = self.db.query(Product).filter(
            Product.seller_id == seller_id
        ).all()
        
        found_product = None
        sku_index = None
        original_reserved = None
        
        for prod in products:
            for i, sku in enumerate(prod.skus):
                if str(sku.get("id")) == str(sku_id):
                    found_product = prod
                    sku_index = i
                    original_reserved = sku.get("reserved_quantity", 0)
                    break
            if found_product:
                break
        
        if not found_product:
            raise HTTPException(status_code=404, detail="SKU not found")
        
        if found_product.status == "HARD_BLOCKED":
            raise HTTPException(status_code=403, detail="Product is hard blocked")
        
        updated_sku = found_product.skus[sku_index].copy()
        
        if "sku_code" in update_data and update_data["sku_code"] is not None:
            updated_sku["sku_code"] = update_data["sku_code"]
        if "price" in update_data and update_data["price"] is not None:
            updated_sku["price"] = update_data["price"]
        if "stock_quantity" in update_data and update_data["stock_quantity"] is not None:
            updated_sku["stock_quantity"] = update_data["stock_quantity"]
        
        updated_sku["reserved_quantity"] = original_reserved
        found_product.skus[sku_index] = updated_sku
        
        if found_product.status in ["MODERATED", "BLOCKED"]:
            found_product.status = "ON_MODERATION"
        
        self.db.commit()
        self.db.refresh(found_product)
        
        updated_sku["product_id"] = str(found_product.id)
        return updated_sku