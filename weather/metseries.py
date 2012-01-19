#!/usr/bin/env python
#

from datetime import datetime, tzinfo, timedelta, date
from minpydap.parsers.dds import DDSParser
from minpydap.parsers.das import DASParser
from minpydap.minxdr import DapUnpacker
from google.appengine.ext import webapp
from coards import from_udunits, to_udunits
from gviz_api import DataTable
from coords20cr import toXY
from decimal import *
import logging

def dDate(time, dataset):
    time_units =  dataset['time'].units
    #logging.debug(time_units)
    if time_units == "hours since 1-1-1 00:00:0.0":
        time_units = "hours since 1800-1-1 00:00:0.0"
        #logging.debug("fixed " + time_units)
        time = time - (657438.0 * 24)
        pass
    date = from_udunits(time, time_units)
    return date


from google.appengine.api import urlfetch
def fetch(url):
    resp = urlfetch.fetch(url, deadline=60, follow_redirects=True)
    if resp.status_code == 200:
        return resp.content
    else:
        logging.warn(resp.status_code)
        return None



#    if tqx['out'] == 'csv':
#        description = {"date": ("string", "Date"),
#                       "value": ("number", config['en'])}
#    else:
#        description = {"date": ("datetime", "Date"),
#                       "value": ("number", config['en'])}
#        pass

#    if tqx['out'] == 'csv':
#        print 'Content-type: text/plain\n'
#        csv = data_table.ToCsv(columns_order=("date", "value"),order_by="date",separator=",")
#        print csv
#    else:
#        json = data_table.ToJSonResponse(columns_order=("date", "value"), order_by="date", 
#                                         req_id=tqx['reqId'])
    
class GetMetSeries(webapp.RequestHandler):
    def get(self):
        self.getArgs()
        self.download()
        self.returnData()
        return

    def getArgs(self):
      global lat, lng, fi, dataurl #start, end
      self.tqx=self.request.get("tqx")
      #lat = float(self.request.get("lat"))
      #lng = float(self.request.get("lng"))
      self.x = int(self.request.get("x"))
      self.y = int(self.request.get("y"))
      fi = self.request.get("fi")
      year_start = self.request.get("yr0")
      rean = self.request.get("rean")
      if rean == "ncep":
          dataurl = "http://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/" + \
              "/ncep.reanalysis/surface_gauss/%s.gauss.%s.nc" % (fi,str(year_start))
      else:
          dataurl = "http://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets20thC_ReanV2/" + \
              "gaussian/monolevel/%s.%s.nc" % (fi,str(year_start))
          pass

      return

    def download(self):
        global dataurl
        #(x,y) = toXY(lat,lng)
        (x,y) = (self.x,self.y)
        #print "fetching", dataurl, fi, x, y

        # for 1970 test time is 1490184.0 to 1498941.0
        # Method 1.
        # Fetch .das then fetch .dods with selection.
        # problem. How to know what the time selections are?
        #
        # Method 2.
        # 1. Fetch. dds.
        # 2a. Fetch .dods of entire sequence.
        # 2b. Fetch .das to get scale factors.
        # 3a. Select from time sequence.
        # 4. Apply scale factors.
 
        param = fi.split('.')[0]
        self.param = param
        data = fetch(dataurl + ".dds")
        fulldataset = DDSParser(data).parse()
        (tmax,ymax,xmax) = fulldataset[param].shape
        das = fetch(dataurl + ".das")
    
        # Fetch with extension .dods to get dds plus binary data.
        # always specify a selection.
        # e.g. dataurl + ".dods" + "?prate[1000:1004][80][31]"
        query = "?%s[0:%d][%d][%d]" % (param,tmax-1,y,x)
        data = fetch(dataurl + ".dods" + query)
        dds, xdrdata = data.split('\nData:\n', 1)
        dataset = DDSParser(dds).parse()
        dataset = DASParser(das, dataset).parse()
        fulldataset  = DASParser(das, fulldataset).parse()
        #logging.debug("time")
        #logging.debug(fulldataset['time'].units)
        dataset.data = DapUnpacker(xdrdata, dataset).getvalue()
        dataset['time'] = fulldataset['time']
        self.scale_factor = Decimal(str(dataset[param].scale_factor)) 
        self.add_offset = Decimal(str(dataset[param].add_offset)) 
        self.datasetinfo = fulldataset
        self.dataset = dataset
        (self.dataRaw,self.dataTime,self.dataLat,self.dataLng) = dataset[param].data
        return



    def returnData(self):
        data = []
        descr = [("Date", "datetime"),
                 (self.param, "number")]

        for i in range(len(self.dataRaw)):
            # set decimal precision for calc
            getcontext().prec = 24
            v = (Decimal(str(self.dataRaw[i])) * self.scale_factor) + self.add_offset
            # apply precision
            getcontext().prec = 3
            v = +v
            data.append( [dDate(self.dataTime[i],self.dataset), v ] )
            pass
        table = DataTable(descr, data)
        expires = datetime.now() + timedelta(days=5) 
        self.response.headers['Content-type'] = 'text/plain'
        self.response.headers['Expires'] = expires.strftime(
            '%a, %d %b %Y %H:%M:%S %Z')
        self.response.headers['Cache-control'] = 'public'
        self.response.out.write(table.ToResponse(tqx=self.tqx))
        return
