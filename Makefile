# ── Local LLM Guides ──────────────────────────────────────────────────────────
# Usage:
#   make          — render diagrams + build full site → dist/
#   make diagrams — re-render .dot → PNG only
#   make serve    — build then serve at http://localhost:3000
#   make clean    — remove dist/ and rendered PNGs

DOTS := $(wildcard diagrams/*.dot)
PNGS := $(DOTS:diagrams/%.dot=diagrams/rendered/%.png)

.PHONY: all diagrams site serve clean

all: diagrams site

# ── Diagrams ──────────────────────────────────────────────────────────────────

diagrams: $(PNGS)

diagrams/rendered/%.png: diagrams/%.dot
	@mkdir -p diagrams/rendered
	@dot -Tpng $< -o $@
	@echo "  ✓  $*"

# ── Site ──────────────────────────────────────────────────────────────────────

site: diagrams
	@python3 build.py

serve: all
	@cd dist && python3 -m http.server 3000

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	@rm -rf dist/ diagrams/rendered/
	@echo "  cleaned"
