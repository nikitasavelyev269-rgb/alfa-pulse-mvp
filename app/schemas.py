from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_PRODUCTS = {"working_capital", "overdraft"}
ALLOWED_STATUSES = {
    "submitted",
    "in_review",
    "need_documents",
    "offer_ready",
    "approved_demo",
    "rejected_demo",
    "contract_demo",
    "disbursed_demo",
}


class ApplicationCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    inn: str | None = Field(default=None, min_length=10, max_length=12)
    product_type: str
    purpose: str = Field(min_length=3, max_length=300)
    amount: float = Field(gt=0, le=100_000_000)
    term_months: int = Field(ge=1, le=120)
    monthly_revenue: float | None = Field(default=None, ge=0, le=1_000_000_000)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("product_type")
    @classmethod
    def product_must_be_supported(cls, value):
        if value not in ALLOWED_PRODUCTS:
            raise ValueError(
                f"product_type must be one of: {', '.join(sorted(ALLOWED_PRODUCTS))}"
            )
        return value


class ApplicationStatusUpdate(BaseModel):
    status: str
    staff_comment: str | None = Field(default=None, max_length=5000)
    # Retain compatibility with earlier clients; client notes stay separate.
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("status")
    @classmethod
    def status_must_be_supported(cls, value):
        if value not in ALLOWED_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}"
            )
        return value


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    inn: str | None
    product_type: str
    purpose: str
    amount: float
    term_months: int
    monthly_revenue: float | None
    status: str
    notes: str | None
    staff_comment: str | None = None
    created_at: datetime
    updated_at: datetime


class SimulationRequest(BaseModel):
    amount: float = Field(gt=0, le=100_000_000)
    annual_rate_percent: float = Field(ge=0, le=100, default=24)
    term_months: int = Field(ge=1, le=120)
    monthly_revenue: float = Field(ge=0, le=1_000_000_000)
    monthly_expenses: float = Field(ge=0, le=1_000_000_000)
    existing_monthly_debt: float = Field(ge=0, le=1_000_000_000, default=0)


class SimulationRead(BaseModel):
    estimated_monthly_payment: float
    estimated_total_repayment: float
    estimated_interest: float
    monthly_cash_before_new_loan: float
    monthly_cash_after_new_loan: float
    cash_flow_status: str
    disclaimer: str
