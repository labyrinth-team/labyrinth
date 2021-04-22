"""Debugging functions"""

from gi.repository import PangoAttrCast

def show_attrlist(al):
    """Display a pango attribute list."""
    it = al.get_iterator()
    def show_range():
        print("%d-%d:" % it.range(), end=' ')
        for x in it.get_attrs():
            print(x.klass.type, x.start_index, x.end_index, end=' ')
            int_attr = PangoAttrCast.as_int(x)
            if int_attr is not None:
                print(int_attr.value, end=', ')
        print()
    
    show_range()
    while it.next():
        show_range()
