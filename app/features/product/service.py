from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.features.product.model import Product
from app.features.product.repository import ProductRepository
from app.features.product.schema import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    def create(self, payload: ProductCreate) -> Product:
        if self.repo.get_by_sku(payload.sku):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")
        product = Product(**payload.model_dump())
        return self.repo.create(product)

    def list_all(self) -> list[Product]:
        return self.repo.list_all()

    def update(self, product_id: int, payload: ProductUpdate) -> Product:
        product = self.repo.get_by_id(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        return product
