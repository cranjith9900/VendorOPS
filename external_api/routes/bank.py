from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/bank")

@router.post("/", response_model=schemas.BankResponse)
def add_bank(data: schemas.BankCreate, db: Session = Depends(get_db)):
    bank = models.BankAccount(**data.model_dump())
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank

@router.get("/{bp_id}", response_model=List[schemas.BankResponse])
def get_banks(bp_id: str, db: Session = Depends(get_db)):
    return db.query(models.BankAccount).filter_by(bp_id=bp_id).all()
