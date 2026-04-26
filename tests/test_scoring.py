from app.intelligence.scoring import dedup_items, score_items
from app.models import IntelItem


def test_dedup_items():
    items = [IntelItem(source="x", title="a", url="u"), IntelItem(source="x", title="a2", url="u")]
    assert len(dedup_items(items)) == 1


def test_score_items_keyword():
    items = [IntelItem(source="x.com", title="AI CPU GPU data center")]
    cfg = {"source_weights": {"x.com": 8}, "keyword_weights": {"cpu": 10, "gpu": 8}}
    scored = score_items(items, cfg)
    assert scored[0].score >= 26
    assert "cpu" in [x.lower() for x in scored[0].matched_keywords]
