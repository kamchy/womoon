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

from datetime import date, timedelta
import random

class ChartModel:
  DATE_FORMAT = "%Y-%m-%d"

  def __init__(self):
    self.nx = 31
    self.ny = 15
    self.base = 362
    self.range = (self.base, self.base + self.ny)
    self.factor = 10.0
    self.start_date = None
    self.days = NotifierList(self.__fire_model_changed)
    self.day_cursor = None
    self.on_change_callbacks = []                                                     
  
  def generate_days(self, date):    
    self.start_date = date
    for i in xrange(self.nx):
      new_date = date + timedelta(i)
      #day = Day(new_date.day, self.range[0] / self.factor, Observation.random(), random.choice([True, False]))
      day = Day(new_date.day, self.range[0] / self.factor, Observation.EMPTY, False)
      self.days.append(day)

  def __set_start_date(self, date):
    self.start_date = date

  def is_sunday(self, i):
    return (self.start_date + timedelta(i)).weekday() == 6

  def get_current_day(self):
    if self.day_cursor is None:
      return (None, -1)
    return (self.days[self.day_cursor], self.day_cursor)

  def get_today(self):
    empty =  (None, -1)
    if self.start_date is None:
      return empty
    curr = date.today()
    offset = (curr - self.start_date).days
    if offset < self.nx and offset >= 0:
      return (self.days[offset], offset)
    else:
      return empty

#   TODO - find prolific days automatically
  def get_prolific_range(self):
    """
    Returns pair of day indixes (both inclusive)
    denoting prolific days
    """    
    return None

  def get_month_str(self):
    end_date = self.start_date + timedelta(self.nx)
    old_m, old_y = self.start_date.month, self.start_date.year
    new_m, new_y = end_date.month, end_date.year
    if (new_m != old_m):
      return "%s %s / %s %s" % (old_m, old_y, new_m, new_y)
    else:
      return "%s %s" % (new_m, new_y)

  def get_days(self):
   return self.days

  def get_ydesc(self):
    scale = [self.range[0] + i for i in xrange(self.ny)]
    return map(lambda d: str(d/self.factor), scale)
                                                   
  def __str__(self):
    return "Width:\t%s\nRange:\t%s\nValues:\t%s" % (self.nx, self.range, self.days)

  def set_temp(self, day_idx, temp):
    if day_idx < 0 or day_idx >= self.nx:
      return
    d = self.days[day_idx]
    new_temp = temp
    if new_temp * self.factor > self.range[1]:
      new_temp = self.range[1] / self.factor
    else:
      if new_temp * self.factor < self.range[0]:
        new_temp = self.range[0] / self.factor
    d.temp = new_temp
    self.__fire_model_changed(day_idx)

  def set_sex(self, day_idx, value):
    if day_idx < 0 or day_idx >= self.nx:
      return
    d = self.days[day_idx]
    if value != d.is_sex:
      d.is_sex = value
    self.__fire_model_changed(day_idx)

  def set_day_cursor(self, new_cursor_idx):
    if new_cursor_idx == self.day_cursor:
      return
    old_cursor = self.day_cursor
    self.day_cursor = new_cursor_idx
    self.__fire_model_changed(old_cursor)
    self.__fire_model_changed(self.day_cursor)

  def get_sex(self, day_idx):
    if day_idx < 0 or day_idx >= self.nx:
      return -1
    return self.days[day_idx].is_sex

  def get_obs(self, day_idx):
    if day_idx < 0 or day_idx >= self.nx:
      return -1
    return self.days[day_idx].obsv

  def set_obs(self, day_idx, value):
    if day_idx < 0 or day_idx >= self.nx or not value in Observation.VALUES:
      return
    d = self.days[day_idx]
    if value != d.obsv:
      d.obsv = value
    self.__fire_model_changed(day_idx)

  def __fire_model_changed(self, day_idx):
    for cb in self.on_change_callbacks:
      cb(day_idx)

  def add_on_change_callback(self, callback):
    self.on_change_callbacks.append(callback)

  def remove_on_change_callback(self, callback):
    if callback in self.on_change_callbacks:
      self.on_change_callbacks.remove(callback)

  def on_day_change(self, day, attr, old_val, new_val):
    if not day in self.days:
      return
    idx = self.days.index(day)
    self.__fire_model_changed(idx)

class Notifier(object):
  def __init__(self, name, callback=None):
    self.name = name
    self.callback = callback

  def __set__(self, obj, nval):
    if obj.__dict__.has_key(self.name):
      oval = obj.__dict__[self.name]
    else: 
      oval = None
    obj.__dict__[self.name] = nval
    self.callback(obj, self.name, oval, nval)

  def __get__(self, obj, type=None):
    return obj.__dict__[self.name]

class NotifierList(list):

  def __init__(self, callback):
    list.__init__(self)
    self.callback = callback

  def __setitem__(self, key, val):
    list.__setitem__(self, key, val)
    self.callback(key)
    
class Day(object):

  def __init__(self, num, temp, obsv, is_sex):
    self.on_change_callbacks = []
    self.num = num
    self.temp = temp 
    self.obsv = obsv
    self.is_sex = is_sex
    self.notes = None
    
  def add_on_change_cb(self, cb):
    self.on_change_callbacks.append(cb)

  def remove_on_change_cb(self, cb):
    if not cb in self.on_change_callbacks:
      self.on_change_callbacks.remove(cb)

  def fire_day_changed(self, attr, old_val, new_val):
    for cb in self.on_change_callbacks:
      cb(self, attr, old_val, new_val)
    
  def __str__(self):
    return "%s" %(self.temp)

  def __repr__(self):
    return self.__str__()

  num = Notifier("num", fire_day_changed)
  temp = Notifier("temp", fire_day_changed)
  obsv = Notifier("obsv", fire_day_changed)
  is_sex = Notifier("is_sex", fire_day_changed)
  notes = Notifier("notes", fire_day_changed)

class Observation:
  """
  Defines possible results of observation
  """
  EMPTY = 0
  MENS_1 = 1
  MENS_2 = 2
  MENS_3 = 3
  MENS_4 = 4
  LITTLE_NOOVUL = 5
  LOT_NOOVUL = 6
  LITTLE_OVUL = 7
  LOT_OVUL = 8
  PEAK = 9

  VALUES = [EMPTY, MENS_1, MENS_2, MENS_3, MENS_4, \
    LITTLE_NOOVUL, LOT_NOOVUL, LITTLE_OVUL, LOT_OVUL, PEAK]

  DESC = ["Brak", "Plamienie", "Menstuacja delikatna", "Menstruacja obfita", 
          "Menstruacja bardzo obfita", "Śluz niepłodny - mało", "Śluz niepłodny - obficie",
          "Śluz płodny - mało", "Śluz płodny - obficie", "Szczyt objawu śluzu"] 
  def random():    
    return random.choice(Observation.VALUES)
  random = staticmethod(random)

class FertilityHeuristics:

  def get_fertile_range(self, daylist):
    """
    Alanyse given daylist and returns either a both-side inclusive
    range of most-probably fertile days or returns None.

    Days before first fertile day returned by this method are considered
    to be conditionally unfertile. 
    Days after last day returned by this method are considered
    to be unconditionally unfertile.
    """
    DAYS_BEFORE = 6
    DAYS_AFTER = 3
    i = -1
    for i, d in enumerate(daylist):
      if d.obsv == Observation.PEAK:
        break
    # we should have at least 6 days to analyse before peak
    if i < DAYS_BEFORE: 
      return None
    peak_temp = daylist[i].temp
    # max temp
    max_before = -1
    max_before_idx = -1
    for nr, d in enumerate(daylist[i - DAYS_BEFORE - 1, i]):
      if d.temp > max_before:
        max_before = d.temp
        max_before_idx = nr + i - DAYS_BEFORE
    # temp in 6 days before peak cannot reach peak temp (to be fertile)
    if max_before >= peak_temp:
      return None

    # three days after temp cannot fall below max_before

    min_after_peak = reduce(min, [d.temp for d in daylist[i, i+DAYS_AFTER]])
    if min_after_peak <= max_before:
      return None
    return [i - DAYS_BEFORE - 1, i + DAYS_AFTER]





