import datetime
import json
import sqlite3
import time
import logging

import requests


logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when the API rate limit is exceeded."""
    pass


class APICache:
    """SQLite database for caching API requests to avoid rate limits and speed up development."""
    unspecified = object()

    def __init__(self, path, cache_failed_requests=True):
        self.conn = sqlite3.connect(path)
        self.cache_failed_requests = cache_failed_requests
        self.create()

    def create(self):
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            called_at INTEGER,
            called_at_str TEXT,
            url TEXT,
            headers JSON,
            params JSON,
            method TEXT,
            response_code INTEGER,
            response_json JSON,
            response_headers JSON
        )""")

    def retrieve_cached_get(self, url, params=unspecified, headers=unspecified, max_age=None, limit=1, order_by="called_at DESC", **kwargs):
        return self.retrieve_cached_request("GET", url, params=params, headers=headers, max_age=max_age, limit=limit, order_by=order_by, **kwargs)

    def retrieve_cached_request(self, method, url, params=unspecified, headers=unspecified, max_age=None, limit=1, order_by="called_at DESC", **kwargs):
        condition = {
            "url": url,
            "method": method,
        }
        condition.update(kwargs)
        if params is not self.unspecified:
            condition["params"] = json.dumps({k: params[k] for k in sorted(params)}) if params else None
        if headers is not self.unspecified:
            condition["headers"] = json.dumps({k: headers[k] for k in sorted(headers)}) if headers else None
        result = self.select(columns="response_json", max_age=max_age, limit=limit, order_by=order_by, **condition)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass
        elif isinstance(result, list) and all(isinstance(x, str) for x in result):
            try:
                result = [json.loads(x) for x in result]
            except json.JSONDecodeError:
                pass
        if result is None:
            return None
        return result

    def cache_post(self, url, params, response_code, response_json, called_at=None):
        return self.cache_request("POST", url, params, response_code, response_json, called_at)

    def cache_get(self, url, params, response, called_at: float = None):
        return self.cache_request("GET", url=url, params=params, response=response, called_at=called_at)

    def cache_request(self, method, url, response, headers=None, params=None, called_at: float = None):
        if not ((response.status_code == 200) or self.cache_failed_requests):
            return
        p = json.dumps({k: params[k] for k in sorted(params)}) if params else None
        h = json.dumps({k: headers[k] for k in sorted(headers)}) if headers else None
        called_at = time.time() if called_at is None else called_at
        called_at_str = str(datetime.datetime.fromtimestamp(called_at))
        response_json = json.dumps(response.json())
        record = {
            "called_at": called_at,
            "called_at_str": called_at_str,
            "url": url,
            "method": method,
            "params": p,
            "headers": h,
            "response_code": response.status_code,
            "response_json": response_json,
            "response_headers": json.dumps(dict(response.headers))
        }
        self.insert(record)

    def trim_old(self, max_age):
        self.delete(max_age=max_age)

    def delete_failed(self):
        self.delete(response_code="!= 200")

    def delete(self, where=None, max_age=None, order_by=None, limit=None, offset=None, **conditions):
        cmd, condition_params = self._compose_query("DELETE", where=where, max_age=max_age, order_by=order_by,
                                                    limit=limit, offset=offset, **conditions)
        self.cursor.execute(cmd, condition_params)
        self.conn.commit()

    def count(self, where=None, max_age=None, order_by=None, limit=None, offset=None, **conditions):
        return self.select(columns="COUNT(*)", where=where, max_age=max_age, order_by=order_by, limit=limit, offset=offset, **conditions)[0]

    def select(self, columns="*", where=None, max_age=None, order_by=None, limit=None, offset=None, **conditions):
        cmd, condition_params = self._compose_query("SELECT", columns=columns, where=where, max_age=max_age,
                                                order_by=order_by, limit=limit, offset=offset, **conditions)
        try:
            self.cursor.execute(cmd, condition_params)
            r = self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in query: {cmd} with params {condition_params}: {e}")
            raise
        if isinstance(columns, str) and columns != "*" and "," not in columns:
            return r[0] if len(r) == 1 and not isinstance(r[0], tuple) else [x[0] for x in r] if len(r) > 0 and all(isinstance(x, tuple) for x in r) else r
        return r

    def insert(self, record):
        keys = ", ".join(record.keys())
        values = ", ".join(["?" for _ in record])
        self.cursor.execute(f"INSERT INTO requests ({keys}) VALUES ({values})", list(record.values()))
        self.conn.commit()

    def _compose_query(self, cmd, columns="*", where=None, max_age=None, order_by=None, limit=None, offset=None, **conditions):
        c = columns if isinstance(columns, str) else ", ".join(columns)
        if max_age is not None:
            called_at = (time.time() - max_age) if max_age else 0
            conditions["called_at"] = f"> {called_at}"

        cond = ""
        condition_params = []
        for k, v in conditions.items():
            if isinstance(v, str) and (
                    v.startswith(">") or v.startswith("<") or v.startswith("=") or v.startswith("!") or v.startswith(
                    "IN") or v.startswith("LIKE") or v.startswith("BETWEEN") or v.startswith("IS")):
                cond += f"{k} {v} AND "
            else:
                cond += f"{k} = ? AND "
                if isinstance(v, (list, dict)):
                    v = json.dumps(v)
                condition_params.append(v)
        cond = cond[:-5]

        if where is not None:
            where = "AND " + where.replace("WHERE", "").strip()
        w = f"WHERE {cond or ''}{where or ''}" if cond or where else ""
        cmd = f"""{cmd} {c} FROM requests {w}"""
        if order_by:
            cmd += f" ORDER BY {order_by}"
        if limit:
            cmd += f" LIMIT {limit}"
        if offset:
            cmd += f" OFFSET {offset}"
        return cmd, condition_params


class API:
    """API class for making GET requests with caching and rate limiting.

    * Uses APICache to store and retrieve API responses in a SQLite database.
    * If you re-call the exact same request you will get the cached response
    unless you specify a max_age (seconds) less than the time since your previous request.
    * If you get a 429 response (rate limit exceeded) the request will be retried after a delay
    based on the rate limits specified in the rate_limits dictionary.
    """
    rate_limits: dict[int, int] = {}  # {<number of requests>: <timeframe in seconds>}
    # e.g. {100: 15*60} means a rate limit of 100 requests every 15 minutes

    def __init__(self, base_url, cache_path,
                 rate_limits=None,
                 headers=None,
                 retry_on_rate_limit=True,
                 loglevel=logging.INFO
                 ):
        self.base_url = base_url
        self.cache = APICache(cache_path)
        self.headers = headers or {}
        if rate_limits is not None:
            self.rate_limits = rate_limits
        self.retry_on_rate_limit = retry_on_rate_limit
        if loglevel:
            logging.basicConfig(level=loglevel)

    def get(self, route, params=None, max_age=None, cache=True, retry_on_rate_limit=None, rate_limit_delay=None):
        if retry_on_rate_limit is None:
            retry_on_rate_limit = self.retry_on_rate_limit
        if params is not None:
            for key, value in params.copy().items():
                if f"{{{key}}}" in route:
                    route = route.replace(f"{{{key}}}", str(value))
                    del params[key]

        if '{' in route and '}' in route:
            raise ValueError(f"Route {route} has unresolved parameters: {params}")

        url = f"{self.base_url}{route}"
        if max_age != 0:
            cached_json = self.cache.retrieve_cached_get(url, params=params, max_age=max_age)
            if cached_json:
                logger.info(f"Retrieved cached response for {url}")
                return cached_json[0] if isinstance(cached_json, list) and len(cached_json) == 1 else cached_json
        called_at = time.time()
        logger.info(f"GET {url}")
        result = requests.get(url, headers=self.headers, params=params)

        if cache:
            logger.info(f"Caching response for {url}")
            self.cache.cache_get(url, params, result, called_at=called_at)
        if result.status_code == 200:
            return result.json()
        elif result.status_code == 429:
            if retry_on_rate_limit:
                logger.info("Rate limit exceeded. Waiting before retrying")
                if rate_limit_delay is not None:
                    time.sleep(rate_limit_delay)
                else:
                    time.sleep(self.get_rate_limit_delay())
                return self.get(route, params=params, max_age=max_age, cache=cache, retry_on_rate_limit=retry_on_rate_limit)
            raise RateLimitError("Rate limit exceeded")
        raise ValueError(f"Error {result.status_code}: {result.text}")

    def get_rate_limit_delay(self):
        safe = None
        for limit, delay in self.rate_limits.items():
            t = self.cache.select(columns="called_at", limit=1, offset=limit-2)
            if t:
                next_safe = t + delay
                if safe is None or next_safe < safe:
                    safe = next_safe
        if safe is None:
            # just guess and use the lowest rate limit
            safe = time.time() + min(self.rate_limits.values())
        logger.info(f"Rate limit delay: {safe - time.time()}")
        return safe - time.time()
