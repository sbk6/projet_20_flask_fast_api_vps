from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional, List, Tuple
from decimal import Decimal
from ..models.product import Product
from ..models.review import Review
from ..schemas.product import ProductCreate, ProductUpdate
import re


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ç]", "c", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def get_products(
    db: Session,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    price_min: Optional[Decimal] = None,
    price_max: Optional[Decimal] = None,
    in_stock: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Product], int]:
    query = db.query(Product).filter(Product.is_active == True)

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(Product.name.ilike(pattern), Product.description.ilike(pattern))
        )
    if price_min is not None:
        query = query.filter(Product.price >= price_min)
    if price_max is not None:
        query = query.filter(Product.price <= price_max)
    if in_stock is True:
        query = query.filter(Product.stock > 0)
    elif in_stock is False:
        query = query.filter(Product.stock == 0)

    total = query.count()
    products = query.offset(skip).limit(limit).all()
    return products, total


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    return (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )


def get_product_with_stats(db: Session, product_id: int) -> Optional[dict]:
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    stats = db.query(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("count"),
    ).filter(Review.product_id == product_id).first()
    return {
        "product": product,
        "average_rating": float(stats.avg_rating) if stats.avg_rating else None,
        "review_count": stats.count or 0,
    }


def create_product(db: Session, product_in: ProductCreate) -> Product:
    slug = slugify(product_in.name)
    existing = db.query(Product).filter(Product.slug == slug).first()
    if existing:
        slug = f"{slug}-{db.query(Product).count()}"
    product = Product(
        name=product_in.name,
        slug=slug,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        image_url=product_in.image_url,
        category_id=product_in.category_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, product_in: ProductUpdate) -> Product:
    data = product_in.model_dump(exclude_unset=True)
    if "name" in data:
        data["slug"] = slugify(data["name"])
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    product.is_active = False
    db.commit()
