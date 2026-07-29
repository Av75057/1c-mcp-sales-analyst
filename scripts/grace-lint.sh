#!/usr/bin/env bash
set -euo pipefail

CI_MODE=false
[[ "${1:-}" == "--ci" ]] && CI_MODE=true

ERRORS=0
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

info() { $CI_MODE || echo "[INFO] $*"; }
ok()   { $CI_MODE || echo "  [OK] $*"; }
fail() { echo "  [FAIL] $*"; ERRORS=$((ERRORS + 1)); }

# ---- 1. XML well-formedness ----
info "1. Проверка XML-синтаксиса..."
for xml in "$ROOT"/docs/*.xml; do
  [[ -f "$xml" ]] || continue
  name=$(basename "$xml")
  if python3 -c "import xml.etree.ElementTree as ET; ET.parse('$xml')" 2>/dev/null; then
    ok "$name"
  else
    fail "$name — невалидный XML"
  fi
done

# ---- 2. Проверка START_BLOCK/END_BLOCK баланса ----
info "2. Проверка START_BLOCK/END_BLOCK баланса..."
PY_FILES=(
  "$ROOT/src/server.py"
  "$ROOT/src/tools.py"
  "$ROOT/src/mcp/tools.py"
  "$ROOT/src/clients/c1_client.py"
  "$ROOT/src/clients/batch_client.py"
  "$ROOT/src/whatif/mcp/tools.py"
)
for py in "${PY_FILES[@]}"; do
  name="$(basename "$(dirname "$py")")/$(basename "$py")"
  if [[ ! -f "$py" ]]; then
    info "$name — файл не найден, пропускаем"
    continue
  fi
  starts=$(grep -c "START_BLOCK_" "$py" 2>/dev/null || true)
  ends=$(grep -c "END_BLOCK_" "$py" 2>/dev/null || true)
  starts=${starts:-0}
  ends=${ends:-0}
  if [[ "$starts" -eq "$ends" ]]; then
    ok "$name: $starts блоков"
  else
    fail "$name: START=$starts END=$ends — несоответствие"
  fi
done

# ---- 3. Покрытие инструментов из requirements.xml ----
info "3. Проверка покрытия инструментов..."
if [[ -f "$ROOT/docs/requirements.xml" ]]; then
  tools_in_xml=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$ROOT/docs/requirements.xml')
root = tree.getroot()
ns = {'g': 'https://opencode.ai/grace/requirements/v1'}
for c in root.findall('.//g:contract', ns):
    tid = c.get('id')
    if tid:
        print(tid)
" 2>/dev/null || echo "")

  tools_in_code=""
  for registry_file in "$ROOT/src/mcp/tools.py" "$ROOT/src/tools.py"; do
    if [[ -f "$registry_file" ]]; then
      found=$(python3 -c "
import ast
with open('$registry_file') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.Dict) and node.keys:
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                print(k.value)
" 2>/dev/null || echo "")
      tools_in_code="$tools_in_code
$found"
    fi
  done
  tools_in_code=$(echo "$tools_in_code" | sort -u)

  for tool in $tools_in_xml; do
    if echo "$tools_in_code" | grep -qF "$tool"; then
      ok "$tool — есть в TOOLS_REGISTRY"
    else
      fail "$tool — НЕТ в TOOLS_REGISTRY"
    fi
  done
else
  info "requirements.xml не найден, пропускаем"
fi

# ---- Итог ----
if [[ $ERRORS -eq 0 ]]; then
  $CI_MODE || echo ""
  echo "GRACE LINT: OK (0 ошибок)"
  exit 0
else
  echo ""
  echo "GRACE LINT: $ERRORS ошибок" >&2
  exit 1
fi
