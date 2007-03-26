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

import chartmodel
from chartmodel import Notifier, ChartModel
from chartmodelio import ChartModelLoader, ChartModelSaver

class ChartProject(object):
  """
  Stores information about diagram's filename
  and its state loaded to one window.
  """

  loader = ChartModelLoader()
  saver = ChartModelSaver()

  SAVED = "saved"
  LOADED = "loaded"
  CHANGED = "changed"
  CREATED = "created"
  
  EVENT_DESC = {
    SAVED : "Diagram został zapisany",
    LOADED : "Diagram został odczytany z pliku.",
    CHANGED : "Diagram został zmieniony",
    CREATED : "Utworzono nowy diagram",
  }
  
  def __init__(self):
    self.on_project_changed_cb = []
    self.chart = None
    self.fname = None
    self.is_modified = False

  def is_untouched(self):
    """
    Defines condition for loading diagram to the current
    window (only if both no project was loaded before
    and empty project was not yet modified)
    """
    return self.fname is None and not self.is_modified

  def project_changed(self, day_idx):
    """
    Fires notification about ChartProject change.
    This is called in two cases:
    a) model field was set on self or
    b) model has been modified
    """
    self.is_modified = True
    self.fire_project_changed(ChartProject.CHANGED)

  def on_model_changed(self, attr, oldv, newv):
    if self.chart is not None:
      self.chart.add_on_change_callback(self.project_changed)

  chart = Notifier("chart", on_model_changed)

  def save(self, fname):
    if fname is None:
      return
    ChartProject.saver.save(self.chart, fname)
    self.is_modified = False
    self.fire_project_changed(ChartProject.SAVED)    

  def load(self, fname):
    if fname is None:
      return
    self.fname = fname
    self.chart = ChartProject.loader.load(self.fname)
    self.is_modified = False
    self.fire_project_changed(ChartProject.LOADED)

  def create(self, start_date):
    self.is_modified = False
    self.chart = ChartModel()
    self.chart.generate_days(start_date)
    self.fname = None
    self.fire_project_changed(ChartProject.CREATED)

  def add_on_project_changed_cb(self, cb):
    self.on_project_changed_cb.append(cb)

  def remove_on_project_changed_cb(self, cb):
    if cb in self.on_project_changed_cb:
      self.on_project_changed_cb.remove(cb)

  def fire_project_changed(self, change_flag):
    for cb in self.on_project_changed_cb:
      cb(self, change_flag)

