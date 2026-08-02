"""Order calculation and persistence helpers."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, SplitPayment


@dataclass
class CartLine:
    """A menu item held in the current in-memory cart."""

    menu_item_id: int
    item_name: str
    unit_price: float
    quantity: int = 1
    note: str | None = None


@dataclass
class Discount:
    """The one optional discount applied to an order."""

    kind: str
    value: float
    scope: str = "order"
    menu_item_id: int | None = None


def calculate_order_totals(
    lines: list[CartLine],
    discount: Discount | None = None,
) -> tuple[float, float, float]:
    """Return subtotal, discount amount, and final total for cart lines."""
    if not lines or any(line.quantity <= 0 for line in lines):
        raise ValueError("An order must contain at least one item.")

    subtotal = round(sum(line.unit_price * line.quantity for line in lines), 2)
    if discount is None:
        return subtotal, 0.0, subtotal

    if discount.kind not in {"flat", "percentage"}:
        raise ValueError("Unknown discount type.")
    if discount.scope not in {"order", "item"}:
        raise ValueError("Unknown discount scope.")
    if discount.value < 0:
        raise ValueError("Discount cannot be negative.")

    discount_base = subtotal
    if discount.scope == "item":
        line = next((line for line in lines if line.menu_item_id == discount.menu_item_id), None)
        if line is None:
            raise ValueError("Discounted item is not in the cart.")
        discount_base = round(line.unit_price * line.quantity, 2)

    if discount.kind == "flat":
        discount_amount = round(discount.value, 2)
    else:
        discount_amount = round(discount_base * discount.value / 100, 2)

    if discount_amount > discount_base:
        raise ValueError("Discount cannot exceed the bill value.")

    return subtotal, discount_amount, round(subtotal - discount_amount, 2)


def validate_payment(
    payment_mode: str,
    total: float,
    split_payments: dict[str, float] | None = None,
) -> None:
    """Validate that a split payment equals the final payable amount."""
    if payment_mode not in {"Cash", "UPI", "Split"}:
        raise ValueError("Unknown payment method.")

    if payment_mode != "Split":
        return

    if split_payments is None:
        raise ValueError("Payment mismatch.")
    if any(amount < 0 for amount in split_payments.values()):
        raise ValueError("Payment mismatch.")
    if abs(sum(split_payments.values()) - total) > 0.01:
        raise ValueError("Payment mismatch.")


def next_bill_number(session: Session, order_date: str) -> int:
    """Return the next bill number for a local calendar date."""
    largest_bill_number = session.scalar(
        select(func.max(Order.bill_number)).where(Order.order_date == order_date)
    )
    return (largest_bill_number or 0) + 1


def save_order(
    session: Session,
    lines: list[CartLine],
    discount: Discount | None,
    payment_mode: str,
    split_payments: dict[str, float] | None = None,
    completed_at: datetime | None = None,
    service_type: str = "Dine In",
) -> Order:
    """Save a completed, immutable order and its historical item snapshots."""
    subtotal, discount_amount, total = calculate_order_totals(lines, discount)
    validate_payment(payment_mode, total, split_payments)

    completed_at = completed_at or datetime.now()
    order_date = completed_at.date().isoformat()
    order = Order(
        bill_number=next_bill_number(session, order_date),
        order_date=order_date,
        order_time=completed_at.strftime("%H:%M:%S"),
        service_type=service_type,
        payment_mode=payment_mode,
        subtotal=subtotal,
        discount_type=_discount_type(discount),
        discount_value=discount.value if discount else None,
        total=total,
    )
    session.add(order)
    session.flush()

    for line in lines:
        session.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=line.menu_item_id,
                item_name=line.item_name,
                quantity=line.quantity,
                unit_price=line.unit_price,
                note=line.note,
            )
        )

    if payment_mode == "Split" and split_payments is not None:
        for mode, amount in split_payments.items():
            if amount > 0:
                session.add(SplitPayment(order_id=order.id, payment_mode=mode, amount=amount))

    session.flush()
    return order


def _discount_type(discount: Discount | None) -> str | None:
    """Store the discount type and scope using the existing text column."""
    if discount is None:
        return None
    return f"{discount.kind}_{discount.scope}"
