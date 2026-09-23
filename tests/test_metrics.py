"""Tests del endpoint /metrics."""


def test_metrics_endpoint_returns_prometheus_format(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    body = r.text
    assert "http_requests_total" in body or "http_request_duration_seconds" in body


def test_metrics_records_requests(client):
    client.get("/health")
    client.get("/health")

    r = client.get("/metrics")
    body = r.text

    assert 'http_requests_total{method="GET",path="/health",status_code="200"}' in body


def test_metrics_excludes_itself(client):
    client.get("/metrics")
    client.get("/metrics")
    client.get("/metrics")

    r = client.get("/metrics")
    body = r.text

    assert 'path="/metrics"' not in body
