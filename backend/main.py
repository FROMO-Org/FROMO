from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.database.schema_sync import ensure_minimum_schema
from app.routers import all_routers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def get_root():
    return {"message": "it is working"}

# Checking for deployment
@app.get("/health")
def check_if_working():
    return {"status": "ok"}


@app.on_event("startup")
def sync_schema():
    ensure_minimum_schema(engine)


for router in all_routers:
    app.include_router(router)
