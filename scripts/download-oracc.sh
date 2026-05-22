#!/usr/bin/env bash
# Download ORACC project JSON packages into source-data/sources/ORACC/.
#
# Usage:
#   ./scripts/download-oracc.sh              # download all projects
#   ./scripts/download-oracc.sh adsd rinap   # download specific projects
#
# Zips are fetched from https://build-oracc.museum.upenn.edu/json/<slug>.zip
# where subproject slugs replace '/' with '-' (e.g. cams/gkab → cams-gkab.zip).
# Each zip extracts to source-data/sources/ORACC/ preserving the internal path
# structure (e.g. cams/gkab/json/cams/gkab/...).
#
# Run from the project root directory.

set -euo pipefail

BASE_URL="https://build-oracc.museum.upenn.edu"
DEST="source-data/sources/ORACC"
REFRESH_DAYS=90

ALL_PROJECTS=(
  # ── top-level ────────────────────────────────────────────────────────────
  adsd
  akklove
  amgg
  ario
  armep
  asbp
  atae
  babcity
  balt
  blms
  borsippa
  btmao
  btto
  cams
  ckst
  cmawro
  ctij
  dcclt
  dccmt
  dsst
  ecut
  edlex
  eisl
  epsd2
  etcsl
  etcsri
  glass
  hbtin
  iraq
  lacost
  nere
  nimrud
  obel
  obmc
  obta
  oimea
  pnao
  riao
  ribo
  rime
  rimanum
  rinap
  saao
  suhu
  tcma
  tsae
  urap
  # ── ADSD subprojects ─────────────────────────────────────────────────────
  adsd/adart1
  adsd/adart2
  adsd/adart3
  adsd/adart5
  adsd/adart6
  # ── ASBP subprojects ─────────────────────────────────────────────────────
  asbp/ninmed
  asbp/rlasb
  # ── ATAE subprojects ─────────────────────────────────────────────────────
  atae/assur
  atae/burmarina
  atae/durkatlimmu
  atae/durszarrukin
  atae/guzana
  atae/huzirina
  atae/imgurenlil
  atae/kalhu
  atae/kunalia
  atae/mallanate
  atae/marqasu
  atae/nineveh
  atae/samal
  atae/szibaniba
  atae/tilbarsip
  atae/tuszhan
  # ── CAMS subprojects ─────────────────────────────────────────────────────
  cams/akno
  cams/anzu
  cams/barutu
  cams/etana
  cams/gkab
  cams/ludlul
  cams/ntlab
  cams/selbi
  # ── CMAWRO subprojects ───────────────────────────────────────────────────
  cmawro/cmawr1
  cmawro/cmawr2
  cmawro/cmawr3
  cmawro/maqlu
  # ── DCCLT subprojects ────────────────────────────────────────────────────
  dcclt/ebla
  dcclt/jena
  dcclt/nineveh
  dcclt/signlists
  # ── RIBO subprojects ─────────────────────────────────────────────────────
  ribo/babylon2
  ribo/babylon3
  ribo/babylon4
  ribo/babylon5
  ribo/babylon6
  ribo/babylon7
  ribo/babylon8
  ribo/babylon10
  # ── RINAP subprojects ────────────────────────────────────────────────────
  rinap/rinap1
  rinap/rinap2
  rinap/rinap3
  rinap/rinap4
  rinap/rinap5
  # ── SAAO subprojects ─────────────────────────────────────────────────────
  saao/aebp
  saao/knpp
  saao/saa01
  saao/saa02
  saao/saa03
  saao/saa04
  saao/saa05
  saao/saa06
  saao/saa07
  saao/saa08
  saao/saa09
  saao/saa10
  saao/saa11
  saao/saa12
  saao/saa13
  saao/saa14
  saao/saa15
  saao/saa16
  saao/saa17
  saao/saa18
  saao/saa19
  saao/saa20
  saao/saa21
  saao/saas2
  # ── other subprojects ────────────────────────────────────────────────────
  aemw/amarna
)

if [[ $# -gt 0 ]]; then
  ALL_PROJECTS=("$@")
fi

mkdir -p "$DEST"

ok=0
skip=0
fail=0

for proj in "${ALL_PROJECTS[@]}"; do
  sentinel="$DEST/$proj/.downloaded"

  if [[ -f "$sentinel" ]]; then
    age_days=$(( ( $(date +%s) - $(stat -f %m "$sentinel" 2>/dev/null || stat -c %Y "$sentinel") ) / 86400 ))
    if [[ $age_days -lt $REFRESH_DAYS ]]; then
      echo "  skip  $proj  (${age_days}d old)"
      (( skip++ )) || true
      continue
    fi
  fi

  # Build server uses hyphen slugs: cams/gkab → cams-gkab.zip
  # Fallback to main server for projects the build server returns 500 for (epsd2, cams, etcsl, rime, ctij, lacost, …)
  slug=$(echo "$proj" | tr '/' '-')
  build_url="$BASE_URL/json/$slug.zip"
  main_url="https://oracc.museum.upenn.edu/$proj/json.zip"
  tmpfile=$(mktemp /tmp/oracc-XXXXXX)
  tmpzip="${tmpfile}.zip"
  echo -n "  fetch $proj ... "

  fetched=0
  for try_url in "$build_url" "$main_url"; do
    if curl -fsSLk --max-time 300 --retry 2 --retry-delay 10 -o "$tmpzip" "$try_url" 2>/dev/null; then
      # Verify it's an actual zip (not a 500 HTML page served as 200)
      if unzip -t "$tmpzip" > /dev/null 2>&1; then
        fetched=1
        break
      fi
    fi
    rm -f "$tmpzip"
  done

  if [[ $fetched -eq 1 ]]; then
    # Extract to DEST root: zip's internal paths land correctly
    unzip -q -o "$tmpzip" -d "$DEST"
    mkdir -p "$DEST/$proj"
    touch "$sentinel"
    rm -f "$tmpzip" "$tmpfile"
    echo "ok"
    (( ok++ )) || true
  else
    rm -f "$tmpzip" "$tmpfile"
    echo "FAILED"
    (( fail++ )) || true
  fi
done

echo ""
echo "Done: $ok downloaded, $skip skipped (fresh), $fail failed"
[[ $fail -eq 0 ]]
