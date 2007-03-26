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

import os.path
import gtk
import gtk.glade

class TopLevel:

  GLADE_DIR = "glade"

  class GladeProxy(gtk.glade.XML):
    def __getattr__(self, attr_name):
      return self.get_widget(attr_name)

  def __init__(self, filename):
    self.ui = self.GladeProxy(os.path.join (self.GLADE_DIR, filename + ".glade"))        
    self.main = self.ui.main
    self.main.hide_all()

  def on_delete(self, win, evt):
    gtk.main_quit()
    
  def on_hide(self, win, evt):
    self.main.hide()
