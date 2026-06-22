from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.category import Category
from ..schemas.category import CategoryCreate, CategoryUpdate, generate_slug


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    return db.query(Category).offset(skip).limit(limit).all()


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
    return db.query(Category).filter(Category.slug == slug).first()


def create_category(db: Session, category_in: CategoryCreate) -> Category:
    slug = generate_slug(category_in.name)
    existing = get_category_by_slug(db, slug)
    if existing:
        slug = f"{slug}-{db.query(Category).count()}"
    category = Category(
        name=category_in.name,
        slug=slug,
        description=category_in.description,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Category, category_in: CategoryUpdate) -> Category:
    data = category_in.model_dump(exclude_unset=True)
    if "name" in data:
        data["slug"] = generate_slug(data["name"])
    for key, value in data.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()
