#!/bin/bash
# ---------------------------------------------------------------------------
# EcoChain Exchange - HashiCorp Vault setup (dev mode demo)
#
# Run this AFTER `docker compose up -d vault`
# Usage:
#   chmod +x vault-setup.sh
#   ./vault-setup.sh
# ---------------------------------------------------------------------------

export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="root"   # dev root token set in docker-compose.yml

echo ">> Checking Vault status..."
vault status

echo ">> Enabling the KV v2 secrets engine at path 'ecochain/'..."
vault secrets enable -path=ecochain kv-v2

echo ">> Storing database credentials..."
vault kv put ecochain/database \
    username="ecochain" \
    password="ecochain_pass" \
    host="postgres" \
    port="5432" \
    dbname="ecochain"

echo ">> Storing application secret key..."
vault kv put ecochain/app \
    secret_key="$(openssl rand -hex 32)"

echo ">> Creating a read-only policy for the application..."
cat > ecochain-app-policy.hcl <<EOF
path "ecochain/data/database" {
  capabilities = ["read"]
}
path "ecochain/data/app" {
  capabilities = ["read"]
}
EOF

vault policy write ecochain-app-policy ecochain-app-policy.hcl

echo ">> Creating an application token scoped to the policy..."
vault token create -policy="ecochain-app-policy" -ttl="24h"

echo ">> Done. Verify secrets with:"
echo "   vault kv get ecochain/database"
echo "   vault kv get ecochain/app"
