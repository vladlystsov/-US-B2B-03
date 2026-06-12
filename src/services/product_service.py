from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.product import Product
from src.schemas.product import ProductCreateRequest
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified


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

        product.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update_sku(self, sku_id: str, seller_id: str, update_data: dict) -> dict:
        from src.services.event_service import send_edited_event
        
        products = self.db.query(Product).filter(
            Product.seller_id == seller_id
        ).all()
        
        found_product = None
        sku_index = None
        original_reserved = None
        
        for prod in products:
            for i, sku in enumerate(prod.skus):
                if sku.get("id") == sku_id:
                    found_product = prod
                    sku_index = i
                    original_reserved = sku.get("reserved_quantity", 0)
                    break
            if found_product:
                break
        
        if not found_product:
            raise HTTPException(
                status_code=404,
                detail={"code": "SKU_NOT_FOUND", "message": "SKU not found"}
            )
        
        if found_product.status == "HARD_BLOCKED":
            raise HTTPException(
                status_code=403,
                detail={"code": "HARD_BLOCKED", "message": "Product is hard blocked"}
            )
        
        sku_to_update = found_product.skus[sku_index]
        
        if "sku_code" in update_data:
            sku_to_update["sku_code"] = update_data["sku_code"]
        if "price" in update_data:
            sku_to_update["price"] = update_data["price"]
        if "stock_quantity" in update_data:
            sku_to_update["stock_quantity"] = update_data["stock_quantity"]
        
        sku_to_update["reserved_quantity"] = original_reserved
        sku_to_update["updated_at"] = datetime.utcnow().isoformat()
        
        if "created_at" not in sku_to_update:
            sku_to_update["created_at"] = datetime.utcnow().isoformat()
        
        flag_modified(found_product, "skus")
        
        old_status = found_product.status
        if old_status in ["MODERATED", "BLOCKED"]:
            found_product.status = "ON_MODERATION"
            found_product.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        result_sku = found_product.skus[sku_index].copy()
        result_sku["product_id"] = str(found_product.id)
        
        send_edited_event(
            product_id=str(found_product.id),
            seller_id=seller_id,
            changes=update_data
        )
        
        return result_sku
    
    def delete_product(self, product_id: str, seller_id: str) -> None:
        from src.services.event_service import send_deleted_event, send_product_deleted_to_b2c
        
        product = self.db.query(Product).filter(
            Product.id == product_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product.seller_id != seller_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if product.deleted:
            raise HTTPException(
                status_code=400,
                detail={"code": "ALREADY_DELETED", "message": "Product already deleted"}
            )
        
        product.deleted = True
        self.db.commit()
        
        sku_ids = [sku.get("id") for sku in product.skus if sku.get("id")]
        
        send_deleted_event(product_id=product.id, seller_id=seller_id)
        send_product_deleted_to_b2c(product_id=product.id, sku_ids=sku_ids)

    def get_seller_products(self, seller_id: str, skip: int = 0, limit: int = 100) -> list[Product]:
        return self.db.query(Product).filter(
            Product.seller_id == seller_id,
            Product.deleted == False
        ).offset(skip).limit(limit).all()