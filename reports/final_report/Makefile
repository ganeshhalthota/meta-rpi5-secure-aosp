MAIN    = main
LATEX   = pdflatex
BIBTEX  = bibtex
LATEXMK = latexmk

.PHONY: all clean distclean

all:
	$(LATEXMK) -pdf -interaction=nonstopmode $(MAIN).tex

# Fallback without latexmk
manual:
	$(LATEX) $(MAIN).tex
	$(BIBTEX) $(MAIN)
	$(LATEX) $(MAIN).tex
	$(LATEX) $(MAIN).tex

clean:
	$(LATEXMK) -c
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk

distclean: clean
	rm -f $(MAIN).pdf
