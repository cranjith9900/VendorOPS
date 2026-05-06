from sqlalchemy import Column, String, Integer
from database import Base

class BusinessPartner(Base):
    __tablename__ = "business_partners"

    id = Column(Integer, primary_key=True, index=True)
    bp_id = Column(String, unique=True, index=True)
    name = Column(String)


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    bp_id = Column(String)
    account_number = Column(String)
    bank_code = Column(String)


class T001(Base):  # Company Code
    __tablename__ = "t001"
    bukrs = Column(String, primary_key=True)
    name = Column(String)


class T052(Base):  # Payment Terms
    __tablename__ = "t052"
    zterm = Column(String, primary_key=True)
    description = Column(String)


class T007A(Base):  # Tax Codes
    __tablename__ = "t007a"
    mwskz = Column(String, primary_key=True)
    rate = Column(Integer)


class BNKA(Base):  # Bank Master
    __tablename__ = "bnka"
    bankl = Column(String, primary_key=True)
    bank_name = Column(String)