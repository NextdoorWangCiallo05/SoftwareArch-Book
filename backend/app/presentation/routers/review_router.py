"""评论与评分路由（UC-017 / UC-018 / UC-021）。"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.application.review_service import ReviewService
from app.core.exceptions import PermissionDeniedError
from app.core.response import APIResponse, ok
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.presentation.dependencies import (
    get_current_account,
    get_review_service,
    require_role,
)


class ReviewSubmitRequest(BaseModel):
    title_id: int
    rating: int
    comment: str | None = Field(default=None, max_length=1000)


class ModerateRequest(BaseModel):
    decision: str  # APPROVED / REJECTED


router = APIRouter(tags=["评论与评分"])


@router.post("/api/reviews", response_model=APIResponse)
def submit_review(
    req: ReviewSubmitRequest,
    service: ReviewService = Depends(get_review_service),
    account: Account = Depends(require_role(Role.READER)),
) -> APIResponse:
    reader_id = service.reader_id_of_account(account.id)
    if reader_id is None:
        raise PermissionDeniedError("读者信息不存在")

    result = service.submit(reader_id, req.title_id, req.rating, req.comment)
    return ok(data=result, message="评论已提交，待审核")


@router.get("/api/reviews", response_model=APIResponse)
def list_reviews(
    title_id: int = Query(...),
    service: ReviewService = Depends(get_review_service),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    result = service.list_approved(title_id)
    return ok(data=result)


@router.get("/api/reviews/pending", response_model=APIResponse)
def list_pending_reviews(
    service: ReviewService = Depends(get_review_service),
    account: Account = Depends(require_role(Role.ADMIN)),
) -> APIResponse:
    """待审核评论列表（UC-021）。`list_reviews` 只返回已公开评论，审核需另取。"""
    return ok(data=service.list_pending())


@router.post("/api/reviews/{review_id}/moderate", response_model=APIResponse)
def moderate_review(
    review_id: int,
    req: ModerateRequest,
    service: ReviewService = Depends(get_review_service),
    account: Account = Depends(require_role(Role.ADMIN)),
) -> APIResponse:
    result = service.moderate(review_id, req.decision)
    return ok(data=result, message="审核完成")
