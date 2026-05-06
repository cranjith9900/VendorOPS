from fastapi import FastAPI
from database import Base, engine
from routes import oauth, business_partner, bank, tables

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SAP Adapter API",
    description="API endpoints for SAP adapter business partner, bank, and table validation flows.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
def read_root():
    return {"status": "SAP adapter API is running"}


app.include_router(oauth.router)
app.include_router(business_partner.router)
app.include_router(bank.router)
app.include_router(tables.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
