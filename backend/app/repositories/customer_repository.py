"""Data access for customers (PRD 12: repositories layer)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, customer_id: uuid.UUID) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def list(self, *, limit: int, offset: int) -> tuple[list[Customer], int]:
        total = self.db.scalar(select(func.count()).select_from(Customer)) or 0
        stmt = (
            select(Customer)
            .order_by(Customer.company_name)
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def add(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.flush()
        return customer

    def delete(self, customer: Customer) -> None:
        self.db.delete(customer)
        self.db.flush()
