from app.robustness import StressScenario, monte_carlo_outcomes, robustness_score, stress_matrix


def test_stress_matrix_contains_default_scenarios():
    results = [
        {"return_pct": 4, "max_drawdown_pct": 5, "win_rate": .60},
        {"return_pct": -1, "max_drawdown_pct": 7, "win_rate": .45},
    ]
    report = stress_matrix(results)
    assert report["scenario_count"] == 5
    assert report["simulation_only"] is True
    assert report["external_execution"] is False


def test_custom_stress_is_deterministic():
    results = [{"return_pct": 10, "max_drawdown_pct": 4, "win_rate": .7}]
    scenario = StressScenario("shock", return_multiplier=.5, drawdown_multiplier=2, win_rate_shift=-.1)
    report = stress_matrix(results, [scenario])
    assert report["reports"][0]["mean_return_pct"] == 5
    assert report["reports"][0]["worst_drawdown_pct"] == 8
    assert report["reports"][0]["results"][0]["win_rate"] == .6


def test_monte_carlo_is_reproducible():
    results = [{"return_pct": 2}, {"return_pct": -1}, {"return_pct": 3}]
    first = monte_carlo_outcomes(results, iterations=100, seed=7)
    second = monte_carlo_outcomes(results, iterations=100, seed=7)
    assert first == second
    assert first["iterations"] == 100
    assert 0 <= first["probability_negative_total"] <= 1


def test_robustness_score_is_bounded():
    stress = stress_matrix([{"return_pct": 3, "max_drawdown_pct": 4, "win_rate": .6}])
    monte = monte_carlo_outcomes([{"return_pct": 3}], iterations=50)
    score = robustness_score(stress, monte)
    assert 0 <= score["score"] <= 1
    assert score["simulation_only"] is True
