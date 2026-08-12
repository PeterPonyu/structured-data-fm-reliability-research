# structured-data-fm-reliability-research manuscript Makefile
# (adapted from reliability-commons/paper-template)
#
# Targets:
#   make figures  - run every figures/*.R via Rscript (figures regenerate
#                   ONLY from on-disk result JSONs in ../experiments/results)
#   make fig0     - compile the standalone TikZ audit-design schematic
#                   (figures/fig0_overview.tex -> fig0_overview.pdf); symbolic,
#                   not data-driven, so it is its own target outside R_SCRIPTS
#   make bib      - copy the portfolio shared bibliography next to the paper
#   make paper    - figures + fig0 + bib, then latexmk -pdf
#   make clean    - remove LaTeX aux files and generated figure PDFs/PNGs
#
# Override SHARED_BIB if reliability-commons lives elsewhere:
#   make paper SHARED_BIB=/path/to/reliability-commons/shared.bib

SHARED_BIB ?= ${COMMONS_ROOT}/shared.bib
R_SCRIPTS  := figures/p4_figs_expansions.R

.PHONY: all figures fig0 bib paper clean

all: paper

figures:
	@for s in $(R_SCRIPTS); do \
		echo "Rscript $$s"; \
		Rscript "$$s" || exit 1; \
	done

fig0:
	@cd figures && pdflatex -interaction=nonstopmode -halt-on-error fig0_overview.tex >/dev/null
	@echo "Built figures/fig0_overview.pdf"

bib:
	@if [ -f "$(SHARED_BIB)" ]; then \
		cp "$(SHARED_BIB)" shared.bib; \
		echo "Copied $(SHARED_BIB) -> shared.bib"; \
	else \
		echo "WARNING: $(SHARED_BIB) not found; creating empty shared.bib"; \
		touch shared.bib; \
	fi

paper: figures fig0 bib
	latexmk -pdf -interaction=nonstopmode paper.tex

clean:
	latexmk -C paper.tex 2>/dev/null || true
	rm -f paper.bbl paper.run.xml shared.bib
	rm -f figures/F*.pdf figures/F*.png figures/p4_table.csv figures/p5_tableshift_table.csv
	rm -f figures/fig0_overview.aux figures/fig0_overview.log figures/fig0_overview.pdf
