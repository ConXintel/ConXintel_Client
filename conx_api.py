"""HTTP client for the main ConX server's API v1."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import requests


class ConXApiError(Exception):
    def __init__(self, message: str, *, code: str = "", status_code: int = 0, payload: Any = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.payload = payload

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.code:
            parts.append(f"(code: {self.code})")
        if self.status_code:
            parts.append(f"[HTTP {self.status_code}]")
        return " ".join(parts)


def _headers(api_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {(api_token or '').strip()}",
        "X-API-Token": (api_token or "").strip(),
        "Accept": "application/json",
    }


def _request_json(
    method: str,
    url: str,
    *,
    api_token: str,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Tuple[requests.Response, Any]:
    try:
        resp = requests.request(
            method,
            url,
            headers=_headers(api_token),
            json=json_body,
            timeout=timeout,
        )
    except requests.ConnectionError:
        raise ConXApiError(
            "Cannot reach the ConX server. Check the URL and that ConX is running "
            "(e.g. python app.py on port 8989)."
        ) from None
    except requests.Timeout:
        raise ConXApiError("ConX server timed out. Try again or check the server URL.") from None
    except requests.RequestException as exc:
        raise ConXApiError(f"Network error talking to ConX: {exc}") from exc

    try:
        data = resp.json()
    except ValueError:
        snippet = (resp.text or "")[:200].strip()
        if resp.status_code == 404:
            raise ConXApiError(
                "ConX API route not found (HTTP 404). Restart the main ConX app so "
                "/api/v1/account is available, or update ConX to the latest version.",
                status_code=404,
                payload=snippet,
            )
        raise ConXApiError(
            f"ConX returned a non-JSON response (HTTP {resp.status_code}). "
            f"Is the server URL correct?{(' Preview: ' + snippet) if snippet else ''}",
            status_code=resp.status_code,
            payload=snippet,
        )
    return resp, data


def _parse_error(resp: requests.Response, data: Any) -> ConXApiError:
    message = "ConX API request failed"
    code = ""
    if isinstance(data, dict):
        message = (data.get("error") or message).strip()
        code = (data.get("code") or "").strip()
    if resp.status_code == 404:
        message = (
            "ConX API route not found. Restart the main ConX server (python app.py) "
            "after updating, then try setup again."
        )
    elif resp.status_code == 401 and code == "invalid_token":
        message = (
            "Invalid API token. In ConX Client, sign in as owner → Settings and paste "
            "a fresh token from ConX → API Access."
        )
    elif resp.status_code == 403 and code == "api_access_disabled":
        message = (
            "API access is not enabled on this ConX account. Use an Agency plan or "
            "enable standalone API access in ConX admin."
        )
    return ConXApiError(message, code=code, status_code=resp.status_code, payload=data)


def _verify_via_search_probe(base_url: str, api_token: str) -> Dict[str, Any]:
    """Fallback when /api/v1/account is missing on older ConX builds."""
    url = f"{base_url.rstrip('/')}/api/v1/search"
    resp, data = _request_json(
        "POST",
        url,
        api_token=api_token,
        json_body={"search_type": "username"},
        timeout=30,
    )
    if resp.status_code == 401:
        raise _parse_error(resp, data)
    if resp.status_code == 403:
        raise _parse_error(resp, data)
    if resp.status_code == 400 and isinstance(data, dict) and data.get("code") == "invalid_request":
        return {
            "email": "",
            "package": "",
            "active": True,
            "expired": False,
            "credits": 0,
            "monthly_search_limit": 0,
            "monthly_search_used": 0,
            "api_access_enabled": True,
            "account_endpoint_missing": True,
        }
    if resp.status_code >= 400:
        raise _parse_error(resp, data)
    raise ConXApiError("Unexpected response while verifying API token.", payload=data)


def verify_api_access(base_url: str, api_token: str) -> Dict[str, Any]:
    """Validate token during client setup. Uses /account or search probe fallback."""
    try:
        return get_account(base_url, api_token)
    except ConXApiError as exc:
        if exc.status_code == 404:
            return _verify_via_search_probe(base_url, api_token)
        raise


def get_account(base_url: str, api_token: str, *, timeout: int = 30) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/account"
    resp, data = _request_json("GET", url, api_token=api_token, timeout=timeout)
    if resp.status_code >= 400:
        raise _parse_error(resp, data)
    if not isinstance(data, dict) or not data.get("ok"):
        raise ConXApiError("Unexpected account response", payload=data)
    account = data.get("account")
    if not isinstance(account, dict):
        raise ConXApiError("Account payload missing", payload=data)
    return account


def get_account_or_probe(base_url: str, api_token: str) -> Optional[Dict[str, Any]]:
    try:
        return get_account(base_url, api_token)
    except ConXApiError as exc:
        if exc.status_code != 404:
            return None
        try:
            return _verify_via_search_probe(base_url, api_token)
        except ConXApiError:
            return None


def search(
    base_url: str,
    api_token: str,
    *,
    search_type: str,
    fields: Dict[str, str],
    timeout: int = 120,
) -> Tuple[Dict[str, Any], int]:
    url = f"{base_url.rstrip('/')}/api/v1/search"
    body = {"search_type": search_type, **fields}
    resp, data = _request_json("POST", url, api_token=api_token, json_body=body, timeout=timeout)
    if resp.status_code >= 400:
        raise _parse_error(resp, data)
    if not isinstance(data, dict) or not data.get("ok"):
        raise ConXApiError("Unexpected search response", payload=data)
    credits = int(data.get("credits_remaining") or 0)
    return data, credits


def fetch_search_health(base_url: str, *, timeout: int = 8) -> Dict[str, Any]:
    """Proxy main ConX search-server health (public endpoint on ConX)."""
    url = f"{base_url.rstrip('/')}/api/search-servers-health"
    try:
        resp = requests.get(url, timeout=timeout)
        data = resp.json()
        if isinstance(data, dict):
            servers = data.get("servers") or []
            live = sum(1 for s in servers if (s.get("status") or "") == "live")
            return {
                "ok": resp.ok,
                "reachable": True,
                "servers": servers,
                "live_count": live,
                "total_count": len(servers),
                "degraded": bool(servers) and live < len(servers),
            }
    except requests.RequestException:
        pass
    return {
        "ok": False,
        "reachable": False,
        "servers": [],
        "live_count": 0,
        "total_count": 0,
        "degraded": True,
    }
