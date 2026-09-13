"""图书评论与评分领域实体（BR-013 / BR-014 / BR-018）。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.exceptions import BusinessError
from app.domain.value_objects.enums import ReviewStatus

MIN_RATING = 1
MAX_RATING = 5


@dataclass
class BookReview:
    """图书评论：评分 1-5，需审核后对外可见。"""

    id: Optional[int] = None
    title_id: Optional[int] = None
    reader_id: Optional[int] = None
    rating: int = 0
    comment: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def validate_rating(rating: int) -> None:
        if not isinstance(rating, int) or not (MIN_RATING <= rating <= MAX_RATING):
            raise BusinessError(f"评分必须为 {MIN_RATING}-{MAX_RATING} 的整数")

    def update(self, rating: int, comment: Optional[str]) -> None:
        """提交或更新评论；更新后状态重置为 PENDING，需重新审核。"""
        self.validate_rating(rating)
        self.rating = rating
        self.comment = comment
        self.status = ReviewStatus.PENDING

    def approve(self) -> None:
        if self.status != ReviewStatus.PENDING:
            raise BusinessError("该评论已审核")
        self.status = ReviewStatus.APPROVED

    def reject(self) -> None:
        if self.status != ReviewStatus.PENDING:
            raise BusinessError("该评论已审核")
        self.status = ReviewStatus.REJECTED

    def is_visible(self) -> bool:
        return self.status == ReviewStatus.APPROVED
