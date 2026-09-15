from decimal import Decimal
from app.models import Candle
from app.validation import leakage_report, summarize_oos, temporal_split, validate_candles, walk_forward_windows

def candle(i: int) -> Candle:
    return Candle(timestamp=i, symbol="TEST", timeframe="1h", open=Decimal("100"), high=Decimal("102"), low=Decimal("99"), close=Decimal(str(100 + i)), volume=Decimal("10"), source="test")

def test_validation_accepts_ordered_ohlcv():
    report = validate_candles([candle(i) for i in range(35)])
    assert report.passed
    assert report.sample_count == 35

def test_validation_rejects_duplicate_timestamps():
    candles = [candle(i) for i in range(30)]
    candles[10] = candle(9)
    report = validate_candles(candles)
    assert not report.passed
    assert any(f.code == "DUPLICATE_TIMESTAMPS" for f in report.findings)

def test_temporal_split_has_no_leakage():
    train, test = temporal_split([candle(i) for i in range(40)], .75)
    assert len(train) == 30
    assert leakage_report(train, test)["passed"]

def test_walk_forward_windows_are_non_overlapping():
    candles = [candle(i) for i in range(100)]
    windows = walk_forward_windows(candles, 40, 20, 20)
    assert len(windows) == 3
    assert windows[0]["test_end"] < windows[1]["test_start"]

def test_oos_summary_reports_worst_case():
    result = summarize_oos([{"return_pct": 2, "max_drawdown_pct": 3, "win_rate": .6}, {"return_pct": -4, "max_drawdown_pct": 8, "win_rate": .4}])
    assert result["worst_return_pct"] == -4
    assert result["worst_drawdown_pct"] == 8
    assert result["windows"] == 2
