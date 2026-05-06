from fastapi import APIRouter

router = APIRouter()

@router.post("/oauth/token")
def get_token():
    return {
        "access_token": "dummy-token",
        "token_type": "bearer"
    }