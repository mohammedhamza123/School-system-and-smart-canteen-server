from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.product.schema import ProductCreate, ProductRead, ProductUpdate
from app.features.product.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF)),
):
    return ProductService(db).create(payload)


@router.get("/", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF))):
    return ProductService(db).list_all()


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF)),
):
    return ProductService(db).update(product_id, payload)
