from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CommerceContext:
    customer_id: str
    query: str
    product_id: str | None = None
    quantity: int = 1


class ProductAgent:
    name = "product-intelligence"

    def inspect(self, context: CommerceContext) -> dict[str, Any]:
        return {
            "agent": self.name,
            "matched_product": context.product_id or "demo-product-001",
            "query": context.query,
            "catalog_status": "available",
        }


class CustomerAgent:
    name = "customer-intelligence"

    def inspect(self, context: CommerceContext) -> dict[str, Any]:
        return {
            "agent": self.name,
            "customer_id": context.customer_id,
            "profile_status": "known" if context.customer_id != "guest" else "guest",
            "personalization": "standard",
        }


class InventoryAgent:
    name = "inventory-intelligence"

    def inspect(self, context: CommerceContext) -> dict[str, Any]:
        stock = 24
        return {
            "agent": self.name,
            "stock_available": stock,
            "requested_quantity": context.quantity,
            "availability": "in_stock" if stock >= context.quantity else "insufficient_stock",
        }


class FinanceAgent:
    name = "commerce-finance"

    def inspect(self, context: CommerceContext) -> dict[str, Any]:
        unit_price = 129.99
        subtotal = round(unit_price * context.quantity, 2)
        return {
            "agent": self.name,
            "currency": "USD",
            "unit_price": unit_price,
            "subtotal": subtotal,
            "payment_required": True,
        }


class OrderAgent:
    name = "order-management"

    def inspect(self, context: CommerceContext, inventory: dict[str, Any]) -> dict[str, Any]:
        return {
            "agent": self.name,
            "order_readiness": "ready" if inventory["availability"] == "in_stock" else "blocked",
            "next_state": "checkout" if inventory["availability"] == "in_stock" else "backorder_review",
        }


class CommerceOrchestrator:
    """Coordinates commerce intelligence without performing external transactions."""

    def __init__(self) -> None:
        self.product = ProductAgent()
        self.customer = CustomerAgent()
        self.inventory = InventoryAgent()
        self.finance = FinanceAgent()
        self.order = OrderAgent()

    def plan(self, context: CommerceContext) -> dict[str, Any]:
        product = self.product.inspect(context)
        customer = self.customer.inspect(context)
        inventory = self.inventory.inspect(context)
        finance = self.finance.inspect(context)
        order = self.order.inspect(context, inventory)

        can_checkout = inventory["availability"] == "in_stock"
        decision = "READY_FOR_CHECKOUT" if can_checkout else "HOLD"

        return {
            "mode": "commerce-intelligence",
            "simulation_only": True,
            "decision": decision,
            "customer": customer,
            "product": product,
            "inventory": inventory,
            "finance": finance,
            "order": order,
            "trace": [
                "customer.requested",
                "product.matched",
                "inventory.checked",
                "finance.calculated",
                "order.evaluated",
                "decision.recorded",
            ],
            "external_action": None,
        }
