from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.common.deps import get_db, get_current_user
from app.common.response import success
from app.knowledge_base.schemas import KnowledgeBaseCreate
from app.knowledge_base import service as kb_service

router = APIRouter(prefix='/api/knowledge-bases', tags=['知识库'])

@router.post("", status_code=201)
async def create_knowledge_base(
        data: KnowledgeBaseCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    kb = await kb_service.create_knowledge_base(db, current_user.id, data)
    return success(data=kb.model_dump(), message="创建成功", code=201)

@router.get("")
async def list_knowledge_bases(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    kb_list = await kb_service.list_knowledge_bases(db, str(current_user.id))
    return success(data=[kb.model_dump() for kb in kb_list])

@router.get("/{kb_id}")
async def get_knowledge_base(
        kb_id: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    kb = await kb_service.get_knowledge_base(db, str(current_user.id), kb_id)
    return success(data=kb.model_dump())

@router.delete("/{kb_id}")
async def delete_knowledge_base(
        kb_id: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    await kb_service.delete_knowledge_base(db, str(current_user.id), kb_id)
    return success(message="删除成功")

@router.post("/{kb_id}/documents", status_code=201)
async def upload_document(
        kb_id: str,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    content = file.read()
    doc = await kb_service.upload_document(db, str(current_user.id), kb_id, file.filename, content)
    return success(data={
        "id": str(doc.id),
        "filename": doc.filename,
        'status': doc.status
    }, message="上传成功", code=201)

@router.get("/{kb_id}/documents")
async def list_documents(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = await kb_service.list_documents(db,current_user.id, kb_id)
    return success(data=[doc.model_dump() for doc in docs])

@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await kb_service.delete_document(db, str(current_user.id), kb_id, doc_id)
    return success(message='删除成功')
