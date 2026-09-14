"""HTTP client with disk cache, retries, per-host rate limits, circuit breaker."""

from __future__ import annotations

import hashlib
import json
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import requests

from . import config as cfg


class CircuitOpenError(RuntimeError):
    pass


@dataclass(slots=True)
class HttpResult:
    ok: bool
    status: int | None
    data: object = None
    from_cache: bool = False
    error: str | None = None
    url: str | None = None

    @property
    def not_found(self) -> bool:
        return self.status == 404


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _host_of(url: str) -> str:
    return urlsplit(url).netloc.lower()


def rate_for_host(host: str) -> float:
    if host in cfg.RATE_LIMITS:
        return cfg.RATE_LIMITS[host]
    for key, value in cfg.RATE_LIMITS.items():
        if key != "default" and host.endswith(key):
            return value
    return cfg.RATE_LIMITS["default"]


class CachedHttp:
    def __init__(self, paths=None, session=None, sleep=None, monotonic=None, rng=None):
        self.paths = (paths or cfg.DEFAULT_PATHS).ensure()
        self.session = session or requests.Session()
        self._sleep = sleep or time.sleep
        self._monotonic = monotonic or time.monotonic
        self._rng = rng or random.Random(0)
        self._lock = threading.Lock()
        self._last_request: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        self._open_until: dict[str, float] = {}

    def cache_path(self, source: str, url: str, params: dict | None = None) -> Path:
        key = url
        if params:
            filtered = sorted((k, v) for k, v in params.items() if v is not None)
            key = f"{url}?{urlencode(filtered)}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self.paths.raw_dir(source) / f"{digest}.json"

    def get_json(self, source: str, url: str, params: dict | None = None, refresh: bool = False, timeout=None) -> HttpResult:
        cache_file = self.cache_path(source, url, params)
        if cache_file.exists() and not refresh:
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                return HttpResult(ok=True, status=200, data=data, from_cache=True, url=url)
            except (OSError, json.JSONDecodeError):
                pass
        try:
            result = self._request(url, params, timeout)
        except CircuitOpenError as exc:
            return HttpResult(ok=False, status=None, error=str(exc), url=url)
        if result.ok and result.status == 200:
            self._write_cache(cache_file, result.data, url)
        return result

    def _request(self, url: str, params: dict | None, timeout) -> HttpResult:
        host = _host_of(url)
        self._check_circuit(host)
        last_error = "request_failed"
        for attempt in range(1, cfg.MAX_RETRIES + 1):
            self._wait_for_slot(host)
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers={"User-Agent": cfg.USER_AGENT, "Accept": "application/json"},
                    timeout=timeout or (cfg.CONNECT_TIMEOUT, cfg.READ_TIMEOUT),
                )
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}"
                self._note_failure(host)
                if attempt < cfg.MAX_RETRIES:
                    self._sleep(self._backoff(attempt))
                continue
            if response.status_code == 404:
                self._note_success(host)
                return HttpResult(ok=False, status=404, error="not_found", url=url)
            if response.status_code in cfg.RETRY_STATUSES:
                last_error = f"http_{response.status_code}"
                self._note_failure(host)
                if attempt < cfg.MAX_RETRIES:
                    self._sleep(self._retry_delay(response, attempt))
                continue
            if response.status_code >= 400:
                self._note_failure(host)
                return HttpResult(ok=False, status=response.status_code, error=f"http_{response.status_code}", url=url)
            self._note_success(host)
            try:
                return HttpResult(ok=True, status=response.status_code, data=response.json(), url=url)
            except ValueError as exc:
                return HttpResult(ok=False, status=response.status_code, error=f"bad_json: {exc}", url=url)
        return HttpResult(ok=False, status=None, error=last_error, url=url)

    def _retry_delay(self, response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), cfg.BACKOFF_MAX)
            except (TypeError, ValueError):
                pass
        return self._backoff(attempt)

    def _backoff(self, attempt: int) -> float:
        delay = min(cfg.BACKOFF_BASE * (2 ** (attempt - 1)), cfg.BACKOFF_MAX)
        return delay * (0.5 + self._rng.random() * 0.5)

    def _wait_for_slot(self, host: str) -> None:
        interval = 1.0 / max(rate_for_host(host), 0.01)
        with self._lock:
            now = self._monotonic()
            last = self._last_request.get(host)
            wait = max(0.0, interval - (now - last)) if last is not None else 0.0
            self._last_request[host] = now + wait
        if wait > 0:
            self._sleep(wait)

    def _check_circuit(self, host: str) -> None:
        until = self._open_until.get(host)
        if not until:
            return
        if self._monotonic() < until:
            raise CircuitOpenError(f"circuit_open:{host}")
        self._open_until.pop(host, None)
        self._failures[host] = 0

    def _note_failure(self, host: str) -> None:
        count = self._failures.get(host, 0) + 1
        self._failures[host] = count
        if count >= cfg.CIRCUIT_FAIL_THRESHOLD:
            self._open_until[host] = self._monotonic() + cfg.CIRCUIT_COOLDOWN_SECONDS

    def _note_success(self, host: str) -> None:
        self._failures[host] = 0

    def _write_cache(self, cache_file: Path, data, url: str) -> None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(cache_file)
        self._append_index({"kind": "json", "url": url, "path": str(cache_file)})

    def _append_index(self, entry: dict) -> None:
        entry["ts"] = _now_iso()
        with self._lock:
            self.paths.cache_index.parent.mkdir(parents=True, exist_ok=True)
            with open(self.paths.cache_index, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
