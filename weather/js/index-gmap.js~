

  var map;
  var layer;

  function drawMap(){
      var tableId = "2358653";
      layer = new google.maps.FusionTablesLayer(Number(tableId),{suppressInfoWindows:true});
      layer.setMap(map);
      google.maps.event.addListener(layer, 'click', function(arg) {
	  window.location = "/location.html?latlng=" + arg.latLng;
      });
  }

  function initialize() {
    var my_centre = new google.maps.LatLng(0,0);
    map = new google.maps.Map(document.getElementById('mapc'), {
      center: my_centre, zoom: 2,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    });
    drawMap();
  }

  initialize();
