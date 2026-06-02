from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.schemas import UserCreate
from app.common.deps import get_db
from app.common.response import success

router = APIRouter(prefix='/api/auth', tags=['认证'])

@router.post('/register', status_code=201)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await service.register(db, user_create)
    return success(data=user.model_dump(), message='注册成功')