from typing import Literal
from fastapi import APIRouter,Depends,Query, status
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.user import UserCreate, UserUpdate, Userout
from services import user_service

router = APIRouter(prefix="/users", tags=["users"])

# POST /users - register
@router.post("", response_model=Userout, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, payload)

@router.get("/search", response_model=list[Userout])
def search_users(
    username_contains:str | None = Query(
        None, description="Case-insensitive substring match on username"
    ),
    is_active: bool | None = Query(
        None, description = "Filter by active status (omit = both)"
    ),
    
    sort_by:Literal["id","created_at","username","email"] = "id",
    sort_order:Literal["asc", "desc"] = "asc",
    skip:int = Query(0, ge=0),
    limit:int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return user_service.search_users(
        db,
        username_contains=username_contains,
        sort_by= sort_by,
        skip = skip,
        limit = limit,
    )

# GET /users - list with sort + pagination
@router.get("", response_model=list[Userout])
def list_users(
    sort_by: Literal["id", "created_at", "username", "email"]  = "id",
    sort_order: Literal["asc", "desc"] = "asc",
    skip:int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return user_service.list_users(
        db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order
    )


# GET /users/{user_id} — by primary key
@router.get("/{user_id}", response_model=Userout)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user(db, user_id)


# PATCH /users/{user_id} — partial update
@router.patch("/{user_id}", response_model=Userout)
def patch_user(
    user_id: int,
    payload:UserUpdate,
    db: Session = Depends(get_db)
):
    user = user_service.get_user(db, user_id)
    return user_service.update_user(db, user, payload)


@router.put("/{user_id}", response_model=Userout)
def put_user(
    user_id: int,
    payload: UserCreate,
    db: Session = Depends(get_db)
):
    user = user_service.get_user(db, user_id)
    return user_service.replace_user(db, user, payload)


@router.delete("/{user_id}", status_code= status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    hard: bool = Query(False, description="Permanently delete the row"),
    db:Session = Depends(get_db)
):
    user = user_service.get_user(db, user_id)
    if hard: 
        user_service.hard_delete_user(db, user)
    else:
        user_service.soft_delete_user(db, user)
    return None