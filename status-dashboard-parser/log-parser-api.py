#!/usr/bin/env python3
"""
Log-parser API for Homepage dashboard.

Endpoints:
  GET /latest           → most recent speedtest result as JSON
  GET /history?n=20     → last n speedtest results as JSON array
  GET /chart            → self-contained Chart.js page (for Homepage iframe)
  GET /dyndns           → latest DynDNS run status as JSON

Run:  python3 log-parser-api.py
Port: 5001
"""

import re
import os
from datetime import datetime
from flask import Flask, jsonify, request, make_response

SPEEDTEST_LOG_FILE = '/stacks/logs/speedtest/speedtest.log'
DYNDNS_LOG_FILE    = '/stacks/logs/dynDNS/dynDNS.log'

# ── Speedtest log parser ──────────────────────────────────────────────────────
# Log line format written by speedtest.py:
# 2025-01-01 12:34:56 INFO     download: 123456789, upload: 87654321, ping: 12.34 on Berlin, DE
_SPEEDTEST_LINE_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\w+\s+'
    r'download: (\d+), upload: (\d+), ping: ([\d.]+) on (.*)'
)

app = Flask(__name__)


def parse_speedtest_log(n: int = 20) -> list:
    results = []
    if not os.path.exists(SPEEDTEST_LOG_FILE):
        return results
    with open(SPEEDTEST_LOG_FILE) as f:
        for line in f:
            m = _SPEEDTEST_LINE_RE.search(line)
            if m:
                ts, dl, ul, ping, loc = m.groups()
                results.append({
                    'timestamp':     ts,
                    'download_mbps': round(int(dl) / 1_000_000, 2),
                    'upload_mbps':   round(int(ul) / 1_000_000, 2),
                    'ping_ms':       float(ping),
                    'server':        loc.strip(),
                })
    return results[-n:]


@app.route('/latest')
def latest():
    results = parse_speedtest_log(1)
    if not results:
        return jsonify({'error': 'no data'}), 404
    return jsonify(results[-1])


@app.route('/history')
def history():
    n = min(int(request.args.get('n', 20)), 100)
    return jsonify(parse_speedtest_log(n))


# ── DynDNS log parser ─────────────────────────────────────────────────────────
# Relevant line patterns:
#   INFO     dynDNS: currentIP: 1.2.3.4
#   INFO     dynDNS: run successful Today!
#   CRITICAL dynDNS failed: ...
#   CRITICAL dynDNS: failed Today

_DYNDNS_IP_RE   = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+INFO\s+dynDNS: currentIP: ([\d.]+)')
_DYNDNS_OK_RE   = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+INFO\s+dynDNS: run successful')
_DYNDNS_FAIL_RE = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+CRITICAL\s+dynDNS')
_DYNDNS_IPv6_RE = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+INFO\s+dynDNS: currentIPv6: ([\da-fA-F:]+)')
_DYNDNS_START_RE = re.compile(r'dynDNS: started')

def parse_dyndns_log() -> dict:
    if not os.path.exists(DYNDNS_LOG_FILE):
        return {'status': 'unknown', 'status_label': '? no log file', 'timestamp': None, 'ip': None, 'ipv6': None}

    last_ip       = None
    last_ipv6     = None
    last_ok_ts    = None
    last_fail_ts  = None
    last_fail_msg = None

        with open(DYNDNS_LOG_FILE) as f:
        all_lines = f.readlines()

    # Only consider lines from the last run
    last_start = 0
    for i, line in enumerate(all_lines):
        if _DYNDNS_START_RE.search(line):
            last_start = i
    lines_to_parse = all_lines[last_start:]

    for line in lines_to_parse:
        for line in f:
            m = _DYNDNS_IP_RE.search(line)
            if m:
                last_ip = m.group(2)
                continue
            m = _DYNDNS_IPv6_RE.search(line)
            if m:
                last_ipv6 = m.group(2)
                continue
            m = _DYNDNS_OK_RE.search(line)
            if m:
                last_ok_ts = m.group(1)
                continue
            m = _DYNDNS_FAIL_RE.search(line)
            if m:
                last_fail_ts  = m.group(1)
                last_fail_msg = line.strip()

    def to_dt(s):
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S') if s else datetime.min

    if to_dt(last_ok_ts) >= to_dt(last_fail_ts):
        return {
            'status':       'ok',
            'status_label': '\u2713 OK',
            'timestamp':    last_ok_ts,
            'ip':           last_ip,
	    'ipv6':         last_ipv6,
        }
    else:
        return {
            'status':       'error',
            'status_label': '\u2717 FAILED',
            'timestamp':    last_fail_ts,
            'ip':           last_ip,
            'ipv6':         last_ipv6,
	    'error':        last_fail_msg,
        }


@app.route('/dyndns')
def dyndns():
    return jsonify(parse_dyndns_log())


# ── Speedtest chart (self-contained HTML) ─────────────────────────────────────

CHART_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Speedtest History</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: transparent;
      color: #e2e8f0;
      font-family: ui-sans-serif, system-ui, sans-serif;
      padding: 8px 4px;
    }
    #nodata {
      display: none;
      color: #64748b;
      text-align: center;
      padding-top: 24px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <canvas id="chart"></canvas>
  <div id="nodata">No speedtest data found.</div>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <script>
    // Fetches via nginx /log-api/ proxy – must be reachable from the browser
    fetch('/log-api/history?n=20')
      .then(r => r.json())
      .then(data => {
        if (!data || data.length === 0) {
          document.getElementById('nodata').style.display = 'block';
          return;
        }

        const labels = data.map(d => d.timestamp.substring(5, 16).replace('T', ' '));
        const dl     = data.map(d => d.download_mbps);
        const ul     = data.map(d => d.upload_mbps);
        const ping   = data.map(d => d.ping_ms);

        new Chart(document.getElementById('chart'), {
          data: {
            labels,
            datasets: [
              {
                type: 'line', label: 'Download (Mbit/s)',
                data: dl, borderColor: '#22d3ee', backgroundColor: '#22d3ee18',
                yAxisID: 'speed', tension: 0.3, pointRadius: 3, fill: true,
              },
              {
                type: 'line', label: 'Upload (Mbit/s)',
                data: ul, borderColor: '#a78bfa', backgroundColor: '#a78bfa18',
                yAxisID: 'speed', tension: 0.3, pointRadius: 3, fill: true,
              },
              {
                type: 'line', label: 'Ping (ms)',
                data: ping, borderColor: '#fb923c', backgroundColor: 'transparent',
                yAxisID: 'ping', tension: 0.3, pointRadius: 3, borderDash: [4, 3],
              },
            ],
          },
          options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
              legend: {
                labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 12 },
              },
              tooltip: { backgroundColor: '#1e293b', titleColor: '#e2e8f0', bodyColor: '#cbd5e1' },
            },
            scales: {
              x: {
                ticks: { color: '#64748b', font: { size: 10 }, maxRotation: 30, maxTicksLimit: 10 },
                grid:  { color: '#1e293b' },
              },
              speed: {
                position: 'left',
                title: { display: true, text: 'Mbit/s', color: '#64748b', font: { size: 10 } },
                ticks: { color: '#64748b', font: { size: 10 } },
                grid:  { color: '#1e293b' },
              },
              ping: {
                position: 'right',
                title: { display: true, text: 'Ping ms', color: '#64748b', font: { size: 10 } },
                ticks: { color: '#64748b', font: { size: 10 } },
                grid:  { drawOnChartArea: false },
              },
            },
          },
        });
      })
      .catch(() => {
        document.getElementById('nodata').style.display = 'block';
      });
  </script>
</body>
</html>
"""


@app.route('/chart')
def chart():
    resp = make_response(CHART_HTML)
    resp.content_type = 'text/html'
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
