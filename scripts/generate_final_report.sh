#!/bin/bash
set -euo pipefail

# generate_final_report.sh
# Compiles reports/final_report/main.tex and copies the PDF to reports/final_report.pdf
#
# Usage:
#   bash scripts/generate_final_report.sh
#
# Requirements:
#   latexmk (preferred) or pdflatex + bibtex

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${REPO_ROOT}/reports/final_report"
OUT_DIR="${REPO_ROOT}/reports"
MAIN="main"
OUTPUT_PDF="${OUT_DIR}/CS23M510_Final_Thesis.pdf"

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Tool check ──────────────────────────────────────────────────
if command -v latexmk &>/dev/null; then
    USE_LATEXMK=true
elif command -v pdflatex &>/dev/null; then
    USE_LATEXMK=false
    log_warn "latexmk not found — falling back to pdflatex (bibliography may need manual pass)"
else
    log_error "Neither latexmk nor pdflatex found. Install texlive or miktex."
    exit 1
fi

# ── Source directory check ───────────────────────────────────────
if [[ ! -f "${SRC_DIR}/${MAIN}.tex" ]]; then
    log_error "Source not found: ${SRC_DIR}/${MAIN}.tex"
    exit 1
fi

mkdir -p "${OUT_DIR}"

# ── Build ────────────────────────────────────────────────────────
log_info "Building report from ${SRC_DIR}/${MAIN}.tex"

pushd "${SRC_DIR}" > /dev/null

if "${USE_LATEXMK}"; then
    # -f: force completion even if bibtex finds nothing (empty .bib is non-fatal)
    latexmk -pdf -f -interaction=nonstopmode "${MAIN}.tex" || true
else
    pdflatex -interaction=nonstopmode -halt-on-error "${MAIN}.tex"
    if command -v bibtex &>/dev/null; then
        bibtex "${MAIN}" || true
    fi
    pdflatex -interaction=nonstopmode -halt-on-error "${MAIN}.tex"
    pdflatex -interaction=nonstopmode -halt-on-error "${MAIN}.tex"
fi

popd > /dev/null

# ── Copy output ──────────────────────────────────────────────────
if [[ ! -f "${SRC_DIR}/${MAIN}.pdf" ]]; then
    log_error "Build succeeded but PDF not found at ${SRC_DIR}/${MAIN}.pdf"
    exit 1
fi

cp "${SRC_DIR}/${MAIN}.pdf" "${OUTPUT_PDF}"
log_info "Report written to ${OUTPUT_PDF}"
