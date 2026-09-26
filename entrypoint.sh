#!/bin/sh
set -eu

# Cloud Run injects the OIDC configuration from Secret Manager at runtime.
if [ -n "${METABOTRACK_STREAMLIT_SECRETS:-}" ]; then
  mkdir -p "$HOME/.streamlit"
  umask 077
  printf '%s' "$METABOTRACK_STREAMLIT_SECRETS" > "$HOME/.streamlit/secrets.toml"
fi

exec streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8080}" \
  --server.headless=true
