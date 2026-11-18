from fastapi import FastAPI, Depends
from core.config import settings
from core.database import Base, engine, get_db
from api.user import router as users_router

# from api.user import User # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.include_router(users_router)

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

@app.get("/health/db")
def health_check(db = Depends(get_db)):
    from sqlalchemy import text
    db.execute(text("SELECT 1"))
    return {"status": "OK", "database":settings.DB_NAME}