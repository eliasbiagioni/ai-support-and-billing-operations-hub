"""Customers API router (PRD 10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import Page
from app.schemas.customer import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Page[CustomerRead])
def list_customers(
    pagination: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[CustomerRead]:
    items, total = CustomerService(db).list_customers(
        limit=pagination.limit, offset=pagination.offset
    )
    return Page[CustomerRead](
        items=[CustomerRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CustomerRead:
    customer = CustomerService(db).create_customer(payload)
    return CustomerRead.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CustomerRead:
    customer = CustomerService(db).get_customer(customer_id)
    return CustomerRead.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CustomerRead:
    customer = CustomerService(db).update_customer(customer_id, payload)
    return CustomerRead.model_validate(customer)
