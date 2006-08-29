dnl configure.ac based on the same from
dnl the "deskbar-applet" module

AC_INIT(labyrinth, 0.1, DonScorgie@Blueyonder.co.uk)
AC_CONFIG_SRCDIR(src/__init__.py)
AC_CONFIG_HEADERS(config.h)
AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE
GNOME_COMMON_INIT

AM_MAINTAINER_MODE
AM_DISABLE_STATIC
AM_PROG_LIBTOOL
AC_SUBST(ACLOCAL_AMFLAGS, "$ACLOCAL_FLAGS -I m4")
AC_PROG_CC

dnl ****************************************************************************
dnl * Pkg-Config
dnl ****************************************************************************
AC_CHECK_PROG(HAVE_PKGCONFIG, pkg-config, yes, no)
if test "x$HAVE_PKGCONFIG" = "xno"; then
  AC_MSG_ERROR(you need to have pkgconfig installed !)
fi

dnl ****************************************************************************
dnl * Translation & i18n
dnl ****************************************************************************

GETTEXT_PACKAGE="labyrinth"
IT_PROG_INTLTOOL([0.35.0])
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", [The gettext package])
AM_GLIB_GNU_GETTEXT

dnl ****************************************************************************
dnl * Python 2.4
dnl ****************************************************************************
AM_PATH_PYTHON(2.4)

dnl ****************************************************************************
dnl * Write the values of various paths in defs.py
dnl ****************************************************************************
AC_SUBST(VERSION)
AC_SUBST(PACKAGE)

AS_AC_EXPAND(DATADIR, $datadir)
AC_SUBST(DATADIR)

AS_AC_EXPAND(LIBDIR, $libdir)
AC_SUBST(LIBDIR)

AS_AC_EXPAND(PYTHONDIR, $pythondir)
AC_SUBST(PYTHONDIR)
		
dnl ****************************************************************************
dnl * pkg-config checks for all the goodness
dnl ****************************************************************************
PKG_CHECK_MODULES(LABYRINTH,
        gtk+-2.0            >= 2.8
        pygtk-2.0           >= 2.8
        pygobject-2.0       >= 2.10
        gnome-python-2.0    >= 2.12
        gnome-desktop-2.0   >= 2.14
        pycairo             >= 1.0
)
AC_SUBST(LABYRINTH_CFLAGS)
AC_SUBST(LABYRINTH_LIBS)


AC_MSG_CHECKING(for pygtk defs)
PYGTK_DEFSDIR=`$PKG_CONFIG --variable=defsdir pygtk-2.0`
AC_SUBST(PYGTK_DEFSDIR)
AC_MSG_RESULT($PYGTK_DEFSDIR)

AC_OUTPUT([
Makefile
src/Makefile
src/defs.py
data/Makefile
doc/Makefile
po/Makefile.in
])

echo
echo $PACKAGE v$VERSION
echo

echo Prefix............... : $prefix
echo data_dir............. : $datadir

