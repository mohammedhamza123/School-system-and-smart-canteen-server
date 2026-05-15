from sqlalchemy.orm import Session

from app.features.product.model import Product


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Product | None:
        return self.db.query(Product).filter(Product.sku == sku).first()

    def list_all(self) -> list[Product]:
        return self.db.query(Product).order_by(Product.id.desc()).all()
