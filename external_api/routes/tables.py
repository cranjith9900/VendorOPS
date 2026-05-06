from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/tables")

@router.get("/T001/{bukrs}")
def get_company(bukrs: str, db: Session = Depends(get_db)):
    return db.query(models.T001).filter_by(bukrs=bukrs).first()

@router.get("/T052/{zterm}")
def get_payment_term(zterm: str, db: Session = Depends(get_db)):
    return db.query(models.T052).filter_by(zterm=zterm).first()

@router.get("/T007A/{mwskz}")
def get_tax(mwskz: str, db: Session = Depends(get_db)):
    return db.query(models.T007A).filter_by(mwskz=mwskz).first()

@router.get("/BNKA/{bankl}")
def get_bank(bankl: str, db: Session = Depends(get_db)):
    return db.query(models.BNKA).filter_by(bankl=bankl).first()

@router.post("/validate")
def validate(data: schemas.ValidateRequest, db: Session = Depends(get_db)):
    company = db.query(models.T001).filter_by(bukrs=data.bukrs).first()
    payment = db.query(models.T052).filter_by(zterm=data.zterm).first()
    tax = db.query(models.T007A).filter_by(mwskz=data.mwskz).first()
    bank = db.query(models.BNKA).filter_by(bankl=data.bankl).first()

    if not all([company, payment, tax, bank]):
        return {"status": "INVALID"}

    return {"status": "VALID"}
