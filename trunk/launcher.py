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

import sys
import os
import gtk
from datetime import date
from main import Main
from chartproject import ChartProject

class Launcher:
  def __init__(self):
    self.launched = []

  def cb_open(self, main_wnd, fname):
    """
    Callback of "Open" menu button from main_wnd.
    Assume fname is not None
    """
    if main_wnd is None:
      main_wnd = self.cb_new(None)

    try:
      if main_wnd.project.is_untouched():
        main_wnd.project.load(fname)
      else:
        project = self.load_project(fname)
        self.show_main(project, ChartProject.LOADED)
    except:
      Main.show_warning(main_wnd, Main.INVALID_FORMAT,  Main.CANNOT_READ_FILE % fname)

  def cb_new(self, main_wnd):
    if len(self.launched) == 0 or main_wnd == None:
      start_date = date.today()
    else:
      start_date = Main.ask_for_date(main_wnd)

    if main_wnd is not None and main_wnd.project.is_untouched():
      main_wnd.project.create(start_date)
    else:
      project = self.create_project(start_date)
      main_wnd = self.show_main(project, ChartProject.CREATED)
    return main_wnd

  def cb_exit(self, main_wnd, *oth):
    if not main_wnd.change_decided():
      return True
    if len(self.launched) > 1:
      main_wnd.close()
      self.launched.remove(main_wnd)
    else:
      gtk.main_quit()
    return False

  def load_project(self, fname):
    project = ChartProject()
    project.load(fname)
    return project

  def create_project(self, date):
    project = ChartProject()
    project.create(date)
    return project

  def show_main(self, project, cause):
    wnd = Main(self)
    project.add_on_project_changed_cb(wnd.cb_project_changed)
    wnd.project = project
    self.launched.append(wnd)
    wnd.update_window()
    wnd.update_status(cause)
    wnd.main.show_all()
    return wnd
      
if __name__ == "__main__":  
  file_names = sys.argv[1:]
  existing = filter(os.path.exists, file_names)
  launcher = Launcher()
  for name in file_names: #existing:
    launcher.cb_open(None, name)

  if not existing:
    launcher.cb_new(None)
  gtk.main()

  
