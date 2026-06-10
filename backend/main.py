from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


for router in all_routers:
    app.include_router(router)
