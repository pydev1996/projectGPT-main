from typing import Union, Any
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.config import settings
from pydantic import ValidationError
from app.database import get_database
from app.schemas import TokenPayload, User
from motor.motor_asyncio import AsyncIOMotorCollection

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login",
    scheme_name="JWT"
)


async def get_current_user(token: str = Depends(reuseable_oauth)) -> User:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        # Convert minutes to a timedelta object
        expire_duration = timedelta(minutes=expire_minutes)
        
        if datetime.fromtimestamp(token_data.iat) < datetime.now() - expire_duration:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    db = get_database()
    users: AsyncIOMotorCollection = db['clients']
    user = await users.find_one({"email": token_data.email})
    
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )
    
    return user