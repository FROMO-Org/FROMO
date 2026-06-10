from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import Profile
from app.schemas import CreateProfileBody, UpdateProfileBody

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/me")
def create_my_profile(
    body: CreateProfileBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    existing = session.query(Profile).filter(Profile.id == user["sub"]).first()
    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists")

    profile = Profile(
        id=user["sub"],
        email=user["email"],
        full_name=body.full_name,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/me")
def get_my_profile(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    profile = session.query(Profile).filter(Profile.id == user["sub"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/me")
def update_my_profile(body: UpdateProfileBody, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    profile = session.query(Profile).filter(Profile.id == user["sub"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if body.full_name is not None:
        profile.full_name = body.full_name
    if body.user_type is not None:
        profile.user_type = body.user_type

    session.commit()
    session.refresh(profile)
    return profile
