"""Smoke tests for HTTP API (same paths and JSON shapes as production)."""


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("message") == "Connections Game API is running"
    assert data.get("docs") == "/docs"


def test_get_game_shape(client):
    r = client.get("/api/game")
    assert r.status_code == 200
    data = r.json()
    assert "words" in data
    assert "categories" in data
    assert "game_date" in data
    assert "found_categories" in data
    assert "mistakes" in data
    assert "remaining" in data
    assert "word_colors" in data
    assert len(data["words"]) == 16
    assert len(data["categories"]) == 4
    for cat in data["categories"]:
        assert "name" in cat and "words" in cat and "color" in cat
        assert len(cat["words"]) == 4


def test_check_selection_invalid(client):
    r = client.post("/api/check_selection", json=["___", "___", "___", "___"])
    assert r.status_code == 200
    body = r.json()
    assert body.get("valid") is False
    assert "mistakes" in body
    assert body["mistakes"] >= 1


def test_check_selection_valid_category(client):
    g = client.get("/api/game")
    assert g.status_code == 200
    first_words = g.json()["categories"][0]["words"]
    r = client.post("/api/check_selection", json=first_words)
    assert r.status_code == 200
    body = r.json()
    assert body.get("valid") is True
    assert body.get("category_name")
    assert "remaining" in body
    assert "game_complete" in body


def test_game_status(client):
    r = client.get("/api/game_status")
    assert r.status_code == 200
    data = r.json()
    assert "found_categories" in data
    assert "total_categories" in data
    assert "remaining" in data
    assert "game_date" in data
    assert "mistakes" in data
    assert "game_complete" in data


def test_daily_info(client):
    r = client.get("/api/daily_info")
    assert r.status_code == 200
    data = r.json()
    assert "today" in data
    assert "current_game_date" in data
    assert "game_complete" in data
    assert "found_count" in data
    assert "total_categories" in data
    assert "mistakes" in data


def test_reset_progress(client):
    r = client.post("/api/reset_progress")
    assert r.status_code == 200
    assert r.json().get("message")


def test_leaderboard_today(client):
    r = client.get("/api/leaderboard/today")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert "user_entry" in data


def test_leaderboard_submit_without_progress_is_400(client):
    r = client.post("/api/leaderboard/submit", params={"nickname": "testuser"})
    assert r.status_code == 400
    assert "error" in r.json()
