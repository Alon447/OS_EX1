#!/bin/bash
# Re-run Part B tests safely. setsid + timeout --kill-after handles fork-bombing submissions.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
SUBS="$ROOT/subs-2026B"
T=5

STUDENTS=(
  "מאיה גבע_89937_assignsubmission_file"
  "משי ברבי_89859_assignsubmission_file"
  "נועה צבעוני_89939_assignsubmission_file"
  "נועם פישביין_89938_assignsubmission_file"
  "ניב לוין_89918_assignsubmission_file"
  "עדן גבריאל באגר_89879_assignsubmission_file"
  "עומר זילברברג_89876_assignsubmission_file"
  "עידן שאול_89909_assignsubmission_file"
  "עמית יוסף_89899_assignsubmission_file"
  "רוי חיים כלפון_89896_assignsubmission_file"
  "שחר קלדרון_89886_assignsubmission_file"
  "שיר חורי_89913_assignsubmission_file"
  "שירה גולן_89893_assignsubmission_file"
)

CMDS=( "ls" "ls -l" "echo hello world" "sleep 1 %" "pwd" "invalid_command" "cat os1.c" )

run_shell () {
  local input="$1"
  printf '%s' "$input" | timeout --foreground --kill-after=2s ${T}s setsid ./os1 2>&1
}

for s in "${STUDENTS[@]}"; do
  echo
  echo "==================================================================="
  echo "STUDENT: $s"
  echo "==================================================================="
  src_dir="$SUBS/$s"
  if [ ! -f "$src_dir/os1.c" ]; then echo "  (no os1.c)"; continue; fi
  tmp="$(mktemp -d /tmp/os1b_XXXXXX)"
  tr -d '\r' < "$src_dir/os1.c" > "$tmp/os1.c"
  pushd "$tmp" >/dev/null
  if ! gcc os1.c -o os1 -Wall 2> compile.err; then
    echo "  COMPILE: FAILED"; head -5 compile.err | sed 's/^/    /'
    popd >/dev/null; rm -rf "$tmp"; continue
  fi
  warns=$(grep -c warning compile.err || true)
  echo "  COMPILE: ok  (warnings: $warns)"

  out=$(run_shell "exit"$'\n')
  rc=$?
  if printf '%s' "$out" | grep -q '\$\$ '; then
    echo "  prompt '\$\$ ': OK"
  else
    snippet=$(printf '%s' "$out" | head -c 80 | tr '\n' ' ')
    echo "  prompt '\$\$ ': MISSING (rc=$rc, got: [$snippet])"
  fi

  for c in "${CMDS[@]}"; do
    out=$(run_shell "$c"$'\n'"exit"$'\n')
    rc=$?
    first=$(printf '%s' "$out" | tr '\n' ' ' | cut -c1-100)
    [ $rc -eq 0 ] && status="ok" || status="rc=$rc"
    printf "  cmd %-22s : %s :: %s\n" "[$c]" "$status" "$first"
    pkill -9 -u "$USER" os1 2>/dev/null || true
    sleep 0.2
  done
  popd >/dev/null
  rm -rf "$tmp"
done
