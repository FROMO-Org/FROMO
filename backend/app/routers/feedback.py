from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import Event, Feedback
from app.schemas import CreateFeedbackBody, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse)
def create_feedback(
    body: CreateFeedbackBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if body.event_id is not None:
        event = session.query(Event).filter(Event.id == body.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    feedback = Feedback(
        user_id=user["sub"],
        event_id=body.event_id,
        feature=body.feature,
        rating=body.rating,
        comment=body.comment,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback
