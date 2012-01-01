#!/bin/bash
#
# If table isn't public then authentication is required.  
# See http://code.google.com/apis/fusiontables/docs/samples/curl.html for how.
#
# For info on Fusion Tables SQL see
# http://code.google.com/apis/fusiontables/docs/developers_reference.html#Select

function FusionTableQuery() {
  local sql=$1
  #curl -L -s --data-urlencode sql="$sql" https://www.google.com/fusiontables/api/query
  curl -L -s --data-urlencode sql="$sql" http://www.google.com/fusiontables/api/query
}

FusionTableQuery "SELECT * FROM 2358653 WHERE ST_INTERSECTS(centroid_x, RECTANGLE(LATLNG(8.39,74.31),LATLNG(12.39,78.31)))"
