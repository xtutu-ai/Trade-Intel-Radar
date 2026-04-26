from app.intelligence.theme_shift import build_theme_snapshot, compare_theme_shift
from app.models import IntelItem


def test_theme_snapshot_and_shift():
    watchlist = {"themes": {"ai": {"keywords": ["CPU", "GPU"], "cn_stocks": ["澜起科技"], "us_stocks": ["AMD"]}}}
    current = build_theme_snapshot([IntelItem(source="x", title="CPU CPU GPU AMD")], watchlist)
    assert current["themes"]["ai"]["CPU"] == 2
    shift = compare_theme_shift(current, [{"theme": {"themes": {"ai": {"CPU": 0}}}}])
    assert shift["alerts"]
