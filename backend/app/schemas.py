from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

CATEGORIES = ["Stay", "Transport", "Food", "Activities", "Local travel", "Reserve"]
Category = Literal["Stay", "Transport", "Food", "Activities", "Local travel", "Reserve"]


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)


class UserPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=500)
    theme: Literal["system", "light", "dark"] | None = None
    notifications: dict[str, bool] | None = None
    current_password: str | None = Field(default=None, max_length=72)
    new_password: str | None = Field(default=None, min_length=8, max_length=72)


class TripIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    start_date: Date
    end_date: Date
    group_size: int = Field(ge=2, le=50)
    budget_total: int = Field(gt=0, le=1_000_000_000)
    currency: str = Field(min_length=3, max_length=3)
    deadline: Date | None = None
    description: str = Field(default="", max_length=1000)

    @field_validator("currency")
    @classmethod
    def upper(cls, v):
        return v.upper()

    @model_validator(mode="after")
    def dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class TripPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    destination: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: Date | None = None
    end_date: Date | None = None
    deadline: Date | None = None
    description: str | None = Field(default=None, max_length=1000)
    budget_total: int | None = Field(default=None, gt=0, le=1_000_000_000)
    status: Literal["active", "archived"] | None = None


class JoinIn(BaseModel):
    code: str = Field(min_length=4, max_length=32)


class MemberPatch(BaseModel):
    target_amount: int = Field(ge=0, le=1_000_000_000)


class BudgetSaveIn(BaseModel):
    categories: dict[str, int]


class OrderIn(BaseModel):
    amount: int = Field(gt=0)


class ExpenseIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    category: Category
    amount: int = Field(gt=0, le=1_000_000_000)
    date: Date
    paid_by: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=500)
    receipt_url: str | None = Field(default=None, max_length=500)


class ExpensePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    category: Category | None = None
    amount: int | None = Field(default=None, gt=0, le=1_000_000_000)
    date: Date | None = None
    paid_by: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    receipt_url: str | None = Field(default=None, max_length=500)


class AiBudgetIn(BaseModel):
    trip_id: str | None = None
    destination: str | None = Field(default=None, max_length=100)
    people: int | None = Field(default=None, ge=1, le=50)
    days: int | None = Field(default=None, ge=1, le=60)
    total: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    preferences: str = Field(default="", max_length=500)
    accommodation: str = Field(default="", max_length=100)
    transport: str = Field(default="", max_length=100)


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)
