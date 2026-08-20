FROM nginx:1.27-alpine

# Self-signed cert for the CDN(-terminated TLS)-to-origin leg — the CDN is
# the public-facing HTTPS endpoint with a real cert; this one only needs to
# satisfy a CDN "Full" (non-strict) SSL mode, not a browser.
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout /etc/nginx/ssl/selfsigned.key -out /etc/nginx/ssl/selfsigned.crt \
        -subj "/CN=electronic.itsashop.top"

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:80/ || exit 1
