"""评论与评分应用服务（FR-022 ~ FR-024）。"""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.domain.entities.review import BookReview
from app.domain.value_objects.enums import ReviewStatus
from app.infrastructure.repositories.catalog_repository import SQLAlchemyTitleRepository
from app.infrastructure.repositories.reader_repository import SQLAlchemyReaderRepository
from app.infrastructure.repositories.review_repository import SQLAlchemyReviewRepository


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.titles = SQLAlchemyTitleRepository(db)
        self.readers = SQLAlchemyReaderRepository(db)
        self.reviews = SQLAlchemyReviewRepository(db)

    def submit(self, reader_id: int, title_id: int, rating: int, comment: str | None) -> dict:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("图书不存在")

        review = self.reviews.find_by_reader_and_title(reader_id, title_id)
        if review is None:
            review = BookReview(title_id=title_id, reader_id=reader_id)

        review.update(rating, comment)  # 评分越界由领域层拒绝；更新后重置为 PENDING
        self.reviews.save(review)
        self.db.commit()

        return {
            "review_id": review.id,
            "title_id": title_id,
            "rating": review.rating,
            "comment": review.comment,
            "status": str(review.status),
        }

    def list_approved(self, title_id: int) -> dict:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("图书不存在")

        rows = self.reviews.list_by_status(title_id, ReviewStatus.APPROVED)
        average = round(sum(r.rating for r in rows) / len(rows), 1) if rows else 0.0

        return {
            "title_id": title_id,
            "average_rating": average,
            "total": len(rows),
            "reviews": [
                {
                    "review_id": r.id,
                    "reader_id": r.reader_id,
                    "rating": r.rating,
                    "comment": r.comment,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
        }

    def moderate(self, review_id: int, decision: str) -> dict:
        review = self.reviews.get(review_id)
        if review is None:
            raise NotFoundError("评论不存在")

        if decision == "APPROVED":
            review.approve()
        elif decision == "REJECTED":
            review.reject()
        else:
            raise PermissionDeniedError("审核结论非法")

        self.reviews.save(review)
        self.db.commit()
        return {"review_id": review.id, "status": str(review.status)}
