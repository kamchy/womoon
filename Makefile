ASCIIDOC=/usr/bin/asciidoc
DOCFILES=README.html notes.html

# main target generates html documentation for the project
main: doc

doc:  $(DOCFILES)
%.html: %.txt
	$(ASCIIDOC) $^

clean:
	rm -f *.pyc *.html
	rm -rf build

