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

class ObservableDict(dict):
  """
  Dictionary that implements observer pattern.
  Listeners can register for updates using
  add_on_change_callback()
  """

  def __init__(self, initial):
    dict.__init__(self, initial)
    self.on_change_callbacks = []
   
  def fire_model_changed(self, old_col, new_col):
    for cb in self.on_change_callbacks:
      cb(old_col, new_col)

  def add_on_change_callback(self, callback):
    self.on_change_callbacks.append(callback)

  def remove_on_change_callback(self, callback):
    if callback in self.on_change_callbacks:
      self.on_change_callbacks.remove(callback)

  def __setitem__(self, key, value):
    old_value = None
#    print "Setting value %s with key %s: dict = %s" %(value, key, self)
    if self.has_key(key):
      old_value = dict.__getitem__(self, key)
    dict.__setitem__(self, key, value)
    self.fire_model_changed(old_value, value)
  
class ObservableNamedDict(ObservableDict):
  """
  Dictionary which stores named key-value pairs
  Name of the pair retrievable using specific key 
  is available with following call:
  thedict.get_name(key)
  """

  def __setitem__(self, key, value):
    old_value = None
    old_name = ""
    if self.has_key(key):
      old_name, old_value = dict.__getitem__(self, key)
    dict.__setitem__(self, key, (old_name, value))
    self.fire_model_changed(old_value, value)

  def __getitem__(self, key):
    name, val =  dict.__getitem__(self, key)
    return val

  def get_name(self, key):
    name, val =  dict.__getitem__(self, key)
    return name

class Listener:
  """
  Testing purposes class
  """
  def color_changed(self, old, new):
    print "Color changed: old = %s, new = %s" % (old, new)

if __name__ == "__main__":
  colors = {1: "blue", 2:"magenta", 3:"red", 4: "citro"}
  l = Listener()
  od = ObservableDict(colors)
  od.add_on_change_callback(l.color_changed)
  od[2] = "dupa"

  named_colors =  {1: ("jeden", "blue"), 2:("dwa", "magenta"), 3:("trzy", "red"), 4:("cztery",  "citro")}
  nod = ObservableNamedDict(named_colors)

  nod.add_on_change_callback(l.color_changed)
  nod[2] = "dupa"
  print nod[2]
  print type(nod[2])
  print nod.get_name(2)
  for i in nod.items():
    print i
