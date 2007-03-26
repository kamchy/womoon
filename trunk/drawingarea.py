#!/usr/bin/python
# -*- coding: UTF-8 -*-

#
#    This file is part of Womoon.
#    Copyright: Kamila Chyla, 2006
#
#    Womoon is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Womoon is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Womoon; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk, gobject
import cairo
import sys
import math
from datetime import date, timedelta
from random import choice, randint
from chartmodel import Day, ChartModel, Observation
from observabledict import ObservableNamedDict

def printr(txt, r):
  print "%s: [%s, %s, %s, %s]" % (txt, r.x, r.y, r.width, r.height)

class ChartController(gtk.EventBox):
  SWITH_SEX = 0
  SWITH_OBS = 1

  def __init__(self, model, view):
    gtk.EventBox.__init__(self)
    self.model = model
    self.view = view
    self.drag_mode = False
    self.drag_column_idx = -1
    self.data_switch_mode = None
    self.connect_signals()
    self.add(view)
    self.cb_screen_changed(self, self.get_screen())                  
    self.set_flags(gtk.CAN_FOCUS)
    self.on_column_doubleclicked_callbacks = []

  def connect_signals(self):
    self.add_events(gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS | gtk.gdk.BUTTON_RELEASE | gtk.gdk.KEY_PRESS_MASK | gtk.gdk.KEY_RELEASE_MASK)
    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("screen-changed", self.cb_screen_changed)
    self.connect("key-press-event", self.cb_key_pressed)    

  def cb_key_pressed(self, widget, event):
    if event.keyval == gtk.keysyms.Escape:
      self.drag_mode = False
      self.view.cursor = None
      self.data_switch_mode = None
      self.drag_column_idx = -1
      self.window.invalidate_rect(self.view.chart_context_painter.mainrect, True)
      self.window.process_updates(True)

  def cb_screen_changed(self, widget, screen):
    self.hand_cursor = gtk.gdk.Cursor(self.get_display(), gtk.gdk.HAND1)

  def cb_motion_notify(self, _, event):
    loc = event.get_coords()
    day_idx = self.get_day_idx(loc)
    if not self.drag_mode:
#      update cursor
      if self.is_in_circle(loc, day_idx):
          self.window.set_cursor(self.hand_cursor)
      else:
          self.window.set_cursor(None)      
    elif self.inside_grid(loc):
      self.view.cursor = (self.drag_column_idx, loc[1])

  def inside_grid(self, loc):
    cp = self.view.chart_context_painter
    return loc[1] > cp.grid.y and loc[1] < cp.grid.y + cp.grid.height

  def get_calculated_temp(self, column, ypos):
    cp = self.view.chart_context_painter
    new_temp =  cp.point_to_temp(column, ypos)
    return round(new_temp / 0.05) * 0.05                                              

  def cb_button_press(self, widget, event):
    coord = event.get_coords()
    self.drag_column_idx = self.get_day_idx(coord)
    self.drag_mode = self.is_in_circle(coord, self.drag_column_idx)
    if self.drag_mode:                                                                       
      self.view.cursor = (self.drag_column_idx, coord[1]) 
    else:
      self.data_switch_mode = self.get_switching_mode(coord, self.drag_column_idx)
      if self.data_switch_mode is None and event.type == gtk.gdk._2BUTTON_PRESS and self.drag_column_idx != -1:
        self.fire_column_doubleclicked(self.drag_column_idx)

  def fire_column_doubleclicked(self, column_idx):
    for cb in self.on_column_doubleclicked_callbacks:
      cb(column_idx)

  def add_on_column_doubleclicked(self, cb):
    self.on_column_doubleclicked_callbacks.append(cb)

  def remove_on_column_doubleclicked(self, cb):
    if cb in self.on_column_doubleclicked_callbacks:
      self.on_column_doubleclicked_callbacks.remove(cb)
      

  def cb_button_release(self, widget, event):
    if self.drag_mode:
      new_temp = self.get_calculated_temp(*self.view.cursor)
      self.view.cursor = None
      self.model.set_temp(self.drag_column_idx, new_temp)
    elif self.data_switch_mode is not None:
      self.switch_next(self.data_switch_mode, self.drag_column_idx, event)
      self.data_switch_mode = None
    self.drag_mode = False
    self.drag_column_idx = -1

  def __is_in_radius(self, p, day_idx, radius):
    if day_idx < 0:
      return False
    c = self.view.chart_context_painter.circles[day_idx]
    if (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 < radius ** 2 :
      return True
    return False

  def is_in_circle(self, p, day_idx):
    return self.__is_in_radius(p, day_idx, self.view.chart_context_painter.point_radius)

  def intersects(self, a, b):
    c = a.intersect(b)
    return not (c.x == 0 and c.y == 0 and c.width == 0 and  c.height == 0)


  def get_switching_mode(self, p, day_idx):
    if day_idx < 0:
      return None
#    print "Clicked: [%s, %s]" % tuple(p)
    test_rect = gtk.gdk.Rectangle(int(p[0]), int(p[1]), 1, 1)
    base_rect = self.view.chart_context_painter.observation_grid
    if self.intersects(base_rect, test_rect):
      b = base_rect.copy()
      b.height = b.height / 2
      if self.intersects(b, test_rect):
        return ChartController.SWITH_SEX
      else:
        return ChartController.SWITH_OBS      
    else:
      return None

  def switch_next(self, switch_mode, day_idx, evt):
    if switch_mode == ChartController.SWITH_SEX:
      self.model.set_sex(day_idx, not self.model.get_sex(day_idx))
    elif switch_mode == ChartController.SWITH_OBS:
      delta = 0
      if evt.button == 1:
        delta = 1
      elif evt.button == 3:
        delta = -1
      self.model.set_obs(day_idx, (self.model.get_obs(day_idx) + delta) % len(Observation.VALUES))

  def get_day_idx(self, loc):
    """
    Returns index of the day column where loc point belongs or -1 if loc
    doesn't denote a point on day column
    """
    cp = self.view.chart_context_painter
    for i, c in enumerate(cp.columns):      
      if loc[0] >= c[0] and loc[0] < c[0] + c[1]:
        return i
    return -1

class ChartViewArea(gtk.DrawingArea):
  def __init__(self, model):
    gtk.DrawingArea.__init__(self)
    self.model = model
    self.cb_idle_redraw_id = None
    self.model.add_on_change_callback(self.cb_idle_redraw)
    self.chart_context_painter = ChartContextPainter(model)
    self.chart_context_painter.colors.add_on_change_callback(self.cb_update_colors)
    self.connect_signals()

  def connect_signals(self):    
    self.connect("expose_event", self.expose)
   
  def expose(self, widget, event):
    self.ctx = widget.window.cairo_create()
#    set a clip region for the expose event
    self.ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
    self.ctx.clip()        
    self.draw(self.ctx)
    return False

  def cb_idle_redraw(self, day_idx):
      if self.cb_idle_redraw_id is None:
        self.cb_idle_redraw_id = gobject.idle_add(self.update, day_idx)

  def cb_update_colors(self, old, new):
    #print "Drawing area updates color: %s -> %s" % (old, new) 
    rec = self.chart_context_painter.rect
    self.__update(rec)

  def update(self, col_idx):
    """
    Updates the self.chart_context_painter.rect
    """
    self.cb_idle_redraw_id = None
    #if col_idx < 0 or col_idx > self.model.nx:
    #  return
    # TODO calculate three columns that need to be repainted
    #rect = self.diag
    rec = self.chart_context_painter.rect
    self.__update(rec)

  def __update(self, rec):
    self.window.invalidate_rect(rec, False)
    self.window.process_updates(False)

  def set_cursor(self, cur):
    self.chart_context_painter.cursor = cur
    if cur is not None:
      self.cb_idle_redraw(cur[0])

  def get_cursor(self):
    return self.chart_context_painter.cursor

  cursor = property(get_cursor, set_cursor)

  def set_color(self, color_name, value):
    c = self.chart_context_painter.colors
    if c.has_key(color_name):
      c[color_name] = value
    self.__update(self.chart_context_painter.mainrect)

  def get_color(self, color_name):
    c = self.chart_context_painter.colors
    if c.has_key(color_name):
      return c[color_name]

  def draw(self, ctx):
    rect = self.get_allocation()
    self.chart_context_painter.draw(ctx, rect)

class ChartContextPainter:
  HORIZ_PARTS = 10 #logical horizontal lines
  MARGINS_IN_HORIZ = 8 #how many margins is in horizontal line
  VERT_PARTS = 10 #logical vertical lines
   
  def __init__(self, model):
    self.model = model
    self.circles = []
    self.columns = [] #pairs (column_xpos, column_width)
    self.rows = [] #pairs (row_ypos, row_height)
    self.dy = 0
    self.point_radius = 4
    self.graph_line_width = 3
    self.date_header_font_size = 20
    self.date_number_font_size = 13
    self.is_top_bottom_margin = False
    self.grid = None
    self.cursor = None
    self.helper = Drawer()
    colors = {
      "curr_day":("Kolumna oznaczająca aktywny dzień", (0.62, 0.13, 0.13)),
      "cursor_circ":("Kolor przeciąganego punktu", (1, 0, 0)),
      "cursor_line":("Kolor przeciąganej łamanej", (0.09, 0.62, 0.59)), 
      "day_today":("Kolumna oznaczająca dzień dzisiejszy", (0.1, 0.23, 0.45)),
      "empty_line":("Brak - linia", (0, 0, 0)),
      "frame":("Ramka", (0, 0, 0)),
      "graph_circ":("Kolor punktu w wierzchołkach łamanej", (0.19, 0, 0.47)), 
      "graph_line":("Kolor łamanej", (0, 0.3, 0.9)), 
      "grid_bg":("Kolor tła siatki", (1, 0.94, 0.94)), 
      "grid_fg":("Kolor siatki", (0, 0, 0)), 
      "lit_noo":("Brak owulacji - mało", (0.65, 0.32, 0.13)),
      "lit_noo_fill":("Brak owulacji - mało (wypełnienie)", (1.0, 0.9, 0.73)),
      "lit_o":("Owulacja - mało", (0.11, 0.21, 0.29)),
      "lit_o_fill":("Owulacja - mało (wypełnienie)", (1.0, 0.63, 0.63)),
      "lot_noo":("Brak owulacji - obficie", (0.3, 0.01, 0)),
      "lot_noo_fill":("Brak owulacji - obficie (wypełnienie)", (0, 0, 0)),
      "lot_o":("Owulacja - obficie", (1, 0.64, 0.46)),
      "lot_o_fill":("Owulacja - obficie (wypełnienie)", (0.72, 0.31, 0.31)),
      "main":("Główna ramka", (0, 0, 0)), 
      "mens":("Poziom menstruacji", (0.4, 0.6, 0.8)),
      "month_bg":("Tło pola z numerem miesiąca i rokiem", (1.0, 0.92, 0.89)), 
      "month_fg":("Tekst pola z numerem miesiąca i rokiem", (0.33, 0.36, 0.29)), 
      "no_sun_bg":("Tekst pola z numerem dnia (niedzieli)", (1, 0.98, 0.83)), 
      "no_sun_fg":("Tekst pola z numerem dnia (powszedniego)", (0.28, 0.25, 0.12)), 
      "ovula_peak_cross":("Szczyt objawu", (0.5, 0.2, 0.6)), 
      "prolif_day":("Kolumny dni płodnych", (0.9, 0.74, 0.95)),
      "sex-arrow-border":("Strzałka - brzeg", (0.2, 0, 0.7)),
      "sex-arrow-fill":("Strzałka - wypełnienie", (0.2, 0.1, 0.6)),
      "sun_bg":("Tło pola z numerem dnia (niedzieli)", (1, 0.86, 0.28)), 
      "sun_fg":("Tekst pola z numerem dnia (niedzieli)" , (0.33, 0.36, 0.29)), 
      "yscale_bg":("Tło skali temperatur", (0.95, 0.95, 0.9)), 
    }
    self.colors = ObservableNamedDict(colors)
    self.observation_painter = ObservationPainter(self.helper, self.colors)

  def draw(self, ctx, rect):
    """
    Draws data from given model to given context with clip rectangle
    defined by rect
    """
    self.rect = rect
    margins = ChartContextPainter.HORIZ_PARTS * ChartContextPainter.MARGINS_IN_HORIZ # number of margins
    margin_size = rect.height / margins
    horiz_part_size = (rect.height - 2 * margin_size) / ChartContextPainter.HORIZ_PARTS
    
    vert_part_size = (rect.width - 2 * margin_size) / ChartContextPainter.VERT_PARTS
    self.vert_part_size = vert_part_size

    grid_width = vert_part_size * (ChartContextPainter.VERT_PARTS - 1) # one vert parts goes to oy descriptions
    grid_height = horiz_part_size * (ChartContextPainter.HORIZ_PARTS - 2) # one for month and days part on top, one for observ. results on bottom
    self.dx = grid_width / self.model.nx
    self.dy = grid_height / self.model.ny
    
    self.mainrect = gtk.gdk.Rectangle(
        rect.x + margin_size,
        rect.y + margin_size,
        grid_width + vert_part_size,
        grid_height + 2 * horiz_part_size)
    self.helper.draw_rect(ctx, self.mainrect, self.colors["main"])

    self.grid = gtk.gdk.Rectangle(
        self.mainrect.x + vert_part_size,
        self.mainrect.y + horiz_part_size,
        grid_width,
        grid_height)

    self.observation_grid = gtk.gdk.Rectangle(
        self.grid.x,
        self.grid.y + self.grid.height,
        self.grid.width, horiz_part_size)

    self.grid_ext = self.grid.copy()
    self.grid_ext.x = self.grid_ext.x - vert_part_size
    self.grid_ext.width = self.grid_ext.width + vert_part_size
    self.helper.fill_rect(ctx, self.grid_ext, self.colors["yscale_bg"])
    self.helper.draw_rect(ctx, self.grid_ext, self.colors["main"])

    self.calculate_sizes()
    # draw grid lines
    self.draw_grid(ctx, self.grid) #requires column data
    # draw ranges defined in model
    self.draw_day_ranges(ctx)
    # draw description on OY axis
    self.ydescrect = gtk.gdk.Rectangle(
       self.mainrect.x, self.grid.y, vert_part_size, self.grid.height)
    self.draw_ydesc(ctx, self.ydescrect)

    # draw rectandle with dates
    self.daterect = gtk.gdk.Rectangle(
        self.grid.x, self.mainrect.y, self.grid.width, horiz_part_size)
    self.draw_date(ctx, self.daterect) #requires grid painted; generates colimn data
    
    self.draw_graph(ctx, self.grid)

    self.draw_observations(ctx, self.observation_grid)
    if self.cursor is not None:
      self.draw_cursor(ctx, self.grid)

  def draw_day_ranges(self, ctx):
    d, idx = self.model.get_current_day()
    if d is not None:
      self.__draw_range(ctx, idx, idx, self.colors["curr_day"])
    today = self.model.get_today()
    d, idx = today
    if d is not None:
      self.__draw_range(ctx, idx, idx, self.colors["day_today"])
    prolif_range = self.model.get_prolific_range()
    if prolif_range is not None:
      idx_start, idx_stop = prolif_range
      self.__draw_range(ctx, idx_start, idx_stop, self.colors["prolif_day"])


  def __draw_range(self, ctx, begin_idx, end_idx, color):
      col_x, col_width = self.columns[begin_idx]
      col_x_end, col_width_end =  self.columns[end_idx]
      r = gtk.gdk.Rectangle(col_x, self.grid.y, col_x_end + col_width_end - col_x, self.grid.height)
      self.helper.fill_rect_alpha(ctx, r, color, 0.3)

  def draw_observations(self, ctx, rect):
    ctx.save()
    for i, d in enumerate(self.model.get_days()):
      col_x, col_width = self.columns[i]
      r = gtk.gdk.Rectangle(col_x, rect.y + rect.height / 2, col_width, rect.height / 2)
#      self.observation_painter.paint(ctx, r, d.obsv)
      self.observation_painter.paint(ctx, r.copy(), d.obsv)
      if d.is_sex:
        r.y = rect.y        
        self.observation_painter.paint_sex(ctx, r)
    ctx.restore()

  def draw_cursor(self, ctx, rect):

    def get_circle(idx):
      if idx < 0 or idx > self.model.nx - 1:
        return None
      return self.circles[idx]
    cx = self.cursor[0]                              
    cp = get_circle(cx)[0], self.cursor[1]
    pp = get_circle(cx - 1)
    np = get_circle(cx + 1)

    circ_col = self.colors["cursor_circ"]
    line_col = self.colors["cursor_line"]
    days = self.model.get_days()
    ctx.save()
    ctx.set_line_width(self.graph_line_width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_dash((4, 4), 0)
    ctx.set_source_rgb(*line_col)
    if pp is not None:
      ctx.move_to(*pp)
      ctx.line_to(*cp)
    else:
      ctx.move_to(*cp)
    if np is not None:
      ctx.line_to(*np)
    ctx.stroke()

    ctx.set_source_rgb(*circ_col)
    self.__draw_circle(ctx, *cp)
    ctx.restore()

  def __draw_circle(self, ctx, x, y):
    ctx.arc(x, y, self.point_radius, 0, 2 * math.pi)
    ctx.fill()


  def draw_graph(self, ctx, rect):
    circ_col = self.colors["graph_circ"]
    line_col = self.colors["graph_line"]
    days = self.model.get_days()
    ctx.save()
    ctx.set_line_width(self.graph_line_width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*self.circles[0])
    ctx.set_source_rgb(*line_col)
    for i, d in enumerate(days[1:]):
      x, y = self.circles[i+1]
      ctx.line_to(x, y)
    ctx.stroke()

    ctx.set_source_rgb(*circ_col)
    for i, d in enumerate(days):
      x, y = self.circles[i]
      ctx.move_to(x, y)
      self.__draw_circle(ctx, x, y)
    ctx.restore()

  def draw_ydesc(self, ctx, rect):
    fg = self.colors["grid_fg"]
    bg = self.colors["grid_bg"]                               
    ctx.save()
    desc_arr =  self.model.get_ydesc()
    desc_arr.reverse()
    for i, desc in enumerate(desc_arr[:-1]):
      ri = self.rows[i]
      cellrect = gtk.gdk.Rectangle(rect.x, ri[0] + ri[1]/2, self.vert_part_size, ri[1]) 
      self.helper.draw_text(ctx, cellrect, fg, self.date_number_font_size, desc)
    ctx.restore()

  def calculate_sizes(self):
    """
    """
    rect = self.grid
    days = self.model.get_days()
    self.columns = []
    self.circles = []
    self.rows = []

    day_col = [rect.x, self.dx]
    ndays = len(days)
    for i in xrange(ndays):
      day_col[1] = (rect.x + rect.width - day_col[0]) / (ndays -  i)
      self.columns.append(tuple(day_col))
      day_col[0] = day_col[0] + day_col[1]

    row = [rect.y, self.dy]
    for i in xrange(self.model.ny):
      row[1] = (rect.y + rect.height -row[0]) / (self.model.ny - i)
      self.rows.append(tuple(row))
      row[0] = row[0] + row[1]

    for i, d in enumerate(days):
      col = self.columns[i]
      circle_loc = [col[0] + col[1]/2, self.temp_to_point(d.temp)]
      self.circles.append(tuple(circle_loc))
                                            
  def temp_to_point(self, temp):
    range_width = self.model.range[1] - self.model.range[0] 
    part = (self.model.range[1] - temp * self.model.factor) / range_width
    point = self.grid.y + self.grid.height * part
    return point

  def point_to_temp(self, column, ypos):
    part = math.fabs((self.grid.y - ypos) / self.grid.height)
    temp = self.model.range[1] - (self.model.range[1] - self.model.range[0]) * part
    return temp/self.model.factor

  def draw_date(self, ctx, rect):
    ctx.save()

    #draw month name
    month_rect = gtk.gdk.Rectangle(rect.x, rect.y, rect.width, rect.height / 2)
    self._draw_cell(ctx, month_rect, "month_fg", "month_bg", "month_fg", self.date_header_font_size, self.model.get_month_str())

    # draw all days
    days = self.model.get_days()
    day_rect = gtk.gdk.Rectangle(0, rect.y + month_rect.height, 0, month_rect.height)
    for i, d in enumerate(days):
      day_rect.x, day_rect.width = self.columns[i]
      self._draw_cell(ctx, day_rect, "no_sun_fg", "no_sun_bg", "no_sun_fg", self.date_number_font_size, str(d.num))

    # day_rect only changes x and width; redraw sundays
    for i, d in enumerate(days):
      if self.model.is_sunday(i):
        day_rect.x, day_rect.width = self.columns[i]
        self._draw_cell(ctx, day_rect, "sun_fg", "sun_bg", "sun_fg", self.date_number_font_size, str(d.num), 2)
    ctx.restore()

  def _draw_cell(self, ctx, rect, fg_colname, bg_colname, txt_colname, txt_size, txt, line_size=1):
    fg = self.colors[fg_colname]
    bg = self.colors[bg_colname]
    txc = self.colors[txt_colname]
    ctx.save()
    self.helper.fill_rect(ctx, rect, bg)
    self.helper.draw_rect(ctx, rect, fg, line_size)
    self.helper.draw_text(ctx, rect, txc, txt_size, txt)
    ctx.restore()


  def draw_grid(self, ctx, rect):
    model = self.model
    fg = self.colors["grid_fg"]
    bg = self.colors["grid_bg"]
    # white rect
    self.helper.fill_rect(ctx, rect, bg)
    self.helper.draw_rect(ctx, rect, fg)
    ctx.set_line_width(0.25)
    #vertical lines
    for (y, hi) in self.rows:
      ctx.move_to(rect.x, y)
      ctx.line_to(rect.x + rect.width - 1,  y)
      ctx.stroke()
    #horizontal lines    
    for (x, wi) in self.columns:
      ctx.move_to(x, rect.y)
      ctx.line_to(x, rect.y + rect.height - 1)
      ctx.stroke()

class Drawer:

  def draw_text(self, ctx, rect, color, size, txt):
    ctx.set_source_rgb(*color)
    ctx.set_font_size(size)
    txt_ext = ctx.text_extents(txt)
    center = self.get_center(rect, txt_ext)
    ctx.move_to(*center)
    ctx.show_text(txt)

  def get_center(self, rect, t_ext):
    x = rect.x + rect.width / 2 - t_ext[2] / 2
    y = rect.y + rect.height / 2 + t_ext[3] / 2
    return (x, y)

  def fill_rect(self, ctx, rect, color):
    ctx.save()
    ctx.rectangle(rect.x, rect.y, rect.width, rect.height)
    ctx.set_source_rgb(*color)
    ctx.fill()
    ctx.restore()

  def fill_rect_alpha(self, ctx, rect, color, alpha):
    ctx.save()
    ctx.rectangle(rect.x, rect.y, rect.width, rect.height)
    color = list(color)
    color.append(alpha)
    ctx.set_source_rgba(*color)
    ctx.fill()
    ctx.restore()

  def draw_rect(self, ctx, rect, color, line_width=2):
    ctx.save()
    ctx.rectangle(rect.x, rect.y, rect.width, rect.height)
    ctx.set_source_rgb(*color)
    ctx.set_line_width(line_width)
    ctx.stroke()
    ctx.restore()

class ObservationPainter:
  def __init__(self, helper, colors):
    self.helper = helper
    self.colors = colors
    self.paint_method = { 
      Observation.EMPTY: self.empty, 
      Observation.MENS_1: self.wrap(self.mens, [0.2]),
      Observation.MENS_2: self.wrap(self.mens, [0.45]),
      Observation.MENS_3: self.wrap(self.mens, [0.65]),
      Observation.MENS_4: self.wrap(self.mens, [0.8]),
      Observation.LITTLE_NOOVUL: self.wrap(self.no_mens, [True, True, "lit_noo", "lit_noo_fill"]),
      Observation.LOT_NOOVUL: self.wrap(self.no_mens, [False, True, "lot_noo", "lot_noo_fill"]),
      Observation.LITTLE_OVUL: self.wrap(self.no_mens, [True, False, "lit_o", "lit_o_fill"]),
      Observation.LOT_OVUL:  self.wrap(self.no_mens, [False, False, "lot_o", "lot_o_fill"]),
      Observation.PEAK: self.peak,
    }

  def wrap(self, fun, new_args):
    """
    This wrapper returns fun function with last argument value
    set to arg
    """
    def fun_arg(*args, **dic):
      args = list(args)
      args.extend(new_args)
      fun(*args, **dic)
    return fun_arg

  def paint(self, ctx, rect, num):
    if rect.width <= 0 or rect.height <= 0:
      return
    ctx.save()
    if not self.paint_method.has_key(num):
      raise Exception("No such Observation constant as %s." % num)
    self.paint_method[num](ctx, rect)
    ctx.restore()

  def paint_sex(self, ctx, rect):
    if rect.width <= 0 or rect.height <= 0:
      return
    ctx.save()
    ctx.set_source_rgb(*self.colors["sex-arrow-border"])
    ctx.translate(rect.x, rect.y)
    ctx.scale(rect.width/6.0, rect.height/6.0)
    ctx.move_to(2.5, 2.0)
    ctx.set_line_width(0.2)
    ctx.line_to(3.5, 2.0)
    ctx.line_to(3.5, 4.0)
    ctx.line_to(4.0, 4.0)
    ctx.line_to(3.0, 5.0)
    ctx.line_to(2.0, 4.0)
    ctx.line_to(2.5, 4.0)
    ctx.close_path()
    ctx.stroke_preserve()
    ctx.set_source_rgb(*self.colors["sex-arrow-fill"])
    ctx.fill()
    ctx.restore()

  def paint_frame(self, ctx, rect):
    """
    Strokes a rectangle given by rect with a "frame" color
    and a line width = 2
    """
    ctx.set_source_rgb(*self.colors["frame"])
    ctx.set_line_width(2)
    rdata=(rect.x, rect.y, rect.width, rect.height)
    ctx.rectangle(*rdata)
   # print "paint_frame: CTX  = %s" % id(ctx)
    ctx.stroke()

  def fill_bottom(self, ctx, rect, part):
    """
    Fills rectangle given by rect in a bottom part
    given by part parameter (0.4 means that bottom quarter
    of the rect is filled, 1 means that whole rect is filled)
    with "mens" color
    """
    r = rect.copy()
    ctx.set_source_rgb(*self.colors["mens"])
    fill_height =  r.height * part
    r.y = r.y + (r.height - fill_height)
    r.height = fill_height
    rdata=(r.x, r.y, r.width, r.height)
    ctx.rectangle(*rdata)
    ctx.fill()

  def draw_circle(self, ctx, rect, is_small, is_filled, color_border, color_fill):    
    """
    Strokes small (when is_small == True) or normal circle inside given rect
    with color_border color. If is_filled == True, then the circle is also
    filled with color_fill color.
    """
    r = min(rect.width, rect.height) / 2
    if (r == 0):
      return
    ctx.save()
    ctx.set_line_width(0.5)
    ctx.set_source_rgb(*color_border)
    ctx.translate(rect.x + rect.width / 2, rect.y + rect.height / 2)
    ctx.scale(1.0 / 2*r, 1.0 / 2*r);
    if is_small:
      r_scaled = 0.8
    else:
      r_scaled = 1
    ctx.arc(0., 0, r_scaled, 0.0, 2 * math.pi)
    if is_filled:
      ctx.stroke_preserve()
      ctx.set_source_rgb(*color_fill)
      ctx.fill()
    else:
      #print "draw_circle: CTX = %s" % id(ctx)
      ctx.stroke()
    ctx.restore()

  def empty(self, ctx, rect):
    """
    Strokes horizontal line in the center of given rect
    with "empty_line" color.
    """
    self.paint_frame(ctx, rect)
    ctx.move_to(rect.x + 0.2 * rect.width, rect.y + rect.height / 2)
    ctx.set_source_rgb(*self.colors["empty_line"])
    ctx.line_to(rect.x + 0.8 * rect.width, rect.y + rect.height / 2)
    ctx.stroke()

  def peak(self, ctx, rect):
    self.paint_frame(ctx, rect)
    ctx.save()
    color = self.colors["ovula_peak_cross"]
    ctx.set_source_rgb(*color)
    ctx.translate(rect.x, rect.y)
    ctx.scale(rect.width/13.0, rect.height/13.0)
    ctx.move_to(3, 3)
    ctx.set_line_width(2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.line_to(10, 10)
    ctx.move_to(10, 3)
    ctx.line_to(3, 10)
    ctx.move_to(7, 7)
    ctx.stroke()
    ctx.restore()

  def mens(self, ctx, rect, part):
    """
    Helper for drawing frame and filling given part on the
    bottom of the rect.
    """
    self.fill_bottom(ctx, rect, part)
    self.paint_frame(ctx, rect)

  def no_mens(self, ctx, rect, is_small, is_filled, col_border_name, col_fill_name):
    """
    Helper for drawing a frame and drawing circle.
    See  draw_circle for details.
    """
    self.paint_frame(ctx, rect)
    col_border = self.colors[col_border_name]
    col_fill = self.colors[col_fill_name]
    self.draw_circle(ctx, rect, is_small, is_filled, col_border, col_fill)

class ChartViewPicture:
  EXT = "png"
  def __init__(self, model, width, height):
    self.width = width
    self.height = height
    self.painter = ChartContextPainter(model)
    self.surface = None

  def write(self, fname):
    if self.surface is None:
      self.create_surface(self.width, self.height, fname)
    r = gtk.gdk.Rectangle(0, 0, self.width, self.height)
    self.painter.draw(self.ctx, r)
    self.finish(fname)

  def finish(self, fname):
    self.surface.write_to_png(fname)

  def create_surface(self, width, height, fname):
    self.surface =  cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    self.ctx = cairo.Context(self.surface)

class ChartViewPdf(ChartViewPicture):

  A4_WIDTH = 597.6
  A4_HEIGHT = 842.4
  EXT = "pdf"

  def __init__(self, model, width, height):
    ChartViewPicture.__init__(self, model, width, height)

  def finish(self, fname):
    self.ctx.show_page()
    self.surface.flush()
    self.surface.finish()

  def create_surface(self, width, height, fname):
    sf = cairo.PDFSurface(fname, width, height)
    self.surface = sf                                             
    self.ctx = cairo.Context(self.surface)
    self.ctx.scale(width / ChartViewPdf.A4_HEIGHT, height / ChartViewPdf.A4_WIDTH)

class ChartViewSVG(ChartViewPdf):

  EXT = "svg"

  def __init__(self, model, width, height):
    ChartViewPdf.__init__(self, model, width, height)

  def create_surface(self, width, height, fname):
    self.surface =  cairo.SVGSurface(fname, width, height)
    self.ctx = cairo.Context(self.surface)

def create_controller_window(model, wi, hi):
  window = gtk.Window()
  window.set_title("Simple Cairo diagram")
  window.set_default_size(wi, hi)
  view = ChartViewArea(model)
  controller = ChartController(model, view)
  window.add(controller)
  window.connect("destroy", gtk.main_quit)
  window.show_all()
  return window

def show_view(model, display, wi, hi):
  w = create_controller_window(model, wi, hi)
  w.set_screen(display.get_default_screen())

def show_gui(model, wi, hi):
  show_view(model, gtk.gdk.Display(":1"), wi, hi)
  gtk.main()

def main_picture(model, wi, hi): 
  pic = ChartViewPicture(model, wi, hi)
  pic.write("out.png");

def main_pdf(model, wi, hi): 
  pic = ChartViewPdf(model, wi, hi)
  pic.write("out.pdf");

def main_svg(model, wi, hi):
  pic = ChartViewSVG(model, wi, hi)
  pic.write("out.svg");

def main(args):
  model = ChartModel()
  model.generate_days(date.today())
  if len(args) >= 2:
    for arg in args[1:]:
      try:
        display, width_str, height_str =  arg.split(",")
        show_view(model, gtk.gdk.Display(display), int(width_str), int(height_str))
      except:
        print "Usage: python %s display,width,height" % args[0]
        sys.exit(0)
  else:
    show_view(model, gtk.gdk.Display(":1"), 800, 600)
  gtk.main()

def multiopt(args):
  """
  Displays diagram in window (-w), to the png file (-p) or as pdf file (-f)
  depending on the argument option
  """
  subprograms = {"-w": show_gui, "-p": main_picture, "-f": main_pdf, "-s": main_svg}
  if len(args) > 1:
    opt = args[1]
    if not opt in ["-w", "-p", "-f", "-s"]:
      print "Usage: python %s [ -p | -w | -f | -s]" % args[0]
      sys.exit(0)
  else:
    opt = "-w"
  cm = ChartModel()
  cm.generate_days(date.today())
  subprograms[opt](cm, 800, 600)

if __name__ == "__main__":
  #main(sys.argv) # eg. python drawingarea.py :1,800,600
  multiopt(sys.argv) # eg. python drawingarea -w

