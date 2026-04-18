"""Minimal Seabhac API client."""

from __future__ import annotations
import requests
from datetime import datetime, timezone
from typing import Any


class SeabhacClient:
    def __init__(self, api_key: str, base_url: str = "https://api.seabhac.io"):
        self._key = api_key
        self._base = base_url.rstrip("/")
        self._s = requests.Session()
        self._s.headers["X-Api-Key"] = api_key

    def _get(self, path: str, params: dict | None = None) -> Any:
        r = self._s.get(self._base + path, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    # --- schedules ---

    def list_schedules(self) -> list[dict]:
        return self._get("/v1/schedules")["data"]

    def get_schedule(self, schedule_id: str) -> dict:
        return self._get(f"/v1/schedules/{schedule_id}")["data"]

    # --- jobs ---

    def list_jobs(self, schedule_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        return self._get(f"/v1/schedules/{schedule_id}/jobs", {"limit": limit, "offset": offset})["data"]

    def get_job(self, schedule_id: str, job_id: str) -> dict:
        return self._get(f"/v1/schedules/{schedule_id}/jobs/{job_id}")["data"]

    # --- alerts ---

    def list_alerts(self, schedule_id: str) -> list[dict]:
        return self._get(f"/v1/schedules/{schedule_id}/alerts")["data"]

    # --- metrics ---

    def _metrics(self, schedule_id: str, kind: str, from_: datetime | None, to: datetime | None) -> list[dict]:
        p: dict = {}
        if from_:
            p["from"] = from_.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if to:
            p["to"] = to.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self._get(f"/v1/schedules/{schedule_id}/metrics/{kind}", p or None)["data"]

    def metrics_http(self, sid: str, from_: datetime | None = None, to: datetime | None = None) -> list[dict]:
        return self._metrics(sid, "http", from_, to)

    def metrics_dns(self, sid: str, from_: datetime | None = None, to: datetime | None = None) -> list[dict]:
        return self._metrics(sid, "dns", from_, to)

    def metrics_ssl(self, sid: str, from_: datetime | None = None, to: datetime | None = None) -> list[dict]:
        return self._metrics(sid, "ssl", from_, to)

    def metrics_email_auth(self, sid: str, from_: datetime | None = None, to: datetime | None = None) -> list[dict]:
        return self._metrics(sid, "email_auth", from_, to)

    def metrics_pageload(self, sid: str, from_: datetime | None = None, to: datetime | None = None) -> list[dict]:
        return self._metrics(sid, "pageload", from_, to)

    def metrics_ssh(self, sid: str, from_: datetime | None = None, to: datetime | None = None) -> list[dict]:
        return self._metrics(sid, "ssh", from_, to)

    # --- dmarc ---

    def dmarc_list_reports(self, limit: int = 50, offset: int = 0) -> dict:
        return self._get("/v1/dmarc/reports", {"limit": limit, "offset": offset})

    def dmarc_get_report(self, report_id: str) -> dict:
        return self._get(f"/v1/dmarc/reports/{report_id}")

    def _dmarc(self, endpoint: str, domain: str | None) -> list[dict]:
        p = {"domain": domain} if domain else None
        return self._get(f"/v1/dmarc/{endpoint}", p)["data"]

    def dmarc_metrics(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("metrics", domain)

    def dmarc_geo(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("geo", domain)

    def dmarc_top_ips(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("top-ips", domain)

    def dmarc_top_failing_ips(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("top-failing-ips", domain)

    def dmarc_top_senders(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("top-senders", domain)

    def dmarc_fail_reasons(self, domain: str | None = None) -> dict:
        p = {"domain": domain} if domain else None
        return self._get("/v1/dmarc/fail-reasons", p)["data"]

    def dmarc_reporters(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("reporters", domain)

    def dmarc_top_asns(self, domain: str | None = None) -> list[dict]:
        return self._dmarc("top-asns", domain)
