"""评论与评分仓储实现。"""

from sqlalchemy.orm import Session

from app.domain.entities.review import BookReview
from app.domain.value_objects.enums import ReviewStatus
from app.infrastructure.models.orm import BookReviewORM


def _to_entity(orm: BookReviewORM) -> BookReview:
    return BookReview(
        id=orm.id,
        title_id=orm.title_id,
        reader_id=orm.reader_id,
        rating=orm.rating,
        comment=orm.comment,
        status=ReviewStatus(orm.status),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


class SQLAlchemyReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, review_id: int) -> BookReview | None:
        orm = self.db.query(BookReviewORM).filter(BookReviewORM.id == review_id).first()
        return _to_entity(orm) if orm else None

    def find_by_reader_and_title(self, reader_id: int, title_id: int) -> BookReview | None:
        orm = (
            self.db.query(BookReviewORM)
            .filter(
                BookReviewORM.reader_id == reader_id,
                BookReviewORM.title_id == title_id,
            )
            .first()
        )
        return _to_entity(orm) if orm else None

    def list_by_status(self, title_id: int, status: ReviewStatus) -> list[BookReview]:
        rows = (
            self.db.query(BookReviewORM)
            .filter(
                BookReviewORM.title_id == title_id,
                BookReviewORM.status == status.value,
            )
            .order_by(BookReviewORM.created_at.desc())
            .all()
        )
        return [_to_entity(r) for r in rows]

    def list_all_by_status(self, status: ReviewStatus) -> list[BookReview]:
        """按状态列出全部标题的评论（供管理员审核台使用）。"""
        rows = (
            self.db.query(BookReviewORM)
            .filter(BookReviewORM.status == status.value)
            .order_by(BookReviewORM.created_at.asc())
            .all()
        )
        return [_to_entity(r) for r in rows]

    def save(self, review: BookReview) -> BookReview:
        orm = None
        if review.id is not None:
            orm = self.db.query(BookReviewORM).filter(BookReviewORM.id == review.id).first()
        if orm is None:
            orm = BookReviewORM(
                title_id=review.title_id,
                reader_id=review.reader_id,
                rating=review.rating,
                comment=review.comment,
                status=review.status.value,
            )
            self.db.add(orm)
        else:
            orm.rating = review.rating
            orm.comment = review.comment
            orm.status = review.status.value
        self.db.flush()
        review.id = orm.id
        review.created_at = orm.created_at
        review.updated_at = orm.updated_at
        return review
