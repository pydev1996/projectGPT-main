from app.error_constants import USER_NOT_FOUND
from fastapi import APIRouter, Depends, status, Header, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_database
from app.schemas import TokenSchema, User, UserAuth, UserOut
from app.utils import create_access_token, create_refresh_token, get_hashed_password, verify_header, verify_password, verify_refresh_token_and_return_email
from uuid import uuid4
from app.deps import get_current_user
from motor.motor_asyncio import AsyncIOMotorCollection

user_router = APIRouter()

@user_router.get('/', response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url='/docs')

@user_router.get('/me', summary='Get details of currently logged in user', response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user

@user_router.post('/signup', summary="Create new user", response_model=UserOut)
async def create_user(data: UserAuth):
    db = get_database()
    users: AsyncIOMotorCollection = db['clients']

    # querying database to check if user already exists
    user = await users.find_one({"email": data.email})
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # saving user to the database
    user = {
        'email': data.email,
        'name': data.name,
        'password': get_hashed_password(data.password),
        'id': str(uuid4())
        
    }
    result = await users.insert_one(user)
    user["_id"] = result.inserted_id
    return user



@user_router.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    
    print("--------------------------Logger-----------------")
    users: AsyncIOMotorCollection = db['clients']

    # querying database to check if user already exists
    user = await users.find_one({"email": form_data.username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user['password']
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    return {
        "name": user['name'],
        "email": user['email'],
        "access_token": create_access_token(user['email']),
        "refresh_token": create_refresh_token(user['email']),
    }


@user_router.get("/check-email", summary="Check if email exists in the database", response_model=bool)
async def check_email(email: str):
    db = get_database()
    users: AsyncIOMotorCollection = db['clients']
    user = await users.find_one({"email": email})
    return user is not None


@user_router.post("/refresh-token",
                  response_model=TokenSchema)
async def refresh_token(refresh_token: str = Header(None)):
    verify_header(refresh_token)
    user_email = verify_refresh_token_and_return_email(refresh_token)
    db = get_database()
    users: AsyncIOMotorCollection = db['clients']
    user = await find_user_db(user_email, users)
    check_user_does_not_exist(user, user_email)
    return {
        "access_token": create_access_token(user["email"]),
        "refresh_token": create_refresh_token(user["email"]),
    }

def check_user_does_not_exist(user, user_email):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{USER_NOT_FOUND} : {user_email}",
        )

async def find_user_db(email: str, users: AsyncIOMotorCollection):
    user = await users.find_one({"email": email})
    return user


