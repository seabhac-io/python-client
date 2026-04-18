# seabhac-python

Minimal Python client for the [Seabhac](https://seabhac.io) API.

## Installation

```
pip install requests
```

Copy `seabhac.py` into your project.

## Quick start

```python
from seabhac import SeabhacClient

client = SeabhacClient("your-api-key")

# List all monitoring schedules
schedules = client.list_schedules()
for s in schedules:
    print(s["name"], s["status"])

# Get a specific schedule
schedule = client.get_schedule("schedule-uuid")

# List recent jobs for a schedule
jobs = client.list_jobs("schedule-uuid", limit=10)
for job in jobs:
    print(job["status"], job["results"]["summary"])
```

## Schedules

```python
schedules = client.list_schedules()
schedule  = client.get_schedule(schedule_id)
```

## Jobs

```python
jobs = client.list_jobs(schedule_id, limit=50, offset=0)
job  = client.get_job(schedule_id, job_id)
```

`job["results"]` contains check-specific fields depending on the schedule type:
`http_results`, `dnsbl_results`, `dns_results`, `ssl_result`, `ssh_result`,
`tcp_result`, `udp_result`, `email_auth_results`, `page_load_result`,
`broken_links_result`, `domain_expiry_result`.

## Alerts

```python
alerts = client.list_alerts(schedule_id)
```

## Metrics

All metrics methods accept optional `from_` and `to` as `datetime` objects.

```python
from datetime import datetime, timezone

from_ = datetime(2024, 1, 1, tzinfo=timezone.utc)
to    = datetime(2024, 2, 1, tzinfo=timezone.utc)

client.metrics_http(schedule_id, from_=from_, to=to)
client.metrics_dns(schedule_id)
client.metrics_ssl(schedule_id)
client.metrics_email_auth(schedule_id)
client.metrics_pageload(schedule_id)
client.metrics_ssh(schedule_id)
```

## DMARC

```python
# Paginated report list — returns dict with data/count/limit/offset
reports = client.dmarc_list_reports(limit=20, offset=0)

# Full report with individual records
report = client.dmarc_get_report(report_id)
print(report["report"], report["records"])

# Analytics (all accept an optional domain filter)
client.dmarc_metrics("example.com")
client.dmarc_geo("example.com")
client.dmarc_top_ips("example.com")
client.dmarc_top_failing_ips("example.com")
client.dmarc_top_senders("example.com")
client.dmarc_fail_reasons("example.com")
client.dmarc_reporters("example.com")
client.dmarc_top_asns("example.com")
```

## Error handling

HTTP errors (4xx/5xx) raise `requests.exceptions.HTTPError`.

```python
from requests.exceptions import HTTPError

try:
    schedule = client.get_schedule("bad-id")
except HTTPError as e:
    print(e.response.status_code)
```

## Running tests

```
uv run pytest
```
