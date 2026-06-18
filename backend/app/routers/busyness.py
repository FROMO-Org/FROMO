import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import BusynessArea, BusynessScore

router = APIRouter(prefix="/busyness", tags=["busyness"])

EARTH_RADIUS_KM = 6371


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1, lng1, lat2, lng2 = map(
        lambda value: math.radians(float(value)),
        [lat1, lng1, lat2, lng2],
    )
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def area_dict(area: BusynessArea) -> dict:
    return {
        "id": area.id,
        "name": area.name,
        "lat": float(area.lat),
        "lng": float(area.lng),
        "radius_metres": area.radius_metres,
        "created_at": area.created_at,
    }


def score_dict(score: BusynessScore | None) -> dict | None:
    if score is None:
        return None

    return {
        "id": score.id,
        "area_id": score.area_id,
        "observed_at": score.observed_at,
        "local_day_of_week": score.local_day_of_week,
        "local_hour": score.local_hour,
        "score": float(score.score),
        "level": score.level,
        "confidence": float(score.confidence) if score.confidence is not None else None,
        "source": score.source,
        "is_prediction": score.is_prediction,
        "updated_at": score.updated_at,
    }


def latest_score_for_area(
    session: Session,
    area_id: UUID,
    day_of_week: int | None = None,
    hour: int | None = None,
    is_prediction: bool | None = None,
) -> BusynessScore | None:
    query = session.query(BusynessScore).filter(BusynessScore.area_id == area_id)

    if day_of_week is not None:
        query = query.filter(BusynessScore.local_day_of_week == day_of_week)
    if hour is not None:
        query = query.filter(BusynessScore.local_hour == hour)
    if is_prediction is not None:
        query = query.filter(BusynessScore.is_prediction == is_prediction)

    return query.order_by(BusynessScore.observed_at.desc()).first()


@router.get("/areas")
def get_busyness_areas(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    areas = (
        session.query(BusynessArea)
        .order_by(BusynessArea.name)
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [area_dict(area) for area in areas]


@router.get("/areas/{area_id}/scores")
def get_busyness_scores_by_area_id(
    area_id: UUID,
    day_of_week: int | None = Query(default=None, ge=0, le=6),
    hour: int | None = Query(default=None, ge=0, le=23),
    is_prediction: bool | None = None,
    limit: int = Query(default=24, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    if (day_of_week is None) != (hour is None):
        raise HTTPException(status_code=400, detail="day_of_week and hour must be provided together")

    area = session.query(BusynessArea).filter(BusynessArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Busyness area not found")

    query = session.query(BusynessScore).filter(BusynessScore.area_id == area_id)

    if day_of_week is not None:
        query = query.filter(BusynessScore.local_day_of_week == day_of_week)
    if hour is not None:
        query = query.filter(BusynessScore.local_hour == hour)
    if is_prediction is not None:
        query = query.filter(BusynessScore.is_prediction == is_prediction)

    scores = (
        query.order_by(BusynessScore.observed_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return {
        "area": area_dict(area),
        "scores": [score_dict(score) for score in scores],
    }


@router.get("/nearby")
def get_busyness_nearby(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=5, gt=0, le=50),
    day_of_week: int | None = Query(default=None, ge=0, le=6),
    hour: int | None = Query(default=None, ge=0, le=23),
    is_prediction: bool | None = None,
    include_empty: bool = True,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    if (day_of_week is None) != (hour is None):
        raise HTTPException(status_code=400, detail="day_of_week and hour must be provided together")

    points = []

    for area in session.query(BusynessArea).all():
        distance_km = haversine_km(lat, lng, area.lat, area.lng)
        if distance_km > radius_km:
            continue

        score = latest_score_for_area(session, area.id, day_of_week, hour, is_prediction)

        if score is None and not include_empty:
            continue

        points.append({
            "area": area_dict(area),
            "score": score_dict(score),
            "distance_km": round(distance_km, 2),
        })

    points.sort(key=lambda point: point["distance_km"])

    return {
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "day_of_week": day_of_week,
        "hour": hour,
        "is_prediction": is_prediction,
        "areas": points[:limit],
    }