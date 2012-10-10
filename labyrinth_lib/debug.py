"""Debugging functions"""

def show_attrlist(al):
    """Display a pango attribute list."""
    it = al.get_iterator()
    def show_range():
        print "%d-%d:" % it.range(),
        for x in it.get_attrs():
            print (x.type, x.start_index, x.end_index),
            if hasattr(x, 'value'):
                print x.value,
        print
    
    show_range()
    while it.next():
        show_range()
