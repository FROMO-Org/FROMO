from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models import Organisation, OrganisationMember, Event, Profile
from app.schemas import CreateMembershipBody, CreateOrganisationBody

router = APIRouter(prefix="/organisations", tags=["organisations"])


@router.post("/")
def create_organisation(
    body: CreateOrganisationBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    profile = session.query(Profile).filter(Profile.id == user["sub"]).first()
    if not profile:
        profile = Profile(
            id=user["sub"],
            email=user["email"],
            user_type="organiser",
        )
        session.add(profile)
    else:
        profile.user_type = "organiser"

    organisation = Organisation(name=body.name)
    session.add(organisation)
    session.flush()

    member = OrganisationMember(
        organisation_id=organisation.id,
        user_id=user["sub"],
        role="owner",
    )
    session.add(member)
    session.commit()
    session.refresh(organisation)
    session.refresh(member)

    return {
        "organisation": organisation,
        "membership": member,
    }


@router.get("/me")
def get_my_organisations(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.query(Organisation, OrganisationMember).join(
        OrganisationMember,
        Organisation.id == OrganisationMember.organisation_id,
    ).filter(
        OrganisationMember.user_id == user["sub"],
    ).all()

    return [
        {
            "organisation": organisation,
            "role": member.role,
            "joined_at": member.created_at,
        }
        for organisation, member in rows
    ]


@router.get("/{organisation_id}")
def get_organisation(organisation_id: UUID, session: Session = Depends(get_session)):
    organisation = session.query(Organisation).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return organisation


@router.get("/{organisation_id}/events")
def get_organisation_events(organisation_id: UUID, session: Session = Depends(get_session)):
    organisation = session.query(Organisation).filter(Organisation.id == organisation_id).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation not found")

    return session.query(Event).filter(Event.host_organisation_id == organisation_id).all()


@router.post("/{organisation_id}/members")
def add_organisation_member(
    organisation_id: UUID,
    body: CreateMembershipBody,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    requester = session.query(OrganisationMember).filter(
        OrganisationMember.organisation_id == organisation_id,
        OrganisationMember.user_id == user["sub"],
    ).first()
    if not requester or requester.role != "owner":
        raise HTTPException(status_code=403, detail="Only an owner of this organisation can add members")

    existing = session.query(OrganisationMember).filter(
        OrganisationMember.organisation_id == organisation_id,
        OrganisationMember.user_id == body.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member of this organisation")

    member = OrganisationMember(
        organisation_id=organisation_id,
        user_id=body.user_id,
        role=body.role,
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member
