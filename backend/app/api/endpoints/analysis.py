from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get('/username/analysis/{gitname}')
async def get_anaylsis(gitname:str):
    return gitname