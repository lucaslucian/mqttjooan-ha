#!/bin/sh
set -eu
OPTIONS=${JOOAN_OPTIONS:-/data/options.json}
read_option() {
  key="$1"; default="$2"
  python3 - "$OPTIONS" "$key" "$default" <<'PY'
import json,sys
path,key,default=sys.argv[1:4]
try:v=json.load(open(path,encoding="utf-8")).get(key,default)
except Exception:v=default
print(("true" if v else "false") if isinstance(v,bool) else v)
PY
}
TLS_MODE=$(read_option tls_mode auto)
TLS_CERT=$(read_option tls_cert '')
TLS_KEY=$(read_option tls_key '')
mkdir -p /data/tls
case "$TLS_MODE" in
  auto)
    CERT=/data/tls/use1mqtt01.jooaniot.com.crt
    KEY=/data/tls/use1mqtt01.jooaniot.com.key
    if [ ! -s "$CERT" ] || [ ! -s "$KEY" ]; then
      echo "[startup] generating TLS identity for use1mqtt01.jooaniot.com"
      openssl req -x509 -nodes -newkey rsa:2048 -sha256 -days 3650 -keyout "$KEY" -out "$CERT" -subj '/CN=use1mqtt01.jooaniot.com' -addext 'subjectAltName=DNS:use1mqtt01.jooaniot.com' >/dev/null 2>&1
      chmod 600 "$KEY"
    fi
    ;;
  custom)
    [ -n "$TLS_CERT" ] && [ -n "$TLS_KEY" ] || exit 1
    CERT="/ssl/$TLS_CERT"; KEY="/ssl/$TLS_KEY"
    [ -r "$CERT" ] && [ -r "$KEY" ] || exit 1
    ;;
  off) CERT=''; KEY='' ;;
  *) echo "unknown tls_mode: $TLS_MODE" >&2; exit 1 ;;
esac
export JOOAN_OPTIONS="$OPTIONS" JOOAN_TLS_CERT="$CERT" JOOAN_TLS_KEY="$KEY"
exec python3 /opt/mqttjooan/app/main.py
