#!/usr/bin/env python
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

from distutils.core import setup

setup(name='Womoon',
      version='1.0',
      description='Edytor wykresów płodności',
      author='Kamila Chyla',
      author_email='bigjane2006@gmail.com',
      url='http://kamila.chyla.pl/womoon/',
      py_modules= [
        'chartmodelio',
        'chartmodel',
        'chartproject',
        'common',
        'drawingarea',
        'exporter',
        'main',
        'observabledict',
        'tag',
        ],
      scripts=[
        'launcher.py',
        ],
      data_files=[
        ("glade", [
          "glade/day-dialog.glade", 
          "glade/example.glade", 
          "glade/properties.glade",
          "glade/day.png",
          "glade/favourite.png",
          "glade/about.glade", 
          ])],
     )
