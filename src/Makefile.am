
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
	BaseThought.py

BUILT_SOURCES = labyrinth

CLEANFILES = $(BUILT_SOURCES)

DISTCLEANFILES = \
	defs.py	\
	$(CLEANFILES)

EXTRA_DIST = defs.py.in \
	labyrinth.py
