"""
Feedback routes for bug reports and feature suggestions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.conn import get_db
from app.models.feedback import Feedback
from app.models.user import User, UserRole
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    FeedbackStats
)
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("", response_model=List[FeedbackResponse])
async def list_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type_filter: Optional[str] = Query(None, alias="type", pattern="^(bug|feature)$"),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|votes|updated_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all feedback with optional filters"""
    query = select(Feedback).options(selectinload(Feedback.user))
    
    # Apply filters
    if type_filter:
        query = query.where(Feedback.type == type_filter)
    
    if status_filter:
        query = query.where(Feedback.status == status_filter)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Feedback.title.ilike(search_filter),
                Feedback.description.ilike(search_filter)
            )
        )
    
    # Sorting
    order_col = getattr(Feedback, sort_by)
    if order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    return feedbacks


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback statistics"""
    # Total count
    total_result = await db.execute(select(func.count(Feedback.id)))
    total = total_result.scalar() or 0
    
    # Count by status
    open_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.status == "open"))
    open_count = open_result.scalar() or 0
    
    in_progress_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.status == "in_progress"))
    in_progress = in_progress_result.scalar() or 0
    
    resolved_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.status == "resolved"))
    resolved = resolved_result.scalar() or 0
    
    closed_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.status == "closed"))
    closed = closed_result.scalar() or 0
    
    # Count by type
    bugs_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.type == "bug"))
    bugs = bugs_result.scalar() or 0
    
    features_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.type == "feature"))
    features = features_result.scalar() or 0
    
    # Top voted (limit 5)
    top_voted_result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.user))
        .order_by(Feedback.votes.desc())
        .limit(5)
    )
    top_voted = top_voted_result.scalars().all()
    
    return FeedbackStats(
        total=total,
        open=open_count,
        in_progress=in_progress,
        resolved=resolved,
        closed=closed,
        bugs=bugs,
        features=features,
        top_voted=top_voted
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific feedback by ID"""
    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.user))
        .where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    return feedback


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new feedback (bug report or feature suggestion)"""
    new_feedback = Feedback(
        **feedback_data.model_dump(),
        user_id=current_user.id,
        status="open",
        votes=0
    )
    
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    # Load user relationship
    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.user))
        .where(Feedback.id == new_feedback.id)
    )
    new_feedback = result.scalar_one()
    
    return new_feedback


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    feedback_data: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update feedback status/priority (admin/manager only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and managers can update feedback"
        )
    
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    update_data = feedback_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback, field, value)
    
    await db.commit()
    await db.refresh(feedback)
    
    # Load user relationship
    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.user))
        .where(Feedback.id == feedback.id)
    )
    feedback = result.scalar_one()
    
    return feedback


@router.post("/{feedback_id}/vote", response_model=FeedbackResponse)
async def vote_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vote on feedback (upvote)"""
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    feedback.votes += 1
    await db.commit()
    await db.refresh(feedback)
    
    # Load user relationship
    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.user))
        .where(Feedback.id == feedback.id)
    )
    feedback = result.scalar_one()
    
    return feedback


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete feedback (admin only or own feedback)"""
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Only admin or feedback owner can delete
    if current_user.role != UserRole.ADMIN and feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own feedback"
        )
    
    await db.delete(feedback)
    await db.commit()
    
    return None
