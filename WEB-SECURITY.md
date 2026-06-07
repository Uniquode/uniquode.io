# Web Security

This document records deployment-facing web security conventions for the
`uniquode` application.

## HTTPS Scheme Detection

Browser session cookies derive their `Secure` attribute from the ASGI request
scheme:

- `http` responses emit non-secure session cookies.
- `https` responses emit secure session cookies.
- `wss` is treated as secure for cookie semantics.

When TLS terminates at a reverse proxy, the proxy must send trustworthy
forwarding headers and Uvicorn must be configured to trust only that proxy. If
Uvicorn does not trust the proxy, `request.scope["scheme"]` remains `http` even
when the browser used HTTPS, so session cookies will not be marked `Secure`.

Use the actual proxy source IP in `--forwarded-allow-ips`. Do not use `*` unless
the app is reachable only from fully trusted infrastructure; trusting forwarded
headers from arbitrary clients lets them spoof the original scheme and client
address.

```sh
uv run wevra-runserver --host 127.0.0.1 --port 8000 -- --proxy-headers --forwarded-allow-ips 127.0.0.1
```

Non-local deployments must set `SESSION_FORCE_SECURE=1`. This is also the
explicit fallback when the ASGI request scheme cannot be made reliable but
browser traffic is still HTTPS. Prefer trusted proxy-header normalisation where
possible because redirects and request context still depend on the request
scheme.

The FastAPI Users authentication backend uses a static cookie transport and
cannot derive cookie security from each request. `SESSION_FORCE_SECURE=1` keeps
that transport aligned with first-party login/logout cookies in non-local
deployments, while the default remains suitable for local HTTP development.

## Nginx

Example Nginx TLS virtual host:

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Run the application so Uvicorn trusts the Nginx proxy source IP:

```sh
uv run wevra-runserver --host 127.0.0.1 --port 8000 -- --proxy-headers --forwarded-allow-ips 127.0.0.1
```

If Nginx runs on a different host or container network address, replace
`127.0.0.1` with that source IP.

## Apache

The Apache example assumes `proxy`, `proxy_http`, `headers`, and `ssl` modules
are enabled.

```apache
<VirtualHost *:80>
    ServerName example.com
    Redirect permanent / https://example.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName example.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/example.com/privkey.pem

    ProxyPreserveHost On
    ProxyAddHeaders On
    RequestHeader set X-Forwarded-Proto "https"

    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

Run the application so Uvicorn trusts the Apache proxy source IP:

```sh
uv run wevra-runserver --host 127.0.0.1 --port 8000 -- --proxy-headers --forwarded-allow-ips 127.0.0.1
```

If Apache runs on a different host or container network address, replace
`127.0.0.1` with that source IP.
