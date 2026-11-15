from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token
from app.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.users.find_one({"email": payload["sub"]}, {"password_hash": 0, "_id": 0})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db = Depends(get_db)):
    existing = db.users.find_one({"email": user_in.email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user_doc = {
        "user_id": f"USR-{int(datetime.utcnow().timestamp())}",
        "name": user_in.name,
        "email": user_in.email,
        "password_hash": hash_password(user_in.password),
        "role": user_in.role or "Pharmacist",
        "created_at": datetime.utcnow()
    }
    db.users.insert_one(user_doc)
    return {"message": "User registered successfully", "email": user_in.email}

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db = Depends(get_db)):
    user = db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": user["email"], "role": user.get("role", "Pharmacist")})
    user_data = {
        "user_id": user.get("user_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role")
    }
    return {"access_token": token, "token_type": "bearer", "user": user_data}

@router.post("/token", response_model=TokenResponse)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["email"], "role": user.get("role", "Pharmacist")})
    user_data = {"name": user.get("name"), "email": user.get("email"), "role": user.get("role")}
    return {"access_token": token, "token_type": "bearer", "user": user_data}

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
