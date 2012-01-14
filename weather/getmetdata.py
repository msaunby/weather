#!/usr/bin/python
#
# Returns reanalysis data for timeseries at specified lat/lng.
# Make async calls for JSON data and return a single merged file.
#
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from django.utils import simplejson as json
import csv
import logging
# gviz_api.py available here http://code.google.com/p/google-visualization-python/
# Note my version is modified to handle datetime better and allow decimal.Decimal numbers.  
import gviz_api
import StringIO
from gviz_api import DataTable
from datetime import datetime, timedelta
from decimal import Decimal
from coords20cr import toXY

def handle_result(rpc,yr):
    result = rpc.get_result()
    if result.status_code == 200:
        logging.debug(result.content[0:30])
        logging.debug(result.headers)
        csvlist[yr].append(result.content)
        pass
    else:
        logging.debug(result.status_code)
        logging.debug(result.content)
    return


# Use a helper function to define the scope of the callback.
def create_callback(rpc,yr):
    return lambda: handle_result(rpc,yr)

class GetMetData(webapp.RequestHandler):
    def post(self):
        self.get()
        return

    def get(self):
        self.getArgs()
        #download_host = self.request.host_url
        download_host = "http://floodsourcerhok.appspot.com"
        logging.debug(download_host)
        self.download(download_host)
        self.returnData(self.tqx)
        return

    def returnData(self,tqx):
        alldata = []
        descr = []
        for yr in self.yrs:
            (descr, data) = self.merge(csvlist[yr])
            for row in data:
                row[0] = datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S+00:00")
                alldata.append(row)
                pass
            pass
        descr[0] = ("Date","datetime")
        for i in range(1,1+len(descr[1:])):
            descr[i]=(descr[i],"number")
            pass
        table = DataTable(descr, alldata)
        expires = datetime.now() + timedelta(days=1)
        self.response.headers['Content-type'] = 'text/plain'
        self.response.headers['Expires'] = expires.strftime(
            '%a, %d %b %Y %H:%M:%S %Z')
        self.response.headers['Cache-control'] = 'public'
        self.response.out.write(table.ToResponse(tqx=tqx))
        return
        
    # Merge combines all second columns with first column of first dataset
    # This assumes that all datasets are of same length and column 1 of each row
    # is the same for all datasets.  
    # Could test for this, but the intended use of this code is pretty narrow.
    # A low cost check would be to ensure first column of first row of all datsets
    # is the same,  i.e. all start at same time, and all have same number or rows.
    def merge(self, csvs):
        # Parse the CSV content
        dsets = []
        for data in csvs:
            src = StringIO.StringIO(data)
            #src.readline()
            content = csv.reader(src) #, quoting=csv.QUOTE_NONNUMERIC)
            row = content.next()
            # get column headers and remove quotes
            data = [[row[0].strip(' "'),row[1].strip(' "')]]
            for row in content:
                row[1] = Decimal(row[1].strip())
                data.append(row)
                pass
            dsets.append(data)
            pass
        # Now merge the data
        merged = dsets[0]
        cols = len(dsets) - 1
        for col in range(cols):
            i = 0
            for row in merged:
                row.append(dsets[col+1][i][1])
                i += 1
                pass
            pass
        return (merged[0],merged[1:])

    def getArgs(self):
        global fi, start, end, rean
        # treat all as strings
        # Trailing ';' from google charts toolbar messes
        # with google gviz_api
        self.tqx=self.request.get("tqx").strip(';')
        lat = self.request.get("lat")
        lng = self.request.get("lng")
        # These x,y coords are only good for
        # 192 x 94 regular global grids
        (self.x,self.y) = toXY(float(lat), float(lng))
        fi = self.request.get("fi")
        start = self.request.get("start")
        end = self.request.get("end")
        rean = self.request.get("rean")
        if rean == None: rean = "20cr"
        return

    def download(self, host):
        global csvlist
        csvlist = {}
        rpcs = []
        (yr0,mo0,dy0) = start.split('-')
        (yr1,mo1,dy1) = end.split('-')
        self.yrs = range(int(yr0),int(yr1)+1)
        for yr in self.yrs:
            csvlist[yr] = []
            for q in fi.split(','):
                rpc = urlfetch.create_rpc(deadline=50) 
                # 60 secs is max, 5 secs is default see 
                # http://code.google.com/appengine/docs/python/urlfetch/asynchronousrequests.html
                rpc.callback = create_callback(rpc, yr)
                url =  host + "/metseries?tqx=out:csv&rean=%s&x=%s&y=%s&fi=%s&yr0=%s" % (rean,self.x,self.y,q,yr)
                urlfetch.make_fetch_call(rpc, url)
                rpcs.append(rpc)
                pass
            pass
        # Finish all RPCs, and let callbacks process the results.
        for rpc in rpcs:
            rpc.wait()
            pass
        
#
# Run the CGI handler.  Share this with other scripts if there's more going on than
# the above.

import wsgiref.handlers

application = webapp.WSGIApplication([  
  ('/getmetdata', GetMetData),
], debug=True)

def main():
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
