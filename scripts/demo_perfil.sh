#!/usr/bin/env bash
# Demonstração da Atividade 6 — perfil com foto no object storage (Garage).
#
# Mostra: upload da foto (200), download pela URL assinada (200 image/webp),
# edição de perfil alheio recusada (403) e URL adulterada recusada pelo Garage (403).
#
# Credenciais NUNCA ficam no repositório — passe por variável de ambiente:
#   USER_A_EMAIL=a@x.com USER_A_SENHA=... USER_B_EMAIL=b@x.com USER_B_SENHA=... \
#     ./scripts/demo_perfil.sh
#
# Opcional: BASE_URL (padrão http://localhost:8000) e FOTO (padrão: PNG gerado na hora).
# Requisitos: bash, curl, jq e python3 (só para gerar a imagem de exemplo).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
: "${USER_A_EMAIL:?defina USER_A_EMAIL}" "${USER_A_SENHA:?defina USER_A_SENHA}"
: "${USER_B_EMAIL:?defina USER_B_EMAIL}" "${USER_B_SENHA:?defina USER_B_SENHA}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

verde() { printf '\033[32m%s\033[0m\n' "$*"; }
vermelho() { printf '\033[31m%s\033[0m\n' "$*"; }
titulo() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

FALHAS=0
esperar() { # esperar <descrição> <status esperado> <status obtido>
  if [ "$2" = "$3" ]; then
    verde "  ✔ $1 → HTTP $3"
  else
    vermelho "  ✘ $1 → HTTP $3 (esperado $2)"
    FALHAS=$((FALHAS + 1))
  fi
}

login() { # login <email> <senha> → imprime o JSON do token
  curl -s -X POST "$BASE_URL/api/auth/login" \
    --data-urlencode "username=$1" --data-urlencode "password=$2"
}

titulo "1. Login dos usuários A e B"
RESP_A="$(login "$USER_A_EMAIL" "$USER_A_SENHA")"
RESP_B="$(login "$USER_B_EMAIL" "$USER_B_SENHA")"
TOKEN_A="$(jq -r '.access_token // empty' <<<"$RESP_A")"
TOKEN_B="$(jq -r '.access_token // empty' <<<"$RESP_B")"
if [ -z "$TOKEN_A" ] || [ -z "$TOKEN_B" ]; then
  vermelho "  login falhou: A=$RESP_A B=$RESP_B"
  exit 1
fi
ID_A="$(jq -r '.user.id' <<<"$RESP_A")"
ID_B="$(jq -r '.user.id' <<<"$RESP_B")"
verde "  ✔ A = usuário $ID_A ($USER_A_EMAIL) · B = usuário $ID_B ($USER_B_EMAIL)"

titulo "2. A envia a própria foto"
FOTO="${FOTO:-$TMP/demo-avatar.png}"
if [ ! -f "$FOTO" ]; then
  # PNG 256x256 em degradê, gerado só com a biblioteca padrão do Python
  python3 - "$FOTO" <<'PY'
import struct, sys, zlib
w = h = 256
linhas = b"".join(b"\0" + bytes(v for x in range(w) for v in (x, y, 160)) for y in range(h))
def bloco(tipo, dados):
    return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))
png = b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
    + bloco(b"IDAT", zlib.compress(linhas)) + bloco(b"IEND", b"")
open(sys.argv[1], "wb").write(png)
PY
fi
STATUS="$(curl -s -o "$TMP/upload.json" -w '%{http_code}' -X PUT \
  -H "Authorization: Bearer $TOKEN_A" -F "foto=@$FOTO;type=image/png" \
  "$BASE_URL/api/perfis/$ID_A/foto")"
esperar "PUT /api/perfis/$ID_A/foto (token de A)" 200 "$STATUS"

titulo "3. GET do perfil de A e download pela URL assinada"
FOTO_URL="$(curl -s -H "Authorization: Bearer $TOKEN_A" "$BASE_URL/api/perfis/$ID_A" | jq -r '.foto_url')"
echo "  foto_url: $FOTO_URL"
read -r STATUS TIPO < <(curl -s -o "$TMP/foto.webp" -w '%{http_code} %{content_type}\n' "$BASE_URL$FOTO_URL")
esperar "GET foto_url (sem token: a assinatura é a autorização) [$TIPO, $(wc -c <"$TMP/foto.webp") bytes]" 200 "$STATUS"

titulo "4. A tenta editar a bio de B com o próprio token"
STATUS="$(curl -s -o "$TMP/r4.json" -w '%{http_code}' -X PUT \
  -H "Authorization: Bearer $TOKEN_A" -H 'Content-Type: application/json' \
  -d '{"bio":"perfil invadido"}' "$BASE_URL/api/perfis/$ID_B")"
esperar "PUT /api/perfis/$ID_B (token de A) — $(jq -r '.detail' "$TMP/r4.json")" 403 "$STATUS"

titulo "5. A tenta trocar a foto de B"
STATUS="$(curl -s -o "$TMP/r5.json" -w '%{http_code}' -X PUT \
  -H "Authorization: Bearer $TOKEN_A" -F "foto=@$FOTO;type=image/png" \
  "$BASE_URL/api/perfis/$ID_B/foto")"
esperar "PUT /api/perfis/$ID_B/foto (token de A) — $(jq -r '.detail' "$TMP/r5.json")" 403 "$STATUS"

titulo "6. URL assinada com a assinatura adulterada"
ASSINATURA="$(sed -E 's/.*X-Amz-Signature=([0-9a-f]+).*/\1/' <<<"$FOTO_URL")"
PRIMEIRO="${ASSINATURA:0:1}"
TROCA="$([ "$PRIMEIRO" = "0" ] && echo 1 || echo 0)"
URL_ADULTERADA="${FOTO_URL/X-Amz-Signature=$PRIMEIRO/X-Amz-Signature=$TROCA}"
STATUS="$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL$URL_ADULTERADA")"
esperar "GET com 1 caractere da assinatura trocado (recusado pelo Garage)" 403 "$STATUS"

titulo "7. O banco guarda só a chave"
CHAVE="$(sed -E "s|^/storage/[^/]+/([^?]+)\?.*|\1|" <<<"$FOTO_URL")"
echo "  chave do objeto: $CHAVE"
echo "  Confira no banco (a coluna foto_key tem só a chave, sem host nem assinatura):"
echo "    SELECT usuario_id, foto_key, foto_bytes FROM perfis WHERE usuario_id = $ID_A;"

echo
if [ "$FALHAS" -eq 0 ]; then
  verde "Demonstração concluída: todos os status conferem."
else
  vermelho "$FALHAS verificação(ões) com status inesperado."
  exit 1
fi
