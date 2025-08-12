from pydantic import BaseModel
from typing import Optional
from datetime import date
from enum import Enum


class PaymentStatus(str, Enum):
    paid = "paid"
    due = "due"


class ModeOfPayment(str, Enum):
    upi = "upi"
    cash = "cash"


class TicketCreate(BaseModel):
    ticket_number: int
    buyer_name: str
    buyer_phone: str
    seller_name: str
    payment_status: PaymentStatus  # Enum
    mode_of_payment: ModeOfPayment  # Enum
    date_sold: date
    date_of_payment: Optional[date] = None
    remarks: Optional[str] = ""
