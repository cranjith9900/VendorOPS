from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/business_partner")

@router.post("/")
def create_bp(bp: schemas.BPCreate, db: Session = Depends(get_db)):
    obj = models.BusinessPartner(bp_id=bp.bp_id, name=bp.name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/{bp_id}")
def get_bp(bp_id: str, db: Session = Depends(get_db)):
    return db.query(models.BusinessPartner).filter_by(bp_id=bp_id).first()