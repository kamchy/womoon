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

import gtk
import gobject
import copy
from exporter import Exporter 
from common import TopLevel
from datetime import date, timedelta
from drawingarea import ChartViewArea, ChartController
from chartmodel import ChartModel, Observation, Day
from chartproject import ChartProject
from observabledict import ObservableNamedDict


class CancellableDialog(TopLevel):
  """
  This base class introduces "cancel dialog on esc pressed"
  functionality. Overriding classes should implement
  cb_cancel(*params) callback.
  """
  
  def __init__(self, glade_fname):
    TopLevel.__init__(self, glade_fname)
    self.main.connect("key-press-event", self.__cb_key_press)

  def __cb_key_press(self, wgt, event):
    if event.keyval == gtk.keysyms.Escape:
      self.cb_cancel()

  def cb_cancel(self, *params):
    pass


class DayDialog(CancellableDialog):
  """
  Allows to edit observation data for a day
  which index is passed in show_day method
  """

  WINDOW_FILE = "day-dialog"

  def __init__(self):
    CancellableDialog.__init__(self, DayDialog.WINDOW_FILE)
    self.model = None
    self.init_window()
    self.connect_signals()

  def show_day(self, chart, idx):
    self.__set_model(chart)
    self.idx = idx
    self.day =  self.model.days[idx]
    self.ui.la_date.set_use_markup(True)
    self.ui.la_date.set_text(date_str(self.model, idx))
    self.ui.hs_temp.set_value(self.day.temp)
    self.ui.cb_obsv.set_active(self.day.obsv)
    self.ui.cb_sex.set_active(self.day.is_sex)
    text = self.day.notes 
    if text is None:
      text = ""
    self.ui.tv_notes.get_buffer().set_text(text)
    self.day.add_on_change_cb(self.model.on_day_change)
    self.day_orig = copy.copy(self.day)
    self.main.show_all()

  def __set_model(self, model):
    if self.model != model:
      self.model = model
      r = self.model.range
      self.ui.hs_temp.set_range(*(r[i] / self.model.factor for i in [0, 1]))

  def connect_signals(self):
    self.ui.bu_cancel.connect("clicked", self.cb_cancel)
    self.ui.bu_save.connect("clicked", self.cb_save)
    self.ui.hs_temp.connect("change-value", self.cb_change_scale)
    self.ui.cb_obsv.connect("changed", self.cb_change_obsv)
    self.ui.cb_sex.connect("toggled", self.cb_change_sex)
  
  def init_window(self):
    self.ui.cb_obsv.set_model(self.create_obsv_model())
    cell = gtk.CellRendererText()
    self.ui.cb_obsv.pack_start(cell, True)
    self.ui.cb_obsv.add_attribute(cell, 'text', 0)
    self.ui.tv_notes.set_buffer(gtk.TextBuffer())

  def create_obsv_model(self):
    list = gtk.ListStore(gobject.TYPE_STRING)
    for s in Observation.DESC:
      list.append([s])
    return list

  def cb_cancel(self, *params):
    self.model.days[self.idx] = self.day_orig
    self.close()

  def cb_save(self, wgt):
    mo = self.ui.tv_notes.get_buffer()
    self.day.notes = mo.get_text(mo.get_start_iter(), mo.get_end_iter())
    self.close()    

  def cb_change_scale(self, scale, scroll, val):
    self.day.temp = self.ui.hs_temp.get_value()

  def cb_change_obsv(self, cb):
    self.day.obsv = self.ui.cb_obsv.get_active()

  def cb_change_sex(self, cb):
    self.day.is_sex = self.ui.cb_sex.get_active()

  def close(self):
    self.day.remove_on_change_cb(self.model.on_day_change)
    self.main.destroy()

class AboutDialog(CancellableDialog):
  """
  Displays information about the program, author and licence text
  """
  WINDOW_FILE = "about"

  def __init__(self):
    CancellableDialog.__init__(self, AboutDialog.WINDOW_FILE)
    self.main.connect("response", self.cb_response)

  def cb_response(self, wn, response_id):
    self.main.destroy()

  def run(self):
    self.main.show_all()
    self.main.run()

class PropertiesDialog(CancellableDialog):
  """
  Allows to define, save and load colors for the diagram.
  """
  TITLE = "Właściwości programu"
  SAVE_COLOR_SCHEME = "Zapisz schemat kolorów"
  OPEN_COLOR_SCHEME = "Otwórz schemat kolorów"
  WINDOW_FILE = "properties"
  INVALID_COLORS = "Podany plik %s nie zawiera definicji kolorów w wymaganym formacie."
  MAX_COL = 65535

  def __init__(self):
    CancellableDialog.__init__(self, PropertiesDialog.WINDOW_FILE)
    self.bucolor_dict = {}
    self.viewport = None
    self.connect_signals()

  def connect_signals(self):
    self.ui.button_cancel.connect("clicked", self.on_cancel)
    self.ui.button_close.connect("clicked", self.on_close)
    self.ui.button_open.connect("clicked", self.on_open)
    self.ui.button_save_as.connect("clicked", self.on_save_as)

  def on_cancel(self, wnd):
    self.__restore_dict()
    self.on_close(wnd)

  def on_close(self, wnd):
    self.main.destroy()

  def on_open(self, wgt):    
    fname = Main.get_filename(PropertiesDialog.OPEN_COLOR_SCHEME, gtk.STOCK_OPEN, gtk.FILE_CHOOSER_ACTION_OPEN)
    if fname is None: return

    f = open(fname, "r")
    try:
      for line in f.xreadlines():
        name, r, g, b = line.split()
        col_tuple = tuple(float(s) for s in (r, g, b))
        gdk_color = self.tuple2col(col_tuple)
        if name in self.color_dict and self.color_dict[name] != col_tuple:
          self.color_dict[name] = col_tuple
          self.bucolor_dict[name].color = gdk_color
    except:
      Main.show_warning(self, Main.INVALID_FORMAT, PropertiesDialog.INVALID_COLORS % fname)
    f.close()

  
  def on_save_as(self, wgt):
    fname = Main.get_filename(PropertiesDialog.SAVE_COLOR_SCHEME, gtk.STOCK_SAVE, gtk.FILE_CHOOSER_ACTION_SAVE)
    f = open(fname, "w")
    for name, (desc, (r, g, b)) in self.color_dict.items():
      f.write("%s %s %s %s\n" % (name, r, g, b))
    f.close()


  def set_color_dict(self, obs):
    """
    Sets the colors dictionary that would be edited 
    in this property dialog
    """
    self.color_dict = obs
    self.color_dict_copy = ObservableNamedDict(obs)
    self.__fill_color_table(self.color_dict)

  def __fill_color_table(self, obs_dict):    
    if self.viewport is not None:
      self.ui.scroll_wnd.remove(self.viewport)
    color_table = gtk.VBox()
    color_table.set_border_width(12)
    sorted_items = sorted(obs_dict.items(), key = lambda el: el[1][0], reverse = True)
    for idx, (name, (desc, color_tuple)) in enumerate(sorted_items):
      gtkcol = self.tuple2col(color_tuple)
      color_table.pack_start(self.__create_color_box(idx, name, desc, gtkcol))
    self.viewport = gtk.Viewport()
    self.viewport.add(color_table)
    self.ui.scroll_wnd.add(self.viewport)

  def __create_color_box(self, idx, name, desc, gtkcol):
    hbox = gtk.HBox()
    la = gtk.Label(str(idx))
    la.set_padding(4, 0)
    hbox.pack_start(la, expand = False, fill = False)
    la = gtk.Label(desc)
    la.set_padding(4, 0)
    la.set_alignment(0.0, 0.5)
    hbox.pack_start(la, expand = True, fill = True)
    bu = gtk.ColorButton(gtkcol)
    bu.connect("color-set", self.cb_update_color, name)
    self.bucolor_dict[name] = bu
    hbox.pack_end(bu, expand = False, fill = False)
    return hbox

  def cb_update_color(self, cb, name):
    new_col = self.col2tuple(cb.get_color())
    self.color_dict[name] = new_col

  def __restore_dict(self):
    for name in self.color_dict.keys():
      new_col = self.color_dict[name]
      old_col = self.color_dict_copy[name]
      if new_col != old_col:
        self.color_dict[name] = old_col

  def tuple2col(self, tuple):
    r, g, b = [int(PropertiesDialog.MAX_COL * i) for i in tuple]
    return gtk.gdk.Color(r, g, b)

  def col2tuple(self, gtkcol):
    rgb = [gtkcol.red, gtkcol.green, gtkcol.blue]
    return tuple([round(float(i) / PropertiesDialog.MAX_COL, 2) for i in rgb])

def create_filter(pattern, filter_name):
  f = gtk.FileFilter()
  f.set_name(filter_name)
  f.add_pattern(pattern)
  return f

class Main(TopLevel):
  """
  Main application window. Windows are launched by Launcher instance
  (passed in constructor parameter).
  """
  WINDOW_FILE = "example"
  ASK_FOR_SAVE = "Diagram został zmodyfikowany.\nCzy chcesz zapisać zmiany?"
  OPEN_DIAGRAM = "Otwórz diagram z pliku:"
  SAVE_DIAGRAM = "Zapisz diagram do pliku:"
  EXPORT_AS = "Wyeksportuj diagram do pliku %s"
  INVALID_FORMAT = "Niepoprawny format pliku."
  CANNOT_READ_FILE = "Plik %s nie mógł zostać wczytany.\nFormat pliku jest niepoprawny. "
  WARNING = "Ostrzeżenie"
  CHOOSE_DATE = "Wybierz datę początkową:"
  POS_MENU_RECENT_FILES = 2
  MENU_RECENT_FILES_LABEL = "O_statnio używane..."
  EXPORT_NOT_SUPPORTED ="Nieudany eksport"
  EXPORT_TO_FORMAT_NOT_SUPPORTED="Eksport pliku do formatu %s nie jest możliwy.\nFunckja ta będzie dostępna w jednym z kolejnych\nwydań programu womoon."
  PROJECT_FILTERS = [\
    create_filter("*.xml", "Pliki XML"),\
    create_filter("*.txt", "Pliki TXT"),\
    create_filter("*", "Wszystkie pliki")]

  def __init__(self, launcher):
    TopLevel.__init__(self, Main.WINDOW_FILE)
    self.main.connect("delete_event", self.cb_exit)
    self.controller = None
    self.init_menu()
    self.launcher = launcher
    self.project  = None

  def on_model_changed(self, attr, oldv, newv):
    if self.chart is not None:
      self.chart.add_on_change_callback(self.project_changed)

  def cb_project_changed(self, proj, cause):
    if cause in [ChartProject.CREATED, ChartProject.LOADED]:
      self.update_window()
    self.update_status(cause)

  def update_status(self, cause):
    ctx = self.ui.statusbar.get_context_id("ctx-changed")
    self.ui.statusbar.pop(ctx)
    self.ui.statusbar.push(ctx, ChartProject.EVENT_DESC[cause])

  def update_window(self):
    model = self.project.chart
    view = ChartViewArea(model)
    if self.controller is not None:
      self.ui.vbox_chart.remove(self.controller)
    self.controller = ChartController(model, view)
    self.controller.add_on_column_doubleclicked(self.cb_column_doubleclicked)    
    self.ui.vbox_chart.pack_end(self.controller)
    self.main.show_all()

  def cb_column_doubleclicked(self, idx):    
    dlg = DayDialog()
    dlg.show_day(self.project.chart, idx)

  def init_menu(self):
    toolbuttons =  [self.ui.toolbutton_new, self.ui.toolbutton_open, self.ui.toolbutton_save, 
      self.ui.toolbutton_save_as, self.ui.toolbutton_properties, self.ui.toolbutton_exit]
    actions = [self.cb_new, self.cb_open, self.cb_save, self.cb_save_as, self.cb_properties, self.cb_exit]
    menu_items = [self.ui.mi_new,  self.ui.mi_open, self.ui.mi_save, self.ui.mi_save_as,  self.ui.mi_properties, self.ui.mi_exit]
    for mi, act in zip(menu_items, actions):
      mi.connect("activate", act)
    for btn, act in zip(toolbuttons, actions):
      btn.connect("clicked", act)
    self.ui.mi_about.connect("activate", self.cb_about)
    self.ui.mi_export_png.connect("activate", self.cb_export, Exporter.PNG)
    self.ui.mi_export_svg.connect("activate", self.cb_export, Exporter.SVG)
    self.ui.mi_export_pdf.connect("activate", self.cb_export, Exporter.PDF)
    self.ui.mi_export_html.connect("activate", self.cb_export, Exporter.HTML)
#   create recently used menu
    ri = self.__create_recent_menu_item()
    self.ui.menuitem_file.get_submenu().insert(ri, Main.POS_MENU_RECENT_FILES)


  def cb_open_recent(self, rec_chooser):
    ri = rec_chooser.get_current_item()
    fname = ri.get_uri()
    if ri.exists():
      self.launcher.cb_open(self, fname)

  def __create_recent_menu_item(self):
    me = gtk.RecentChooserMenu()
    me.set_show_not_found(False)
    me.set_show_numbers(True)
    me.connect("item-activated", self.cb_open_recent) 

    mi = gtk.MenuItem(Main.MENU_RECENT_FILES_LABEL)
    mi.set_submenu(me)

    filter = gtk.RecentFilter()
    filter.add_pattern(".*\.xml")    
    me.set_filter(filter)
    return mi

  def change_decided(self):    
    out = True
    if self.project.is_modified: 
      resp = self.ask_for_saving()
      out = resp != gtk.RESPONSE_CANCEL
    return out

  def cb_new(self, wgt):
    self.launcher.cb_new(self)

  def cb_open(self, wgt):
    fname = Main.get_filename(Main.OPEN_DIAGRAM, gtk.STOCK_OPEN, gtk.FILE_CHOOSER_ACTION_OPEN)
    if fname is None:
      return
    self.launcher.cb_open(self, fname)    

  def cb_export(self, wgt, export_type):
    if not self.change_decided():
      return
    if not Exporter.export_supported(export_type):
      Main.show_warning(self, Main.EXPORT_NOT_SUPPORTED, Main.EXPORT_TO_FORMAT_NOT_SUPPORTED % export_type)
    else:
      fname = Main.get_filename(Main.EXPORT_AS % export_type, gtk.STOCK_SAVE, gtk.FILE_CHOOSER_ACTION_SAVE)
      if fname is not None:
        Exporter.export(export_type, self.project.chart, fname)

  def cb_save(self, wgt):
    if self.project.fname is None:
      self.project.fname = Main.get_filename(Main.SAVE_DIAGRAM, gtk.STOCK_SAVE, gtk.FILE_CHOOSER_ACTION_SAVE)
    self.project.save(self.project.fname)

  def cb_save_as(self, wgt):
    fname = Main.get_filename(Main.SAVE_DIAGRAM, gtk.STOCK_SAVE, gtk.FILE_CHOOSER_ACTION_SAVE)
    self.project.save(fname)

  def cb_properties(self, wgt):
    col_dict = self.controller.view.chart_context_painter.colors
    prop_dlg = PropertiesDialog()
    prop_dlg.set_color_dict(col_dict)
    prop_dlg.main.show_all()

  def cb_about(self, wgt):
    dlg = AboutDialog()
    dlg.run()

  def cb_exit(self, *params):
    return self.launcher.cb_exit(self)
 
  def close(self):
    self.main.destroy()

  def get_filename(dlg_title, stock_accept, action_id, filters = PROJECT_FILTERS):
    fname = None
    dlg = gtk.FileChooserDialog(title = dlg_title, action = action_id,
      buttons = (stock_accept, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    for filter in filters:
      dlg.add_filter(filter)
    if action_id == gtk.FILE_CHOOSER_ACTION_SAVE:
      dlg.set_do_overwrite_confirmation(True)
    dlg.set_default_response(gtk.RESPONSE_OK)
    resp = dlg.run()
    if resp == gtk.RESPONSE_OK:
      fname = dlg.get_filename()
    dlg.destroy()
    return fname
  get_filename = staticmethod(get_filename)

  def ask_for_saving(self):
    msg = gtk.MessageDialog(parent = self.main, flags = gtk.DIALOG_MODAL, type = gtk.MESSAGE_WARNING,
      buttons = gtk.BUTTONS_YES_NO, message_format = Main.ASK_FOR_SAVE)
    msg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    msg.set_default_response(gtk.RESPONSE_YES)
    resp = msg.run()
    msg.destroy()
    if resp == gtk.RESPONSE_YES:
      self.cb_save(None)      
    return resp

  def ask_for_date(parent):
    msg  = gtk.Dialog(parent = parent.main, flags = gtk.DIALOG_MODAL, title = Main.CHOOSE_DATE,
      buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    cal = gtk.Calendar()    
    msg.vbox.pack_start(cal)
    msg.show_all()
    resp = msg.run()
    msg.destroy()
    if resp == gtk.RESPONSE_OK:
      y, m, d = cal.get_date()
      return date(y, m + 1, d)
    else:
      return date.today()
  ask_for_date = staticmethod(ask_for_date)

  def show_warning(parent, primary_text, secondary_text):
    msg = gtk.MessageDialog(parent = parent.main, flags = gtk.DIALOG_MODAL, type = gtk.MESSAGE_WARNING,
      buttons = gtk.BUTTONS_CLOSE, message_format = primary_text)
    msg.set_title(Main.WARNING)
    msg.format_secondary_text(secondary_text)
    msg.set_default_response(gtk.RESPONSE_CLOSE)
    msg.run()
    msg.destroy()
  show_warning = staticmethod(show_warning)
  
def date_str(model, idx):
  d = model.start_date + timedelta(idx)
  return d.strftime(ChartModel.DATE_FORMAT)

if __name__ == "__main__":
  Main()
  gtk.main()

