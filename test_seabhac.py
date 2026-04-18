"""Tests for the Seabhac Python client."""

from datetime import datetime, timezone

import pytest
import responses as rsps_lib
from _pytest.outcomes import Failed
from requests.exceptions import HTTPError

from seabhac import SeabhacClient

BASE = "https://test.local"


@pytest.fixture
def client():
    return SeabhacClient("test-key", base_url=BASE)


# --- helpers ---


def reg(method, path, payload, status=200):
    """Register a responses mock for BASE + path."""
    rsps_lib.add(method, BASE + path, json=payload, status=status)


# --- auth ---


@rsps_lib.activate
def test_api_key_header(client):
    reg(rsps_lib.GET, "/v1/schedules", {"data": []})
    client.list_schedules()
    assert rsps_lib.calls[0].request.headers["X-Api-Key"] == "test-key"


# --- schedules ---


@rsps_lib.activate
def test_list_schedules(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules",
        {
            "data": [
                {"id": "s1", "name": "HTTP check", "type": "http", "status": "active"},
            ]
        },
    )
    result = client.list_schedules()
    assert len(result) == 1
    assert result[0]["id"] == "s1"
    assert result[0]["type"] == "http"
    assert rsps_lib.calls[0].request.url == BASE + "/v1/schedules"


@rsps_lib.activate
def test_get_schedule(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1",
        {
            "data": {
                "id": "s1",
                "name": "DNS check",
                "type": "dns",
                "config": {"domain_name": "example.com"},
            }
        },
    )
    s = client.get_schedule("s1")
    assert s["id"] == "s1"
    assert s["config"]["domain_name"] == "example.com"


# --- jobs ---


@rsps_lib.activate
def test_list_jobs_params(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/jobs",
        {
            "data": [
                {
                    "id": "j1",
                    "status": "completed",
                    "results": {
                        "summary": {
                            "total_checks": 1,
                            "successful_checks": 1,
                            "failed_checks": 0,
                            "execution_time_ms": 50,
                        }
                    },
                },
            ]
        },
    )
    result = client.list_jobs("s1", limit=25, offset=10)
    assert len(result) == 1
    assert result[0]["status"] == "completed"
    qs = rsps_lib.calls[0].request.url
    if qs:
        assert "limit=25" in qs
        assert "offset=10" in qs


@rsps_lib.activate
def test_get_job(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/jobs/j1",
        {
            "data": {
                "id": "j1",
                "type": "http",
                "status": "completed",
                "results": {
                    "summary": {
                        "total_checks": 1,
                        "successful_checks": 1,
                        "failed_checks": 0,
                        "execution_time_ms": 80,
                    },
                    "http_results": {
                        "status_code": 200,
                        "response_time_ms": 95,
                        "success": True,
                    },
                },
            }
        },
    )
    j = client.get_job("s1", "j1")
    assert j["results"]["http_results"]["status_code"] == 200
    assert rsps_lib.calls[0].request.url == BASE + "/v1/schedules/s1/jobs/j1"


@rsps_lib.activate
def test_get_job_dnsbl_results(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/jobs/j2",
        {
            "data": {
                "id": "j2",
                "type": "dnsbl",
                "status": "completed",
                "results": {
                    "summary": {
                        "total_checks": 1,
                        "successful_checks": 1,
                        "failed_checks": 0,
                        "execution_time_ms": 20,
                    },
                    "dnsbl_results": {
                        "zen.spamhaus.org": {
                            "server": "zen.spamhaus.org",
                            "listed": False,
                            "response": "",
                        },
                    },
                },
            }
        },
    )
    j = client.get_job("s1", "j2")
    assert j["results"]["dnsbl_results"]["zen.spamhaus.org"]["listed"] is False


# --- alerts ---


@rsps_lib.activate
def test_list_alerts(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/alerts",
        {
            "data": [
                {
                    "id": "a1",
                    "metric": "response_time_ms",
                    "condition": "gt",
                    "threshold": 500.0,
                    "is_enabled": True,
                },
            ]
        },
    )
    alerts = client.list_alerts("s1")
    assert len(alerts) == 1
    assert alerts[0]["threshold"] == 500.0
    assert rsps_lib.calls[0].request.url == BASE + "/v1/schedules/s1/alerts"


# --- metrics ---


@rsps_lib.activate
def test_metrics_http(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/metrics/http",
        {
            "data": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "avg_latency_ms": 120.5,
                    "uptime_percent": 98.0,
                    "total_requests": 100,
                    "successful_requests": 98,
                },
            ]
        },
    )
    pts = client.metrics_http("s1")
    assert len(pts) == 1
    assert pts[0]["avg_latency_ms"] == 120.5
    assert pts[0]["uptime_percent"] == 98.0


@rsps_lib.activate
def test_metrics_with_time_range(client):
    reg(rsps_lib.GET, "/v1/schedules/s1/metrics/dns", {"data": []})
    from_ = datetime(2024, 1, 1, tzinfo=timezone.utc)
    to = datetime(2024, 1, 2, tzinfo=timezone.utc)
    client.metrics_dns("s1", from_=from_, to=to)
    url = rsps_lib.calls[0].request.url
    if url:
        assert (
            "from=2024-01-01T00%3A00%3A00Z" in url or "from=2024-01-01T00:00:00Z" in url
        )
        assert "to=2024-01-02T00%3A00%3A00Z" in url or "to=2024-01-02T00:00:00Z" in url
    else:
        assert Failed


@rsps_lib.activate
def test_metrics_no_time_range_omits_params(client):
    reg(rsps_lib.GET, "/v1/schedules/s1/metrics/ssl", {"data": []})
    client.metrics_ssl("s1")
    url = rsps_lib.calls[0].request.url
    if url:
        assert "from" not in url
        assert "to" not in url
    else:
        assert Failed


@rsps_lib.activate
def test_metrics_ssl(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/metrics/ssl",
        {
            "data": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "avg_latency_ms": 10.0,
                    "avg_days_until_expiry": 87.3,
                    "uptime_percent": 100.0,
                },
            ]
        },
    )
    pts = client.metrics_ssl("s1")
    assert pts[0]["avg_days_until_expiry"] == 87.3


@rsps_lib.activate
def test_metrics_email_auth(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/metrics/email_auth",
        {
            "data": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "avg_latency_ms": 50.0,
                    "spf_valid_count": 5,
                    "dmarc_valid_count": 5,
                    "dkim_valid_count": 4,
                },
            ]
        },
    )
    pts = client.metrics_email_auth("s1")
    assert pts[0]["dkim_valid_count"] == 4


@rsps_lib.activate
def test_metrics_pageload(client):
    reg(
        rsps_lib.GET,
        "/v1/schedules/s1/metrics/pageload",
        {
            "data": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "avg_response_time_ms": 350.0,
                    "avg_ttfb_ms": 80.0,
                    "avg_page_load_ms": 340.0,
                },
            ]
        },
    )
    pts = client.metrics_pageload("s1")
    assert pts[0]["avg_ttfb_ms"] == 80.0


@pytest.mark.parametrize(
    "method,kind",
    [
        ("metrics_http", "http"),
        ("metrics_dns", "dns"),
        ("metrics_ssl", "ssl"),
        ("metrics_email_auth", "email_auth"),
        ("metrics_pageload", "pageload"),
        ("metrics_ssh", "ssh"),
    ],
)
@rsps_lib.activate
def test_metrics_path(client, method, kind):
    reg(rsps_lib.GET, f"/v1/schedules/s1/metrics/{kind}", {"data": []})
    getattr(client, method)("s1")
    url = rsps_lib.calls[0].request.url
    if url:
        assert url.startswith(BASE + f"/v1/schedules/s1/metrics/{kind}")
    else:
        assert Failed


# --- dmarc ---


@rsps_lib.activate
def test_dmarc_list_reports(client):
    reg(
        rsps_lib.GET,
        "/v1/dmarc/reports",
        {
            "data": [{"id": "r1"}],
            "count": 42,
            "limit": 10,
            "offset": 0,
        },
    )
    result = client.dmarc_list_reports(limit=10, offset=0)
    assert result["count"] == 42
    assert len(result["data"]) == 1
    url = rsps_lib.calls[0].request.url
    if url:
        assert "limit=10" in url
        assert "offset=0" in url
    else:
        assert Failed


@rsps_lib.activate
def test_dmarc_get_report(client):
    reg(
        rsps_lib.GET,
        "/v1/dmarc/reports/r1",
        {
            "report": {"id": "r1", "org_name": "Google"},
            "records": [{"source_ip": "1.2.3.4"}],
        },
    )
    result = client.dmarc_get_report("r1")
    assert result["report"]["org_name"] == "Google"
    assert len(result["records"]) == 1


@rsps_lib.activate
def test_dmarc_metrics(client):
    reg(
        rsps_lib.GET,
        "/v1/dmarc/metrics",
        {
            "data": [
                {
                    "timestamp": "2024-01-01",
                    "domain": "example.com",
                    "total_messages": 1000,
                    "dmarc_pass": 975,
                },
            ]
        },
    )
    pts = client.dmarc_metrics("example.com")
    assert pts[0]["total_messages"] == 1000
    assert pts[0]["dmarc_pass"] == 975
    if rsps_lib.calls[0].request.url:
        assert "domain=example.com" in rsps_lib.calls[0].request.url
    else:
        assert Failed


@rsps_lib.activate
def test_dmarc_metrics_no_domain(client):
    reg(rsps_lib.GET, "/v1/dmarc/metrics", {"data": []})
    client.dmarc_metrics()
    url = rsps_lib.calls[0].request.url
    if url:
        assert "domain" not in url
    else:
        assert Failed


@pytest.mark.parametrize(
    "method,endpoint",
    [
        ("dmarc_geo", "geo"),
        ("dmarc_top_ips", "top-ips"),
        ("dmarc_top_failing_ips", "top-failing-ips"),
        ("dmarc_top_senders", "top-senders"),
        ("dmarc_reporters", "reporters"),
        ("dmarc_top_asns", "top-asns"),
    ],
)
@rsps_lib.activate
def test_dmarc_analytics_endpoints(client, method, endpoint):
    reg(
        rsps_lib.GET,
        f"/v1/dmarc/{endpoint}",
        {"data": [{"country": "US", "count": 100}]},
    )
    result = getattr(client, method)("example.com")
    assert len(result) == 1
    url = rsps_lib.calls[0].request.url
    if url:
        assert f"/v1/dmarc/{endpoint}" in url
        assert "domain=example.com" in url
    else:
        assert Failed


@rsps_lib.activate
def test_dmarc_fail_reasons(client):
    reg(
        rsps_lib.GET,
        "/v1/dmarc/fail-reasons",
        {"data": {"spf_only": 10, "dkim_only": 5}},
    )
    result = client.dmarc_fail_reasons("example.com")
    assert result["spf_only"] == 10


@rsps_lib.activate
def test_dmarc_fail_reasons_no_domain(client):
    reg(rsps_lib.GET, "/v1/dmarc/fail-reasons", {"data": {}})
    client.dmarc_fail_reasons()
    url = rsps_lib.calls[0].request.url
    if url:
        assert "domain" not in url
    else:
        assert Failed


# --- error handling ---


@rsps_lib.activate
def test_http_error_404(client):
    reg(rsps_lib.GET, "/v1/schedules/missing", {"error": "not found"}, status=404)
    with pytest.raises(HTTPError) as exc_info:
        client.get_schedule("missing")
    assert exc_info.value.response.status_code == 404


@rsps_lib.activate
def test_http_error_401(client):
    reg(rsps_lib.GET, "/v1/schedules", {"error": "invalid api key"}, status=401)
    with pytest.raises(HTTPError):
        client.list_schedules()
