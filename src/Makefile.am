
labyrinth: labyrinth.py
	sed -e "s|\@PYTHONDIR\@|$(pythondir)/labyrinth|" $< > $@

labyrinthbindir = $(prefix)/bin
labyrinthbin_SCRIPTS = labyrinth

labyrinthdir = $(pythondir)/labyrinth
labyrinth_PYTHON = 	\
	defs.py		\
	MainWindow.py	\
	MMapArea.py	\
	TextThought.py	\
	__init__.py	\
	Links.py	\
	utils.py	\
	Browser.py	\
	BaseThought.py	\
	ImageThought.py	\
	DrawingThought.py

nodist_labyrinth_PYTHON = defs.py

defs.py: defs.py.in
	sed						\
		-e s!\@prefix\@!$(prefix)!		\
		-e s!\@datadir\@!$(datadir)!		\
		-e s!\@pkgdatadir\@!$(pkgdatadir)!	\
		-e s!\@libexecdir\@!$(libexecdir)!	\
		-e s!\@libdir\@!$(libdir)!		\
		-e s!\@PACKAGE\@!$(PACKAGE)!		\
		-e s!\@VERSION\@!$(VERSION)!		\
		-e s!\@PYTHONDIR\@!$(PYTHONDIR)!    \
		< $< > $@
defs.py: Makefile

BUILT_SOURCES = labyrinth

CLEANFILES = $(BUILT_SOURCES)

DISTCLEANFILES = \
	defs.py	\
	$(CLEANFILES)

EXTRA_DIST = defs.py.in \
	labyrinth.py
