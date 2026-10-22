import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models
from .schemas import (
    ApplicationCreate, ApplicationRead, ApplicationStatusUpdate,
    SimulationRequest, SimulationRead
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for a demo starter. Use Alembic migrations before production use.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="ALFA PULSE API",
    description="Демонстрационный backend кредитного навигатора ALFA PULSE. Не является банковской системой.",
    version="0.1.0",
    lifespan=lifespan,
)

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "ALFA PULSE API", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/applications", response_model=ApplicationRead, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    item = models.Application(**payload.model_dump(), status="submitted")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/api/applications", response_model=list[ApplicationRead])
def list_applications(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(models.Application).order_by(models.Application.created_at.desc())
    if status:
        stmt = stmt.where(models.Application.status == status)
    return list(db.scalars(stmt.offset(offset).limit(limit)).all())

@app.get("/api/applications/{application_id}", response_model=ApplicationRead)
def get_application(application_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Application, application_id)
    if not item:
        raise HTTPException(status_code=404, detail="Application not found")
    return item

@app.patch("/api/applications/{application_id}/status", response_model=ApplicationRead)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
):
    item = db.get(models.Application, application_id)
    if not item:
        raise HTTPException(status_code=404, detail="Application not found")
    item.status = payload.status
    if payload.notes is not None:
        item.notes = payload.notes
    db.commit()
    db.refresh(item)
    return item

@app.post("/api/finance/simulate", response_model=SimulationRead)
def simulate_finance(payload: SimulationRequest):
    # Simplified annuity estimate for a product demo, not an underwriting decision.
    monthly_rate = payload.annual_rate_percent / 100 / 12
    if monthly_rate == 0:
        payment = payload.amount / payload.term_months
    else:
        factor = (1 + monthly_rate) ** payload.term_months
        payment = payload.amount * monthly_rate * factor / (factor - 1)
    total = payment * payload.term_months
    before = payload.monthly_revenue - payload.monthly_expenses - payload.existing_monthly_debt
    after = before - payment
    if after < 0:
        status = "cash_gap_risk"
    elif after < payload.monthly_revenue * 0.1:
        status = "low_buffer"
    else:
        status = "positive_buffer"
    return SimulationRead(
        estimated_monthly_payment=round(payment, 2),
        estimated_total_repayment=round(total, 2),
        estimated_interest=round(total - payload.amount, 2),
        monthly_cash_before_new_loan=round(before, 2),
        monthly_cash_after_new_loan=round(after, 2),
        cash_flow_status=status,
        disclaimer="Демо-расчёт по упрощённой аннуитетной формуле. Не является кредитным решением или банковским предложением.",
    )
