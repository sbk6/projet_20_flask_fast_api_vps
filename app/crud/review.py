from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from ..models.review import Review
from ..schemas.review import ReviewCreate, ReviewUpdate


def get_product_reviews(db: Session, product_id: int, skip: int = 0, limit: int = 20) -> List[Review]:
    return (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def get_user_product_review(db: Session, user_id: int, product_id: int) -> Optional[Review]:
    return db.query(Review).filter(
        Review.user_id == user_id, Review.product_id == product_id
    ).first()


def create_review(db: Session, user_id: int, product_id: int, review_in: ReviewCreate) -> Review:
    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=review_in.rating,
        title=review_in.title,
        comment=review_in.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_review(db: Session, review: Review, review_in: ReviewUpdate) -> Review:
    data = review_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()
