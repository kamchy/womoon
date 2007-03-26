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

import os
import xml.parsers.expat
from datetime import date
import time
from tag import XMLDocument, Tag
from chartmodel import ChartModel, Day

class ChartModelSaver:
  def __init__(self):
    self.model = None
 
  def save(self, model, fname):
    self.model = model
    f = open(fname, "w+")
    root = self.__create_chart_node()
    f.write(str(XMLDocument(root)))
    f.close()

  def __create_chart_node(self):
    model = self.model
    r = Tag("chart")
    general = Tag("general", {
      "nx": model.nx,
      "ny": model.ny,
      "base": model.base,
      "factor": model.factor,
      "start_date": model.start_date}
      )
    r << general
    days_tag = Tag("days")
    for i, d in enumerate(model.days):
      day_tag = Tag("day", {
        "id": i,
        "num" : d.num, 
        "temp": d.temp, 
        "obsv": d.obsv, 
        "is_sex": d.is_sex
      })
      days_tag << day_tag 
      if d.notes is not None:
         day_tag << Tag("notes") << d.notes
    r << days_tag
    return r

class ChartModelLoader:
  def __init__(self):
    self.fname = None
    self.model = None
    
  def load(self, fname):
    self.model = ChartModel()    
    self.daylist = {}
    self.currid = None
    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = self.__parse_element
    p.CharacterDataHandler = self.__parse_chars
    f = open(fname, "r")
    p.ParseFile(f)
    f.close()
    self.__sort_days()
    return self.model

  def __sort_days(self):
    items = self.daylist.items()
    items.sort(key=lambda el: el[0])
    self.model.days = map(lambda el: el[1], items)

  def __parse_element(self, name, attrs):
    if name == "general":
      self.model.nx = int(attrs["nx"])
      self.model.ny = int(attrs["ny"])
      self.model.base = int(attrs["base"])
      self.model.factor = float(attrs["factor"])
      ttuple = time.strptime(attrs["start_date"], ChartModel.DATE_FORMAT)
      self.model.start_date =  date(*ttuple[:3])
    elif name == "day":
      num = int(attrs["num"])
      temp = float(attrs["temp"])
      obsv = int(attrs["obsv"])
      is_sex = attrs["is_sex"] == "True"
      id = int(attrs["id"])
      d = Day(num, temp, obsv, is_sex)
      self.daylist[id] = d
      self.currid = id

  def __parse_chars(self, chars):
    old = self.daylist[self.currid].notes 
    if old is None:
      old = ""
    self.daylist[self.currid].notes = old + chars

if __name__ == "__main__":
  fname = "/home/karma/chart1.xml"
  fname2 = "/home/karma/chart2.xml"
  mo = ChartModel()
  mo.generate_days(date.today())  
  mo.days[1].notes = "This is my notes.\n And I love it!"
  mo.days[2].notes = "More notess"
  cm = ChartModelSaver()
  cm.save(mo, fname)

  lo = ChartModelLoader()
  mo2 = lo.load(fname)
  
  cm = ChartModelSaver()
  cm.save(mo2, fname2)

