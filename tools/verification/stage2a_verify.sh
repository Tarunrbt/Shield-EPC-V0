#!/usr/bin/env bash
# Stage 2A verification script for Shield-EPC-V0 (updated)
# Purpose: reproducibly run tooling-based dead-code detection (vulture + ruff)
# and cross-check current-tree and history references for candidate modules.
#
# Usage:
#   1) Clone repository locally: git clone https://github.com/Tarunrbt/Shield-EPC-V0.git
#   2) cd Shield-EPC-V0
#   3) Save this script as stage2a_verify.sh and make executable: chmod +x stage2a_verify.sh
#   4) Run: ./stage2a_verify.sh
#
# Outputs (created under repository root):
#   - vulture_report.txt        (vulture findings)
#   - ruff_unused.txt           (ruff unused-imports/unused-vars findings)
#   - stage2a_candidates.txt    (per-candidate raw git-grep + history + tool excerpts)
#   - stage2a_classification.txt (deterministic classification per candidate)
#
# Notes on classification (implemented exactly as requested):
# - Classification uses only textual repository evidence:
#     IF CurrentTreeHits > 0 -> Live
#     ELSE IF CurrentTreeHits == 0 AND HistoryHits > 0 -> Candidate Unused
#     ELSE IF CurrentTreeHits == 0 AND HistoryHits == 0 -> Candidate Unused (High Confidence)
# - vulture and ruff are recorded as supporting evidence columns (VultureFlag, RuffFlag)
#   and are NOT used for classification logic.
# - The script NEVER declares Confirmed Unused automatically.
#
# After running, paste vulture_report.txt, ruff_unused.txt, stage2a_classification.txt,
# and stage2a_candidates.txt back into the chat for Stage 2A analysis.

set -euo pipefail

# -------- Configuration --------
MIN_CONFIDENCE=50
VULTURE_REPORT="vulture_report.txt"
RUFF_REPORT="ruff_unused.txt"
CANDIDATES_RAW="stage2a_candidates.txt"
CLASSIFY_OUT="stage2a_classification.txt"
HISTORY_TMP="stage2a_history_raw.txt"

# Candidate list (path relative to repo root). Add additional candidates if desired.
CANDIDATES=(
  "ai-agents/pipeline/groq_preprocess.py"
)

# Helper: check command availability
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Pre-flight: ensure we are in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: Not inside a git repository. Clone the repository and run this script from its root." >&2
  exit 2
fi

# Check for required tooling
MISSING_TOOLS=()
for tool in python3 git; do
  if ! command_exists "$tool"; then
    MISSING_TOOLS+=("$tool")
  fi
done

if ! command_exists vulture; then
  MISSING_TOOLS+=("vulture")
fi
if ! command_exists ruff; then
  MISSING_TOOLS+=("ruff")
fi

if [ "${#MISSING_TOOLS[@]}" -ne 0 ]; then
  echo "ERROR: Missing required tools: ${MISSING_TOOLS[*]}" >&2
  echo
  echo "Install instructions (examples):"
  echo "  python3 -m pip install --user vulture ruff"
  echo "  # ensure ~/.local/bin is on PATH or use a virtualenv"
  echo
  echo "After installation, re-run this script."
  exit 3
fi

# -------- Step 1: vulture run (supporting evidence) --------
echo "=== Step 1: running vulture (this may take a while) ==="
# vulture returns non-zero if it finds issues; capture output regardless
vulture . --min-confidence "$MIN_CONFIDENCE" --sort-by-size > "$VULTURE_REPORT" || true
echo "Wrote vulture output to $VULTURE_REPORT"
echo

# -------- Step 2: ruff run for selected codes (unused imports, unused vars) --------
echo "=== Step 2: running ruff check for F401 (unused imports) and F841 (unused variables) ==="
ruff check . --select F401,F841 > "$RUFF_REPORT" || true
echo "Wrote ruff output to $RUFF_REPORT"
echo

# -------- Step 3: git history filenames extraction (unique filenames) --------
echo "=== Step 3: history scan for filenames in git history ==="
git log --all --name-only --pretty=format: | sed '/^$/d' | sort -u > "$HISTORY_TMP"
echo "Wrote unique filenames from git history to $HISTORY_TMP"
echo

# -------- Step 4 / 5: Per-candidate current-tree search, tool-flag detection, and classification --------
echo "=== Step 4: per-candidate git grep, tool-flag detection, and deterministic classification ==="
: > "$CANDIDATES_RAW"
: > "$CLASSIFY_OUT"

# CSV header for classification output
printf "Candidate,CurrentTreeHits,HistoryHits,VultureFlag,RuffFlag,Classification,Notes\n" >> "$CLASSIFY_OUT"

for cand in "${CANDIDATES[@]}"; do
  fname="$(basename "$cand")"
  modname="${fname%.py}"

  echo "Processing candidate: $cand"

  # --- Current-tree hits (git grep) ---
  # Capture filename exact occurrences and module-name occurrences
  # Use command substitution to capture outputs and then write them into the raw file.
  CUR_GREP_FILENAME_OUTPUT="$(git grep -n -- "$fname" -- || true)"
  CUR_GREP_MODNAME_OUTPUT="$(git grep -n -- "$modname" -- || true)"

  # Consolidate unique non-empty lines for stability
  {
    printf "%s\n" "$CUR_GREP_FILENAME_OUTPUT"
    printf "%s\n" "$CUR_GREP_MODNAME_OUTPUT"
  } | sed '/^$/d' | sort -u > ./.stage2a_tmp/cur_hits_$$.txt || true

  if [ -s ./.stage2a_tmp/cur_hits_$$.txt ]; then
    CUR_COUNT=$(wc -l < ./.stage2a_tmp/cur_hits_$$.txt || true)
  else
    CUR_COUNT=0
  fi

  # --- History hits: check filename presence in history list (exact match)
  if grep -Fxq "$cand" "$HISTORY_TMP"; then
    HIST_COUNT=1
  elif grep -Fxq "$fname" "$HISTORY_TMP"; then
    HIST_COUNT=1
  else
    HIST_COUNT=0
  fi

  # --- Tool flags (supporting evidence only) ---
  if grep -F -- "$fname" "$VULTURE_REPORT" >/dev/null 2>&1 || grep -F -- "$modname" "$VULTURE_REPORT" >/dev/null 2>&1; then
    VULTURE_FLAG=1
  else
    VULTURE_FLAG=0
  fi

  if grep -F -- "$fname" "$RUFF_REPORT" >/dev/null 2>&1 || grep -F -- "$modname" "$RUFF_REPORT" >/dev/null 2>&1; then
    RUFF_FLAG=1
  else
    RUFF_FLAG=0
  fi

  # --- Classification using only repository reference evidence (exact rules given) ---
  if [ "$CUR_COUNT" -gt 0 ]; then
    CLASS="Live"
    NOTES="Textual references present in current tree."
  else
    if [ "$HIST_COUNT" -gt 0 ]; then
      CLASS="Candidate Unused"
      NOTES="No current-tree textual references, but file appears in git history."
    else
      CLASS="Candidate Unused (High Confidence)"
      NOTES="No current-tree textual references and no history filename matches."
    fi
  fi

  # --- Append classification CSV row ---
  # Ensure commas are escaped by quoting the fields as needed
  printf '%s,%s,%s,%s,%s,%s,"%s"\n' "$cand" "$CUR_COUNT" "$HIST_COUNT" "$VULTURE_FLAG" "$RUFF_FLAG" "$CLASS" "$NOTES" >> "$CLASSIFY_OUT"

  # --- Append detailed per-candidate raw trace to candidates raw file for traceability ---
  {
    echo "=== Candidate: $cand ==="
    echo "Current-tree git grep results (filename and module symbol):"
    if [ -s ./.stage2a_tmp/cur_hits_$$.txt ]; then
      sed -n '1,200p' ./.stage2a_tmp/cur_hits_$$.txt || true
    else
      echo "<no matches in current tree>"
    fi
    echo
    echo "History filename presence (searching git log --all unique names):"
    if [ "$HIST_COUNT" -gt 0 ]; then
      echo "Found in git history filenames list (exact match on $cand or $fname)."
    else
      echo "<no matches in git history filenames>"
    fi
    echo
    echo "VultureFlag: $VULTURE_FLAG (1=yes,0=no)"
    echo "  -- vulture excerpt (if any):"
    grep -n -F -- "$fname" "$VULTURE_REPORT" || grep -n -F -- "$modname" "$VULTURE_REPORT" || echo "<no vulture matches for candidate>"
    echo
    echo "RuffFlag: $RUFF_FLAG (1=yes,0=no)"
    echo "  -- ruff excerpt (if any):"
    grep -n -F -- "$fname" "$RUFF_REPORT" || grep -n -F -- "$modname" "$RUFF_REPORT" || echo "<no ruff matches for candidate>"
    echo
    echo "Classification: $CLASS"
    echo "Notes: $NOTES"
    echo
  } >> "$CANDIDATES_RAW"

  # cleanup per-candidate tmp file
  rm -f ./.stage2a_tmp/cur_hits_$$.txt || true
done

# -------- Step 6: Append Known Limitations note to classification file --------
cat >> "$CLASSIFY_OUT" <<'EOF'

Known limitations

- git grep detects only textual references.
- It cannot detect runtime dispatch.
- It cannot detect importlib usage.
- It cannot detect dynamically constructed filenames.
- It cannot detect subprocess execution built from configuration.
- It cannot detect plugin registration.
- It cannot detect external orchestration outside the repository.

Therefore:

Zero textual references indicate a strong orphaning signal,
but are not sufficient by themselves to prove a module is unused.

Manual review remains required before any module can be classified as
Confirmed Unused.
EOF

echo "Wrote classification CSV to $CLASSIFY_OUT"
echo "Wrote detailed per-candidate raw trace to $CANDIDATES_RAW"
echo "Wrote vulture report to $VULTURE_REPORT"
echo "Wrote ruff report to $RUFF_REPORT"
echo "Wrote git history filenames to $HISTORY_TMP"
echo

echo "=== Short summary ==="
column -t -s, "$CLASSIFY_OUT" || true
echo
echo "Full reports created (paste contents into chat for Stage 2A analysis):"
echo " - $VULTURE_REPORT"
echo " - $RUFF_REPORT"
echo " - $CANDIDATES_RAW"
echo " - $CLASSIFY_OUT"
echo

# Final marker lines (required)
echo "STAGE 2A SCRIPT READY"
echo "STOP."

# End of script
