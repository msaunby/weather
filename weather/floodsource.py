#!/usr/bin/env python
#

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
import urllib
import logging
import csv, StringIO
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

class Welcome(webapp.RequestHandler):
  def get(self):
    lat = None
    lng = None
    latlng = self.request.get("latlng")
    rean = self.request.get("reanalysis")
    if rean == '':
      rean = 'ncep'
      pass

    try:
      latlng = latlng[1:-1]
      (lat,lng) = latlng.split(',')
      lat = float(lat)
      lng = float(lng)
      latlng = "(%.2f,%.2f)" % (lat, lng)
    except:
      latlng = ""
      lat = None
      lng = None
      pass

    recs = []
    if lat is not None and lng is not None:
      table = "2358653"
      lat_s = lat - 2.0
      lat_n = lat + 2.0
      lng_w = lng - 2.0
      lng_e = lng + 2.0
      region = "RECTANGLE(LATLNG(%.2f,%.2f),LATLNG(%.2f,%.2f))" % (lat_s,lng_w,lat_n,lng_e)
      sql = "SELECT * FROM %s WHERE ST_INTERSECTS(centroid_x, %s) ORDER BY began" % (table, region)
      url = "http://www.google.com/fusiontables/api/query"
      resp = urlfetch.fetch(url, payload="sql="+sql, method="POST", follow_redirects=True)

      if resp.status_code == 200:
          reader = csv.DictReader(StringIO.StringIO(resp.content))
          for fld in reader:
              recs.append(fld)
              pass
          pass
      else:
          logging.info("Failed to get CSV from Fusion Table %s" % table)
          logging.debug(resp.status_code)
          logging.debug(resp.content)
          pass
      pass
    else:
      # No valid latlng
      lat = 0.0
      lng = 0.0
      pass

    marker_text = "&maptype=hybrid"
    mkrref = {}
    idn = 0
    for m in recs:
      mkr =  chr(ord('1')+idn)
      mkrref[mkr] = idn
      marker_text += "&markers=color:blue|label:%c|%s,%s" % (mkr,m['centroid_y'],m['centroid_x'])
      m['id'] = mkr
      idn += 1
      pass

    # Names with dots in can be problematic so in Javascript use the name 
    # rather than id.
    # Note name is opendap field name, id is part of file name.
    # e.g. file  air.2m will have field named 'air'.
    # Neither are standardised so names and ids for NCEP and 20CR
    # are different.
    # These same names are used in the visualization, so modifiation
    # will be required if air.2m and air.sfc are to be plotted on
    # the same chart.
    # metseries.py fetches the data. Most likely from
    # http://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets20thC_ReanV2/gaussian/monolevel/
    # Browse that dir to see what parameters are available.
    # air.2m, air.sfc, albedo, cprat...
    paramlist = {}
    paramlist['20cr'] = [{'name':'prate','id':'prate','en':'rain rate'},
                 {'name':'soilm','id':'soilm','en':'soil moisture'},
                 {'name':'runoff','id':'runoff','en':'run off'},
                 {'name':'air','id':'air.2m','en':'air temperature'},
                 {'name':'press','id':'press.sfc','en':'surface pressure'}]

    paramlist['ncep'] = [{'name':'prate','id':'prate.sfc','en':'rain rate'},
                 {'name':'soilw','id':'soilw.0-10cm','en':'soil moisture'},
                 {'name':'runof','id':'runof.sfc','en':'run off'},
                 {'name':'air','id':'air.2m','en':'air temperature'},
                 {'name':'pres','id':'pres.sfc','en':'surface pressure'}]

    template_values = {
            'locationName' : latlng,
            'latlng' : latlng,
            'map_centre' : "%.2f,%.2f" % (lat,lng),
            'markers' : marker_text,
            'mkrref' : mkrref,
            'floodrecs' : recs,
            'rean': rean,
            'paramlist' : paramlist[rean],
            'message' : self.request.path
        }
    if self.request.path == '/':
         path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
    else:
        path = os.path.join(os.path.dirname(__file__), 'templates' + self.request.path)
        pass

    self.response.out.write(template.render(path, template_values))
    return
  pass

from getmetdata import *
from metseries import *

application = webapp.WSGIApplication([
    ('/getmetdata', GetMetData),
    ('/metseries', GetMetSeries),
    ('.+',Welcome)], debug=False)

def main():
  run_wsgi_app(application)
if __name__ == '__main__':
  main()
