#!/bin/bash
# Re-run os1.sh for each flagged student and print exactly what happens.
# Usage (from WSL): bash Ex1/verify_part1.sh
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
SUBS="$ROOT/subs-2026B"
TIMEOUT_SECS=15

STUDENTS=(
  "איזבלה סבבוליה_89927_assignsubmission_file"
  "בן ואן_89873_assignsubmission_file"
  "בן חייטין_89905_assignsubmission_file"
  "גינאן עאסי_89869_assignsubmission_file"
  "דורון שן צור_89934_assignsubmission_file"
  "דימיטרי טודוסייב_89916_assignsubmission_file"
  "יואב וינשטיין_89865_assignsubmission_file"
  "יובל גבאי_89875_assignsubmission_file"
  "ירון מירולוז_89900_assignsubmission_file"
  "ליאור רוסנובסקי_89936_assignsubmission_file"
  "ליאור שמחייב_89920_assignsubmission_file"
  "מאור אדירים_89892_assignsubmission_file"
  "מאי חגבי_89891_assignsubmission_file"
  "מאיה גבע_89937_assignsubmission_file"
  "משה יניב טל_89895_assignsubmission_file"
  "נועה צבעוני_89939_assignsubmission_file"
  "ניצן בר אור_89884_assignsubmission_file"
  "עדי פנסו_89874_assignsubmission_file"
  "עידן גלובוס_89935_assignsubmission_file"
  "עידן שאול_89909_assignsubmission_file"
  "רום מאיר_89925_assignsubmission_file"
  "רועי שלום_89890_assignsubmission_file"
  "רחלי שיראל בר לב_89858_assignsubmission_file"
  "שחר קלדרון_89886_assignsubmission_file"
  "שירה גולן_89893_assignsubmission_file"
  "תומר כהן_89908_assignsubmission_file"
)

for s in "${STUDENTS[@]}"; do
  echo
  echo "================================================================"
  echo "STUDENT: $s"
  echo "================================================================"
  src_dir="$SUBS/$s"
  if [ ! -f "$src_dir/os1.sh" ]; then
    echo "  (no os1.sh)"
    continue
  fi

  tmp="$(mktemp -d /tmp/os1_verify_XXXXXX)"
  # Copy os1.sh with LF endings
  tr -d '\r' < "$src_dir/os1.sh" > "$tmp/os1.sh"
  # Copy os1.c so it can be compiled
  if [ -f "$src_dir/os1.c" ]; then
    cp "$src_dir/os1.c" "$tmp/os1.c"
  else
    # Fall back to lecturer solution
    cp "$ROOT/p_solution/os1.c" "$tmp/os1.c"
  fi
  src_c="$tmp/os1.c"

  pushd "$tmp" >/dev/null
  stdout_file="$tmp/stdout.txt"
  stderr_file="$tmp/stderr.txt"
  timeout "${TIMEOUT_SECS}s" bash os1.sh test_output_dir "$src_c" /tmp >"$stdout_file" 2>"$stderr_file"
  rc=$?
  popd >/dev/null

  echo "  exit=$rc (124 = timeout)"
  out_dir="$tmp/test_output_dir"
  if [ -d "$out_dir" ]; then
    echo "  dir created: YES"
    echo "  dir contents:"; ls -la "$out_dir" | sed 's/^/    /'
    if [ -f "$out_dir/greeting.txt" ]; then
      echo "  greeting.txt:"; sed 's/^/    /' "$out_dir/greeting.txt"
    else
      echo "  greeting.txt: MISSING"
      # Look for similarly-named files
      maybe=$(ls -1 "$out_dir" 2>/dev/null | grep -i greet || true)
      [ -n "$maybe" ] && echo "    (similar filenames: $maybe)"
    fi
    if [ -f "$out_dir/os1exe" ]; then
      echo "  os1exe: YES"
    else
      echo "  os1exe: MISSING"
      bad=$(ls -1 "$out_dir" 2>/dev/null | grep -Ei 'exe|os1' | grep -v '\.c$' || true)
      [ -n "$bad" ] && echo "    (other binary-ish files: $bad)"
    fi
  else
    echo "  dir created: NO"
  fi

  echo "  --- stdout (first 10 lines) ---"
  head -n 10 "$stdout_file" | sed 's/^/    /'
  if [ -s "$stderr_file" ]; then
    echo "  --- stderr (first 10 lines) ---"
    head -n 10 "$stderr_file" | sed 's/^/    /'
  fi
  rm -rf "$tmp"
done
