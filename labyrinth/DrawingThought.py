# DrawingThought.py
# This file is part of Labyrinth
#
# Copyright (C) 2006 - Don Scorgie <Don@Scorgieorg>
#
# Labyrinth is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Labyrinth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Labyrinth; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA
#

import xml.dom.minidom as dom
import xml.dom
import gettext
_ = gettext.gettext
import math

from gi.repository import Gtk, Gdk

import BaseThought
import utils
import UndoManager

STYLE_CONTINUE=0
STYLE_END=1
STYLE_BEGIN=2
ndraw =0

MODE_EDITING = 0
MODE_IMAGE = 1
MODE_DRAW = 2

UNDO_RESIZE = 0
UNDO_DRAW = 1
UNDO_ERASE = 2

class DrawingThought (BaseThought.ResizableThought):
    class DrawingPoint (object):
        def __init__ (self, coords, style=STYLE_CONTINUE, color = Gdk.Color(0,0,0), width = 2):
            self.x, self.y = coords
            self.style = style
            if color is None:
                color = Gdk.Color(0,0,0)
            self.color = color
            self.width = 1
        def move_by (self, x, y):
            self.x += x
            self.y += y

    def __init__ (self, coords, pango_context, thought_number, save, undo, loading, background_color, foreground_color):
        global ndraw
        super (DrawingThought, self).__init__(save, "drawing_thought", undo, background_color, foreground_color)
        ndraw+=1
        self.identity = thought_number
        self.want_move = False
        self.points = []
        self.text = _("Drawing #%d" % ndraw)
        self.drawing = 0
        if not loading:
            margin = utils.margin_required (utils.STYLE_NORMAL)
            self.ul = (coords[0]-margin[0], coords[1]-margin[1])
            self.lr = (coords[0]+100+margin[2], coords[1]+100+margin[3])
            self.min_x = coords[0]+90
            self.max_x = coords[0]+15
            self.min_y = coords[1]+90
            self.max_y = coords[1]+15
            self.width = 100
            self.height = 100

        self.all_okay = True

    def draw (self, context):
        if len (self.extended_buffer.get_text()) == 0:
            utils.draw_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL)
        else:
            utils.draw_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_EXTENDED_CONTENT)
        cwidth = context.get_line_width ()
        context.set_line_width (2)
        if len (self.points) > 0:
            for p in self.points:
                if p.style == STYLE_BEGIN:
                    context.move_to (p.x, p.y)
                    r,g,b = utils.gtk_to_cairo_color(self.foreground_color)
                    context.set_source_rgb (r, g, b)
                elif p.style == STYLE_END:
                    context.line_to (p.x, p.y)
                    context.stroke()
                else:
                    context.line_to (p.x, p.y)

        context.set_line_width (cwidth)
        context.stroke ()
        return

    def want_motion (self):
        return self.want_move

    def recalc_edges (self):
        self.lr = (self.ul[0]+self.width, self.ul[1]+self.height)

    def undo_resize (self, action, mode):
        self.undo.block ()
        choose = 1
        if mode == UndoManager.UNDO:
            choose = 0
        self.ul = action.args[choose][0]
        self.width = action.args[choose][1]
        self.height = action.args[choose][2]
        self.recalc_edges ()
        self.emit ("update_links")
        self.emit ("update_view")
        self.undo.unblock ()

    def undo_drawing (self, action, mode):
        self.undo.block ()
        if mode == UndoManager.UNDO:
            choose = 1
            for p in action.args[0]:
                self.points.remove (p)
        else:
            choose = 2
            for p in action.args[0]:
                self.points.append (p)

        self.ul = action.args[choose][0]
        self.width = action.args[choose][1]
        self.height = action.args[choose][2]
        self.recalc_edges ()
        self.emit ("update_links")
        self.emit ("update_view")
        self.undo.unblock ()

    def process_button_down (self, event, mode, transformed):
        modifiers = Gtk.accelerator_get_default_mod_mask ()
        self.button_down = True
        if event.button == 1:
            if event.type == Gdk.EventType.BUTTON_PRESS:
                self.emit ("select_thought", event.state & modifiers)
                self.emit ("update_view")
            if mode == MODE_EDITING and self.resizing != self.RESIZE_NONE:
                self.want_move = True
                self.drawing = 0
                self.orig_size = (self.ul, self.width, self.height)
                return True
            elif mode == MODE_DRAW:
                self.want_move = True
                self.drawing = 2
                if not event.state & Gdk.ModifierType.SHIFT_MASK:
                    self.drawing = 1
                self.orig_size = (self.ul, self.width, self.height)
                self.ins_points = []
                self.del_points = []
                return True
        elif event.button == 3:
            self.emit ("popup_requested", event, 1)
        self.emit ("update_view")

    def process_button_release (self, event, unending_link, mode, transformed):
        self.button_down = False
        if unending_link:
            unending_link.set_child (self)
            self.emit ("claim_unending_link")
        if len(self.points) > 0:
            self.points[-1].style=STYLE_END
        self.emit ("update_view")
        if self.want_move and self.drawing == 0:
            self.undo.add_undo (UndoManager.UndoAction (self, UNDO_RESIZE, self.undo_resize, \
                                                                                                    self.orig_size, (self.ul, self.width, self.height)))
        elif self.want_move and self.drawing == 1:
            self.undo.add_undo (UndoManager.UndoAction (self, UNDO_DRAW, self.undo_drawing, \
                                                                                                    self.ins_points, self.orig_size, \
                                                                                                    (self.ul, self.width, self.height)))
        elif self.want_move and self.drawing == 2:
            self.undo.add_undo (UndoManager.UndoAction (self, UNDO_ERASE, self.undo_erase, \
                                                                                                    self.ins_points))
        self.drawing = 0
        self.want_move = False

    def undo_erase (self, action, mode):
        self.undo.block ()
        action.args[0].reverse ()
        if mode == UndoManager.UNDO:
            for x in action.args[0]:
                if x[0] == 0:
                    self.points.remove (x[2])
                else:
                    self.points.insert (x[1],x[2])
        else:
            for x in action.args[0]:
                if x[0] == 0:
                    self.points.insert (x[1], x[2])
                else:
                    self.points.remove (x[2])
        self.undo.unblock ()
        self.emit ("update_view")

    def handle_motion (self, event, mode, transformed):
        if (self.resizing == self.RESIZE_NONE or not self.want_move or not event.state & Gdk.ModifierType.BUTTON1_MASK) \
           and mode != MODE_DRAW:
            if not event.state & Gdk.ModifierType.BUTTON1_MASK or mode != MODE_EDITING:
                return False
            else:
                self.emit ("create_link", \
                 (self.ul[0]-((self.ul[0]-self.lr[0]) / 2.), self.ul[1]-((self.ul[1]-self.lr[1]) / 2.)))
        diffx = transformed[0] - self.motion_coords[0]
        diffy = transformed[1] - self.motion_coords[1]
        change = (len(self.points) == 0)
        tmp = self.motion_coords
        self.motion_coords = transformed
        if self.resizing != self.RESIZE_NONE:
            if self.resizing == self.RESIZE_LEFT:
                if self.ul[0] + diffx > self.min_x:
                    self.motion_coords = tmp
                    return True
                self.ul = (self.ul[0]+diffx, self.ul[1])
                if change:
                    self.max_x += diffx
            elif self.resizing == self.RESIZE_RIGHT:
                if self.lr[0] + diffx < self.max_x:
                    self.motion_coords = tmp
                    return True
                self.lr = (self.lr[0]+diffx, self.lr[1])
                if change:
                    self.min_x += diffx
            elif self.resizing == self.RESIZE_TOP:
                if self.ul[1] + diffy > self.min_y:
                    self.motion_coords = tmp
                    return True
                self.ul = (self.ul[0], self.ul[1]+diffy)
                if change:
                    self.max_y += diffy
            elif self.resizing == self.RESIZE_BOTTOM:
                if self.lr[1] + diffy < self.max_y:
                    self.motion_coords = tmp
                    return True
                self.lr = (self.lr[0], self.lr[1]+diffy)
                if change:
                    self.min_y += diffy
            elif self.resizing == self.RESIZE_UL:
                if self.ul[1] + diffy > self.min_y or self.ul[0] + diffx > self.min_x:
                    self.motion_coords = tmp
                    return True
                self.ul = (self.ul[0]+diffx, self.ul[1]+diffy)
                if change:
                    self.max_x += diffx
                    self.max_y += diffy
            elif self.resizing == self.RESIZE_UR:
                if self.ul[1] + diffy > self.min_y or self.lr[0] + diffx < self.max_x:
                    self.motion_coords = tmp
                    return True
                self.ul = (self.ul[0], self.ul[1]+diffy)
                self.lr = (self.lr[0]+diffx, self.lr[1])
                if change:
                    self.min_x += diffx
                    self.max_y += diffy
            elif self.resizing == self.RESIZE_LL:
                if self.lr[1] + diffy < self.max_y or self.ul[0] + diffx > self.min_x:
                    self.motion_coords = tmp
                    return True
                self.ul = (self.ul[0]+diffx, self.ul[1])
                self.lr = (self.lr[0], self.lr[1]+diffy)
                if change:
                    self.max_x += diffx
                    self.min_y += diffy
            elif self.resizing == self.RESIZE_LR:
                if self.lr[1] + diffy < self.max_y:
                    self.motion_coords = tmp
                    return True
                if self.lr[0] + diffx < self.max_x:
                    self.motion_coords = tmp
                    return True
                self.lr = (self.lr[0]+diffx, self.lr[1]+diffy)
                if change:
                    self.min_x += diffx
                    self.min_y += diffy
            self.width = self.lr[0] - self.ul[0]
            self.height = self.lr[1] - self.ul[1]
            self.emit ("update_links")
            self.emit ("update_view")
            return True

        elif self.drawing == 1:
            if transformed[0] < self.ul[0]+5:
                self.ul = (transformed[0]-5, self.ul[1])
            elif transformed[0] > self.lr[0]-5:
                self.lr = (transformed[0]+5, self.lr[1])
            if transformed[1] < self.ul[1]+5:
                self.ul = (self.ul[0], transformed[1]-5)
            elif transformed[1] > self.lr[1]-5:
                self.lr = (self.lr[0], transformed[1]+5)

            if transformed[0] < self.min_x:
                self.min_x = transformed[0]-10
            elif transformed[0] > self.max_x:
                self.max_x = transformed[0]+5
            if transformed[1] < self.min_y:
                self.min_y = transformed[1]-10
            elif transformed[1] > self.max_y:
                self.max_y = transformed[1]+5
            self.width = self.lr[0] - self.ul[0]
            self.height = self.lr[1] - self.ul[1]
            if len(self.points) == 0 or self.points[-1].style == STYLE_END:
                p = self.DrawingPoint (transformed, STYLE_BEGIN, self.foreground_color)
            else:
                p = self.DrawingPoint (transformed, STYLE_CONTINUE)
            self.points.append (p)
            self.ins_points.append (p)
        elif self.drawing == 2 and len (self.points) > 0:
            out = self.points[0]
            loc = []
            handle = []
            ins_point = -1

            for x in self.points:
                ins_point += 1
                dist = (x.x - transformed[0])**2 + (x.y - transformed[1])**2

                if dist < 16:
                    if x == self.points[0]:
                        out = None
                    loc.append ((ins_point, x, dist))
                else:
                    if len(loc) != 0:
                        handle.append ((loc, out, x))
                        loc = []
                    elif x.style != STYLE_BEGIN:
                        x1 = x.x - out.x
                        y1 = x.y - out.y
                        d_rsqr = x1**2 + y1 **2
                        d = ((out.x-transformed[0])*(x.y-transformed[1]) - (x.x-transformed[0])*(out.y-transformed[1]))
                        det = (d_rsqr*16) - d**2
                        if det > 0:
                            xt = -99999
                            yt = -99999
                            xalt = -99999
                            yalt = -99999
                            if y1 < 0:
                                sgn = -1
                            else:
                                sgn = 1
                            xt = (((d*y1) + sgn*x1 * math.sqrt (det)) / d_rsqr) +transformed[0]
                            xalt = (((d*y1) - sgn*x1 * math.sqrt (det)) / d_rsqr) +transformed[0]
                            yt = (((-d*x1) + abs(y1)*math.sqrt(det)) / d_rsqr) + transformed[1]
                            yalt = (((-d*x1) - abs(y1)*math.sqrt(det)) / d_rsqr) +transformed[1]
                            x1_inside = (xt > x.x and xt < out.x) or (xt > out.x and xt < x.x)
                            x2_inside = (xalt > x.x and xalt < out.x) or (xalt > out.x and xalt < x.x)
                            y1_inside = (yt > x.y and yt < out.y) or (yt > out.y and yt < x.y)
                            y2_inside = (yalt > x.y and yalt < out.y) or (yalt > out.y and yalt < x.y)


                            if (x1_inside and x2_inside and y1_inside and y2_inside):
                                if abs (xalt - x.x) < abs (xt - x.x):
                                    handle.append ((None, out, x, ins_point, xt, xalt, yt, yalt))
                                else:
                                    handle.append ((None, out, x, ins_point, xalt, xt, yalt, yt))
                            elif x.x == out.x and y1_inside and y2_inside:
                                if abs (yalt - x.y) < abs (yt - x.y):
                                    handle.append ((None, out, x, ins_point, xt, xalt, yt, yalt))
                                else:
                                    handle.append ((None, out, x, ins_point, xalt, xt, yalt, yt))
                            elif x.y == out.y and x1_inside and x2_inside:
                                if abs (xalt - x.x) < abs (xt - x.x):
                                    handle.append ((None, out, x, ins_point, xt, xalt, yt, yalt))
                                else:
                                    handle.append ((None, out, x, ins_point, xalt, xt, yalt, yt))

                    out = x
            if loc:
                handle.append ((loc, out, None))
            appends = []
            dels = []
            for l in handle:
                inside = l[0]
                prev = l[1]
                next = l[2]
                if not inside:
                    ins = l[3]
                    x1 = l[4]
                    x2 = l[5]
                    y1 = l[6]
                    y2 = l[7]
                    p1 = self.DrawingPoint ((x1,y1), STYLE_END)
                    p2 = self.DrawingPoint ((x2,y2), STYLE_BEGIN)
                    appends.append ((p1, ins))
                    appends.append ((p2, ins))
                else:
                    first = inside[0][1]
                    last = inside[-1][1]
                    done_ins = 0
                    if last.style != STYLE_END:
                        end_dist = math.sqrt (inside[-1][2]) - 4
                        alpha = math.atan2 ((last.y-next.y), (last.x-next.x))
                        new_x = end_dist * math.cos(alpha) + last.x
                        new_y = end_dist * math.sin(alpha) + last.y
                        p = self.DrawingPoint ((new_x, new_y), STYLE_BEGIN)
                        appends.append ((p, inside[-1][0]))
                        done_ins = 1
                    if first.style != STYLE_BEGIN:
                        start_dist = math.sqrt (inside[0][2]) - 4
                        alpha = math.atan2 ((first.y-prev.y),(first.x-prev.x))
                        new_x = start_dist * math.cos (alpha) + first.x
                        new_y = start_dist * math.sin (alpha) + first.y
                        p = self.DrawingPoint ((new_x, new_y), STYLE_END)
                        appends.append ((p, inside[0][0]-done_ins))
                    for i in inside:
                        dels.append (i[1])
            inserts = 0
            for x in appends:
                self.points.insert (x[1]+inserts, x[0])
                self.ins_points.append ((0, x[1]+inserts, x[0]))
                inserts+=1
            for x in dels:
                self.ins_points.append ((1, self.points.index (x), x))
                self.points.remove (x)

        self.emit ("update_links")
        self.emit ("update_view")
        return True

    def move_by (self, x, y):
        self.ul = (self.ul[0]+x, self.ul[1]+y)
        self.min_x += x
        self.min_y += y
        self.max_x += x
        self.max_y += y
        map(lambda p : p.move_by(x,y), self.points)
        self.recalc_edges ()
        self.emit ("update_links")

    def update_save (self):
        next = self.element.firstChild
        while next:
            m = next.nextSibling
            if next.nodeName == "point":
                self.element.removeChild (next)
                next.unlink ()
            next = m
        text = self.extended_buffer.get_text ()
        if text:
            self.extended_buffer.update_save()
        else:
            try:
                self.element.removeChild(self.extended_buffer.element)
            except xml.dom.NotFoundErr:
                pass
        self.element.setAttribute ("ul-coords", str(self.ul))
        self.element.setAttribute ("lr-coords", str(self.lr))
        self.element.setAttribute ("identity", str(self.identity))
        self.element.setAttribute ("background-color", self.background_color.to_string())
        self.element.setAttribute ("foreground-color", self.foreground_color.to_string())
        self.element.setAttribute ("min_x", str(self.min_x))
        self.element.setAttribute ("min_y", str(self.min_y))
        self.element.setAttribute ("max_x", str(self.max_x))
        self.element.setAttribute ("max_y", str(self.max_y))

        if self.am_selected:
            self.element.setAttribute ("current_root", "true")
        else:
            try:
                self.element.removeAttribute ("current_root")
            except xml.dom.NotFoundErr:
                pass
        if self.am_primary:
            self.element.setAttribute ("primary_root", "true");
        else:
            try:
                self.element.removeAttribute ("primary_root")
            except xml.dom.NotFoundErr:
                pass
        doc = self.element.ownerDocument
        for p in self.points:
            elem = doc.createElement ("point")
            self.element.appendChild (elem)
            elem.setAttribute ("coords", str((p.x,p.y)))
            elem.setAttribute ("type", str(p.style))
            elem.setAttribute ("color", p.color.to_string())
        return

    def load (self, node):
        tmp = node.getAttribute ("ul-coords")
        self.ul = utils.parse_coords (tmp)
        tmp = node.getAttribute ("lr-coords")
        self.lr = utils.parse_coords (tmp)
        self.identity = int (node.getAttribute ("identity"))
        try:
            tmp = node.getAttribute ("background-color")
            self.background_color = Gdk.color_parse(tmp)
            tmp = node.getAttribute ("foreground-color")
            self.foreground_color = Gdk.color_parse(tmp)
        except ValueError:
            pass
        self.min_x = float(node.getAttribute ("min_x"))
        self.min_y = float(node.getAttribute ("min_y"))
        self.max_x = float(node.getAttribute ("max_x"))
        self.max_y = float(node.getAttribute ("max_y"))

        self.width = self.lr[0] - self.ul[0]
        self.height = self.lr[1] - self.ul[1]

        self.am_selected = node.hasAttribute ("current_root")
        self.am_primary = node.hasAttribute ("primary_root")

        for n in node.childNodes:
            if n.nodeName == "Extended":
                self.extended_buffer.load(n)
            elif n.nodeName == "point":
                style = int (n.getAttribute ("type"))
                tmp = n.getAttribute ("coords")
                c = utils.parse_coords (tmp)
                col = None
                try:
                    tmp = n.getAttribute ("color")
                    col = Gdk.color_parse (tmp)
                except ValueError:
                    pass
                self.points.append (self.DrawingPoint (c, style, col))
            else:
                print("Unknown node type: "+str(n.nodeName))

    def export (self, context, move_x, move_y):
        utils.export_thought_outline (context, self.ul, self.lr, self.background_color, self.am_selected, self.am_primary, utils.STYLE_NORMAL,
                                                                  (move_x, move_y))
        cwidth = context.get_line_width ()
        context.set_line_width (1)
        if len (self.points) > 0:
            for p in self.points:
                if p.style == STYLE_BEGIN:
                    context.move_to (p.x+move_x, p.y+move_y)
                else:
                    context.line_to (p.x+move_x,p.y+move_y)

        context.set_line_width (cwidth)
        r,g,b = utils.gtk_to_cairo_color(self.foreground_color)
        context.set_source_rgb (r, g, b)
        context.stroke ()
        return

    def includes (self, coords, mode):
        if not self.ul or not self.lr or not coords:
            return False

        if self.want_move and mode == MODE_DRAW:
            self.emit ("change_mouse_cursor", Gdk.CursorType.PENCIL)
            return True

        inside = (coords[0] < self.lr[0] + self.sensitive) and \
                         (coords[0] > self.ul[0] - self.sensitive) and \
                     (coords[1] < self.lr[1] + self.sensitive) and \
                     (coords[1] > self.ul[1] - self.sensitive)

        self.resizing = self.RESIZE_NONE
        self.motion_coords = coords

        if inside and (mode != MODE_EDITING or self.button_down):
            if mode == MODE_DRAW:
                self.emit ("change_mouse_cursor", Gdk.CursorType.PENCIL)
            else:
                self.emit ("change_mouse_cursor", Gdk.CursorType.LEFT_PTR)
            return inside

        if inside:
            # 2 cases: 1. The click was within the main area
            #                  2. The click was near the border
            # In the first case, we handle as normal
            # In the second case, we want to intercept all the fun thats
            # going to happen so we can resize the thought
            if abs (coords[0] - self.ul[0]) < self.sensitive:
                # its near the top edge somewhere
                if abs (coords[1] - self.ul[1]) < self.sensitive:
                # Its in the ul corner
                    self.resizing = self.RESIZE_UL
                    self.emit ("change_mouse_cursor", Gdk.CursorType.TOP_LEFT_CORNER)
                elif abs (coords[1] - self.lr[1]) < self.sensitive:
                # Its in the ll corner
                    self.resizing = self.RESIZE_LL
                    self.emit ("change_mouse_cursor", Gdk.CursorType.BOTTOM_LEFT_CORNER)
                elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
                #anywhere else along the left edge
                    self.resizing = self.RESIZE_LEFT
                    self.emit ("change_mouse_cursor", Gdk.CursorType.LEFT_SIDE)
            elif abs (coords[0] - self.lr[0]) < self.sensitive:
                if abs (coords[1] - self.ul[1]) < self.sensitive:
                # Its in the UR corner
                    self.resizing = self.RESIZE_UR
                    self.emit ("change_mouse_cursor", Gdk.CursorType.TOP_RIGHT_CORNER)
                elif abs (coords[1] - self.lr[1]) < self.sensitive:
                # Its in the lr corner
                    self.resizing = self.RESIZE_LR
                    self.emit ("change_mouse_cursor", Gdk.CursorType.BOTTOM_RIGHT_CORNER)
                elif coords[1] < self.lr[1] and coords[1] > self.ul[1]:
                #anywhere else along the right edge
                    self.resizing = self.RESIZE_RIGHT
                    self.emit ("change_mouse_cursor", Gdk.CursorType.RIGHT_SIDE)
            elif abs (coords[1] - self.ul[1]) < self.sensitive and \
                     (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
                # Along the top edge somewhere
                self.resizing = self.RESIZE_TOP
                self.emit ("change_mouse_cursor", Gdk.CursorType.TOP_SIDE)
            elif abs (coords[1] - self.lr[1]) < self.sensitive and \
                     (coords[0] < self.lr[0] and coords[0] > self.ul[0]):
                # Along the bottom edge somewhere
                self.resizing = self.RESIZE_BOTTOM
                self.emit ("change_mouse_cursor", Gdk.CursorType.BOTTOM_SIDE)
            else:
                self.emit ("change_mouse_cursor", Gdk.CursorType.LEFT_PTR)
        self.want_move = (self.resizing != self.RESIZE_NONE)
        return inside

    def get_popup_menu_items(self):
        return []
