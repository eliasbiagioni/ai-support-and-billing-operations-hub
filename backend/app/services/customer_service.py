"""Business rules for customers. Keeps routes thin (PRD 10.2)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CustomerRepository(db)

    def list_customers(self, *, limit: int, offset: int) -> tuple[list[Customer], int]:
        return self.repo.list(limit=limit, offset=offset)

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.repo.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return customer

    def create_customer(self, payload: CustomerCreate) -> Customer:
        customer = Customer(**payload.model_dump())
        self.repo.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update_customer(self, customer_id: int, payload: CustomerUpdate) -> Customer:
        customer = self.get_customer(customer_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        self.db.commit()
        self.db.refresh(customer)
        return customer
