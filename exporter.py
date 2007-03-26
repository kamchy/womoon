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

import drawingarea

class Exporter:
  def export_png(model, fname):
    """
    Exports given chartmodel to file with given name as pdf document
    If such file exists, it is overwritten    
    """
    pic = drawingarea.ChartViewPicture(model, 800, 600)
    pic.write(fname);

  def export_svg(model, fname):
    """
    Exports given chartmodel to file with given name as svg document
    If such file exists, it is overwritten    
    """
    pic = drawingarea.ChartViewSVG(model, 800, 600)
    pic.write(fname);

  def export_html(model, fname):
    """
    Exports given chartmodel to file with given name as html document
    If such file exists, it is overwritten    
    """
    print "not implemented"
  
  def export_pdf(model, fname):
    """
    Exports given chartmodel to file with given name as pdf document.
    If such file exists, it is overwritten    
    """
    pic = drawingarea.ChartViewPdf(model, 800, 600)
    pic.write(fname);

  def export(export_type, model, fname):
    if not Exporter.export_supported(export_type):
      raise Exception("Format exportu %s nie jest obsługiwany" % export_type)
    Exporter.EXPORT_METHODS[export_type](model, fname)
  export = staticmethod(export)

  def export_supported(export_type):
     return Exporter.EXPORT_METHODS.has_key(export_type)
  export_supported = staticmethod(export_supported)

  PNG = "png"
  SVG = "svg"
  PDF = "pdf"
  HTML = "html"

  EXPORT_METHODS = {PNG: export_png, SVG: export_svg, PDF: export_pdf}

