from pydantic import BaseModel, ConfigDict

class BPCreate(BaseModel):
    bp_id: str
    name: str

class BPResponse(BaseModel):
    bp_id: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class BankCreate(BaseModel):
    bp_id: str
    account_number: str
    bank_code: str


class BankResponse(BaseModel):
    id: int
    bp_id: str
    account_number: str
    bank_code: str

    model_config = ConfigDict(from_attributes=True)


class ValidateRequest(BaseModel):
    bukrs: str
    zterm: str
    mwskz: str
    bankl: str
