from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import bcrypt
from models.user import User
from schemas.user import UserCreate, UserUpdate



# password helpers
def hash_password(plain:str)->str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain:str, hashed:str)->bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

# Read operations
def get_user(db:Session, user_id:int)->User:
    """Fetch by primary key or raise 404"""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

def get_user_by_email(db:Session, email:str)->User | None:
    return db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

def get_user_by_username(db:Session, username:str)->User:
    return db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    

def list_users(
    db:Session,
    skip:int = 0,
    limit:int = 100,
    sort_by:str = "id",
    sort_order:str = "asc"
)->list[User]:
    sort_column = getattr(User, sort_by)
    order_expr = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    
    return(
        db.execute(
            select(User).order_by(order_expr).offset(skip).limit(limit)
        ).scalars()
        .all()
    )

def search_users(
    db:Session,
    username_contains:str | None = None,
    is_active: bool | None = None,
    sort_by:str = "asc",
    sort_order:str = "asc",
    skip:int = 0,
    limit: int = 100,
) -> list[User]:
    """Filter + sort + paginate. All filters are optional; None means 'no filter'"""
    stmt = select(User)
    
    if username_contains:
        stmt = stmt.where(User.username.ilike(f"%{username_contains}%"))
    
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    
    sort_column = getattr(User, sort_by)
    stmt = stmt.order_by(
        sort_column.asc() if sort_order == "asc" else sort_column.desc()
    )
    
    # pagination
    stmt = stmt.offset(skip).limit(limit)
    
    return db.execute(stmt).scalars().all()

# Write operations
def create_user(db: Session, payload: UserCreate)->User:
    """Register a new user. Raises 409 on duplicate email/username."""
    
    # Fast-path duplicate check (nice error message for the common case)
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= "Email already registered"
        )
    
    if get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= "Username already taken"
        )
    
    user = User(
        email = payload.email,
        username = payload.username, 
        full_name = payload.full_name,
        hashed_password = hash_password(payload.password)
    )
    db.add(user)
    
     # Correctness check — the pre-checks above can race. UNIQUE constraints
    # are the actual guarantee; this catches the loser of the race.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail= "Email or username already exist"
        )
    db.refresh(user)
    return user

def update_user(db:Session, user: User, payload: UserUpdate) ->User:
    """
    PATCH semantics - update only fields that client sent. A field omitted from JSON is left untouched. A field explicitly sent as null clears it (for nullable fields)
    """
    update_data = payload.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"] is not None:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    else:
        update_data.pop("password", None) # discard null passwords silently
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "Email or username already exist"
        )
    
    db.refresh(user)
    return user


def replace_user(db:Session, user: User, payload: UserCreate)->User:
    """
    PUT semantics — full replacement of mutable fields.
    Because UserCreate has required email/username/password, the client
    MUST send them; omitting any is a 422.
    """
    update_payload = UserUpdate(
        email = payload.email,
        username = payload.username,
        full_name = payload.full_name,
        password= payload.password
    )
    
    return update_user(db, user, update_payload)


def soft_delete_user(db:Session, user:User)->None:
    """Flip is_active=False. Row remains for FK integrity + audit."""
    user.is_active = False
    db.commit()


def hard_delete_user(db: Session, user: User)->None:
    """Actual DELETE row. Use with care — breaks FKs in real apps."""
    db.delete(user)
    db.commit()