"""Pydantic schemas for customers (PRD 6.2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import CustomerStatus


class CustomerBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    email: EmailStr
    status: CustomerStatus = CustomerStatus.active
    plan_id: uuid.UUID | None = None
    stripe_customer_id: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    status: CustomerStatus | None = None
    plan_id: uuid.UUID | None = None
    stripe_customer_id: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    currency: str


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    contact_name: str | None
    email: EmailStr
    status: CustomerStatus
    plan_id: uuid.UUID | None
    plan: PlanRead | None = None
    stripe_customer_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
