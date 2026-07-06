from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.security import decode_access_token
from app.database import get_session
from app.models import OrganisationMember

security = HTTPBearer()

# This is authintification and authorization. Used in schemas for checking if it is a right user.
# Also checkes for being an admin of organisation.

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


def require_org_role(role: str | None = None):
    def dependency(
        user: dict = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> OrganisationMember:
        member = session.query(OrganisationMember).filter(
            OrganisationMember.user_id == user["sub"]
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organisation membership required",
            )
        if role is not None and member.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return member
    return dependency


def require_organisation_member(
    session: Session,
    user_id: str,
    organisation_id: UUID,
    role: str | None = None,
) -> OrganisationMember:
    member = session.query(OrganisationMember).filter(
        OrganisationMember.user_id == user_id,
        OrganisationMember.organisation_id == organisation_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organisation membership required",
        )
    if role is not None and member.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' required",
        )
    return member
