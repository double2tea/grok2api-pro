# Proxy Policy

This document describes how proxy selection, SSO binding, and health switching work in the current implementation.

## Sources and priority

1. **Static proxy**: `grok.proxy_url` in `data/setting.toml`.
2. **Proxy pool API**: `grok.proxy_pool_url` (if provided, proxies are fetched and added to the pool).
3. **Manual proxies**: proxies added through the admin panel are stored in the pool.
4. **Multiple proxies**: `grok.proxy_urls` (if set in config) are added to the pool at startup.

## SSO binding (automatic)

When an SSO is present:
- If the SSO already has a bound proxy **and it is healthy**, that proxy is used.
- If the bound proxy is missing or unhealthy, the binding is removed.
- A **healthy proxy is selected** (round-robin) and **auto-bound** to the SSO.
- Binding is persisted in `data/proxy_state.json` (or storage backend).

## Selection strategy

- **Primary**: round-robin among **healthy** proxies in the pool.
- If no healthy proxies are available:
  - If proxy pool API is enabled, fetch a new proxy and try again.
  - Otherwise fall back to the static proxy (if configured).

## Health rules

- Each proxy tracks `fail_count` and health status.
- After **3 consecutive failures**, the proxy is marked **unhealthy** and all its bound SSO are unbound.
- On success, `fail_count` is reset and unhealthy proxies can be restored to healthy.

## Switching behavior

- Requests with SSO use `get_proxy_for_sso()`: it will keep a stable proxy when healthy and only switch when unhealthy.
- Requests without SSO use `get_proxy()` (round-robin / pool / fallback).
- 403 errors can trigger forced refresh when proxy pool is enabled.

## Where this is implemented

- Proxy pool and bindings: `app/core/proxy_pool.py`
- Proxy usage in requests: `app/services/grok/client.py`, `app/services/grok/create.py`, `app/services/grok/upload.py`, `app/services/grok/token.py`
