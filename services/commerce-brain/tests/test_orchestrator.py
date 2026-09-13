from services.commerce_brain.app.orchestrator import CommerceContext, CommerceOrchestrator


def test_demo_plan_is_traceable_and_non_executing() -> None:
    result = CommerceOrchestrator().plan(
        CommerceContext(customer_id="test", query="find a product", quantity=2)
    )
    assert result["decision"] == "READY_FOR_CHECKOUT"
    assert result["simulation_only"] is True
    assert result["external_action"] is None
    assert result["trace"][-1] == "decision.recorded"


def test_insufficient_inventory_holds() -> None:
    # The current demo inventory is intentionally bounded. A future inventory
    # adapter will replace this deterministic fixture.
    result = CommerceOrchestrator().plan(
        CommerceContext(customer_id="test", query="bulk order", quantity=100)
    )
    assert result["decision"] == "HOLD"
