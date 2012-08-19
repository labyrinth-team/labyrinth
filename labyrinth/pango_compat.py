from gi.repository import Pango

class AttrIterator():
    def __init__ (self, attributes=[]):
        self.attributes = attributes
        self.attribute_stack = []
        self.start_index = 0
        self.end_index = 0
        if not self.next():
            self.end_index = 2**32 -1

    def next(self):
        if len(self.attributes) == 0 and len(self.attribute_stack) == 0:
            return False
        self.start_index = self.end_index
        self.end_index = 2**32 - 1

        to_remove = []
        for attr in self.attribute_stack:
            if attr.end_index == self.start_index:
                to_remove.append(attr)
            else:
                self.end_index = min(self.end_index, attr.end_index)

        while len(to_remove) > 0:
            attr = to_remove[0]
            self.attribute_stack.remove(to_remove[0])
            try:
                to_remove.remove(attr)
            except:
                pass

        while len(self.attributes) != 0 and \
              self.attributes[0].start_index == self.start_index:
            if self.attributes[0].end_index > self.start_index:
                self.attribute_stack.append(self.attributes[0])
                self.end_index = min(self.end_index, self.attributes[0].end_index)
            self.attributes = self.attributes[1:]
        if len(self.attributes) > 0:
            self.end_index = min(self.end_index, self.attributes[0].start_index)
        return True

    def range(self):
        return (self.start_index, self.end_index)

#Dont create pango.fontdesc as it should. But half working.
    def get_font(self):
        tmp_list1 = self.attribute_stack
        fontdesc = Pango.FontDescription()
        for attr in self.attribute_stack:
            if attr.klass.type == Pango.ATTR_FONT_DESC:
                tmp_list1.remove(attr)
                attr.__class__ = gi.repository.Pango.AttrFontDesc
                fontdesc = attr.desc
        return (fontdesc, None, self.attribute_stack)



def get_iterator(self):
    tmplist = []
    def fil(val, data):
        print val, data
        tmplist.append(val)
        return False
    self.filter(fil, None)
    return AttrIterator(tmplist)


setattr(Pango.AttrList, 'get_iterator', get_iterator)

from copy import copy
class _InstantiableAttribute(Pango.Attribute):
    _attrtype = None
    def __new__(cls, value, start_index=0, end_index=1):
        inst = copy(prototypes[cls._attrtype])
        inst.value = value
        inst.start_index = start_index
        inst.end_index = end_index
        return inst

class AttrStyle(_InstantiableAttribute):
   _attrtype = Pango.AttrType.STYLE
Pango.AttrStyle = AttrStyle

class AttrWeight(_InstantiableAttribute):
    _attrtype = Pango.AttrType.WEIGHT
Pango.AttrWeight = AttrWeight

class AttrUnderline(_InstantiableAttribute):
    _attrtype = Pango.AttrType.UNDERLINE
Pango.AttrUnderline = AttrUnderline

class AttrFamily(Pango.Attribute):
   pass
Pango.AttrFamily = AttrFamily

class AttrVariant(Pango.Attribute):
   pass
Pango.AttrVariant = AttrVariant

class AttrVariant(Pango.Attribute):
   pass
Pango.AttrVariant = AttrVariant

class AttrStretch(Pango.Attribute):
   pass
Pango.AttrStretch = AttrStretch


class _InstantiableColorAttribute(Pango.Attribute):
    _attrtype = None
    def __new__(cls, r, g, b, start_index=0, end_index=1):
        inst = copy(prototypes[cls._attrtype])
        inst.color = Pango.Color()
        inst.color.red, inst.color.green, inst.color.blue =  r, g, b
        inst.start_index = start_index
        inst.end_index = end_index
        inst.__class__ = Pango.Attribute
        return inst

class AttrBackground(_InstantiableColorAttribute):
    _attrtype = Pango.AttrType.BACKGROUND
Pango.AttrBackground = AttrBackground

class AttrForeground(_InstantiableColorAttribute):
    _attrtype = Pango.AttrType.FOREGROUND
Pango.AttrForeground = AttrForeground

class AttrFontDesc_(Pango.Attribute):
    _attrtype = Pango.AttrType.FONT_DESC
    def __new__(cls, font_desc, start_index=0, end_index=1):
        # HORRIBLE HACK: I can't find any way to create an AttrFontDesc besides
        # converting the description back to a string and parsing it like this.
        markup = '<span font_desc="%s">a</span>' % font_desc.to_string()
        inst = make_prototype(markup)
        inst.start_index = start_index
        inst.end_index = end_index
        return inst
Pango.AttrFontDesc_ = AttrFontDesc_


#And to access values 
pango_type_table = {
    Pango.AttrType.SIZE: Pango.AttrInt,
    Pango.AttrType.WEIGHT: Pango.AttrInt,
    Pango.AttrType.UNDERLINE: Pango.AttrInt,
    Pango.AttrType.STRETCH: Pango.AttrInt,
    Pango.AttrType.VARIANT: Pango.AttrInt,
    Pango.AttrType.STYLE: Pango.AttrInt,
    Pango.AttrType.SCALE: Pango.AttrFloat,
    Pango.AttrType.FAMILY: Pango.AttrString,
    Pango.AttrType.FONT_DESC: Pango.AttrFontDesc,
    Pango.AttrType.STRIKETHROUGH: Pango.AttrInt,
    Pango.AttrType.BACKGROUND: Pango.AttrColor,
    Pango.AttrType.FOREGROUND: Pango.AttrColor,
    Pango.AttrType.RISE: Pango.AttrInt}

def make_with_value(a):
    type_ = a.klass.type
    klass = a.klass
    start_index = a.start_index
    end_index = a.end_index
    #Nasty workaround, but then python object gets value field.
    a.__class__ = pango_type_table[type_]
    a.type = type_
    a.start_index = start_index
    a.end_index = end_index
    a.klass = klass
    return a

def make_prototype(markup):
    res, attrlist, _, _ = Pango.parse_markup(markup, -1, '\0')
    assert res
    
    tmplist = []
    def fil(val, data):
        tmplist.append(val)
        return False
    attrlist.filter(fil, None)
    attr = tmplist[0]
    return make_with_value(attr)

fontdesc_proto = make_prototype('<span font_desc="Sans Italic 12">a</span>')
mask = fontdesc_proto.desc.get_set_fields()
# Reset the fields to default values, but it crashes if we reset family
fontdesc_proto.desc.unset_fields(Pango.FontMask(mask & ~Pango.FontMask.FAMILY))   
del mask

prototypes = {
    Pango.AttrType.STYLE: make_prototype("<i>a</i>"),
    Pango.AttrType.WEIGHT: make_prototype("<b>a</b>"),
    Pango.AttrType.UNDERLINE: make_prototype("<u>a</u>"),
    Pango.AttrType.BACKGROUND: make_prototype('<span background="red">a</span>'),
    Pango.AttrType.FOREGROUND: make_prototype('<span foreground="red">a</span>'),
    Pango.AttrType.FONT_DESC: fontdesc_proto,
    }



