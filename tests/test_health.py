def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
