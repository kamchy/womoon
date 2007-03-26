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

import os, sys
class Stream:

  def __init__(self):
    self.__elems = []
    
  def add(self, elem):
    self.__elems.append(elem)
  
  def __lshift__(self, obj):
    self.add(obj)
    return obj

  def __str__(self):
    return "".join(map(str, self.__elems))



class Tag(Stream):

  def __init__(self, name, attrs = {}, **param_attrs):
    Stream.__init__(self)
    self.__name = name
    self.__attrs = attrs.copy()
    self.__attrs.update(param_attrs)
      
  def __str__(self):
    s = Stream.__str__(self)
    attrs_str = "".join([' %s="%s"' % (name, value) for name, value in self.__attrs.iteritems()])
    if s:
      return "<%s%s>%s</%s>" % (self.__name, attrs_str, s, self.__name)
    else:
      return "<%s%s/>" % (self.__name, attrs_str)
            
  def add_attr(self, name, value):
    self.__attrs[name] = value    

class HtmlDocument(Stream):

  def __init__(self, title):
    Stream.__init__(self)
    self.title = title
    
  def __str__(self):
    result = Stream()
    result << '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
    html = Tag("html", xmlns="http://www.w3.org/1999/xhtml", lang="en")
    head = Tag("head")
    head << '<meta http-equiv="content-type" content="text/html; charset=ISO-8859-2"/>'
    head << '<meta name="author" content="Kamila Chyla"/>'
    head << Tag("title") << self.title
    head << Tag("link", type = "text/css", rel = "stylesheet", href = "../style.css")
    html << head
    html << Tag("body") << Stream.__str__(self)
    result << html
    return str(result)

class XMLDocument(Stream):

  def __init__(self, root):
    Stream.__init__(self)
    self.root_stream = root
    
  def __str__(self):
    result = Stream()
    result << '<?xml version="1.0" standalone="yes"?>'
    result << self.root_stream
    return str(result)

    
class HtmlCreator:
  HTML_FILE = "index.html"
  def __init__ (self, source, out_dir):
    self.source = source
    self.file_name = os.path.join(out_dir, HtmlCreator.HTML_FILE)
  
  def create(self):
    doc = HtmlDocument('History')        
    doc << Tag("div", {"class" : "header"}) << "Clearcase history"
    doc << self.source
    print "creating file: %s" % self.file_name
    f = open (self.file_name, "w+")
    f.write(str(doc))
    f.close()
