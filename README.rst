Labyrinth
=========

**No-one is actively maintaining Labyrinth at the moment. If you're interested in
taking it on, please open an issue to discuss it.**

Labyrinth is a lightweight mind-mapping tool, written in Python using Gtk and
Cairo to do the drawing.  It is intended to be as light and intuitive as
possible, but still provide a wide range of powerful features.

A mind-map is a diagram used to represent words, ideas, tasks or other items
linked to and arranged radially around a central key word or idea. It is used
to generate, visualise, structure and classify ideas, and as an aid in study,
organisation, problem solving, and decision making. (From wikipedia)

Currently, Labyrinth provides 3 different types of thoughts, or nodes - Text,
Image and Drawing.  Text is the basic standard text node.  Images allow you to
insert and scale any supported image file (png, jpeg, svg).  Drawings are for
those times when you want to illustrate something, but don't want to fire up
a separate drawing program.  It allows you to quickly and easily sketch very
simple line diagrams.

License
-------

This software is released under the GNU GPL v2 (or later) license.  All source
files are included in this, unless explicitly stated in the source file itself.
For copyright owners, please refer to the source files individually.

The "labyrinth" icon (``data/labyrinth.svg`` and ``data/labyrinth-*.png``) is
copyright Josef Vybíral and is released under the GNU GPL v2 license.

Please refer to the "COPYING" file for a complete copy of the GNU GPL v2
license.

All documentation (This file, anything in the docs directory) released with
this package is released as public domain.  The documentation, you can do with
as you please.

Requirements
------------

* Python >= 2.6
* gtk+
* pygtk
* pygobject
* pycairo
* PyXDG

The minimum required versions are unknown, but any reasonably recent packages
should work.

How to use it
-------------

From the top directory of the package, run the command::

    ./labyrinth

You can also install Labyrinth with ``python setup.py install``, and
``./install_data_files.sh`` for icons and translations. It can then be run as
``labyrinth``.

This will open a browser window, showing you all the maps currently available
and allow you to modify / delete them and create new maps.  The title is
(currently) the primary thought text(truncated to 27 characters long).  This is
usually the first thought created in a new map.

In a new map, single click somewhere to create a new "thought".  This is your
root.  Add your main thought to this.  Click somewhere else will create a new
thought, linked to the first.  To move thoughts around, single-click and drag.
To edit a current thought, double click on it (text thoughts only).

Drawing and Image thoughts can be resized using their corners / sides.

Links between thoughts can be created, strengthened and weakened.  To create a
new link, in edit mode, click and drag from the "parent" thought to the "child"
thought while holding down the ctrl key.  Doing this with a link already in
place will strengthen the link by 1 and dragging from child to parent will
weaken the link by 1.  If the link goes to 0 strength (it starts at 2),
the link is deleted.  Links can also be created / deleted by selecting both
thoughts (hold down the shift key to select > 1 thought) and choosing
"Edit->(Un)Link Thoughts" from the menu (shortcut: Ctrl-L).

Loading and saving of maps is in the tomboy style - they are automatically
saved, you shouldn't have to worry about them.  For reference anyway, the maps
are saved in ``$XDG_DATA_HOME/labyrinth/<longstring>.map``. Please see the Freedesktop 
basedir specification for more information http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html

Future Plans
------------

In ``doc/TheFuture``, there are a list of goals for a 1.0 release and for the next
release. Releases are feature-based at this stage. Once all the required
features are in place, a release is made.

However a release may also be made without all the changes if it is deemed
that this is in the best interest.

Getting the Latest Development Code
-----------------------------------

Development happens on Github. See https://github.com/labyrinth-team/labyrinth

Helping Out and Questions
-------------------------

If you have any questions about Labyrinth or just want to be part of our gang,
the mailing list address is labyrinth-devel@googlegroups.com

If you want to help out with developing labyrinth, please let us know on the
mailing list.  We aren't just looking for coders.  We're looking for packagers,
artists, doc writers, interface designers, web developers, and just about
anyone else.

Translations now take place `on Transifex <https://www.transifex.com/projects/p/labyrinth/>`_.
If you want to use Transifex in your language, it's very easy to get started.
