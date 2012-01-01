      var map = new OpenLayers.Map('map', {
	  controls : [
      new OpenLayers.Control.LayerSwitcher(),
      new OpenLayers.Control.PanZoomBar(),
      new OpenLayers.Control.ZoomToMaxExtent(),
      new OpenLayers.Control.ScaleLine(),
      new OpenLayers.Control.ArgParser(),
      new OpenLayers.Control.Attribution(),
      new OpenLayers.Control.Permalink(),
			new OpenLayers.Control.Navigation(),
    ]
  });

	    OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
      defaultHandlerOptions: {
        'single': true,
        'double': false,
        'pixelTolerance': 0,
        'stopSingle': false,
        'stopDouble': false
      },

      initialize: function(options) {
        this.handlerOptions = OpenLayers.Util.extend(
          {}, this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
          this, arguments
        ); 
        this.handler = new OpenLayers.Handler.Click(
          this, {
              'click': this.trigger
          }, this.handlerOptions
        );
      }
    });          

    var gotoLocationControl = new OpenLayers.Control.Click({
      trigger: function(e) {
        var lonlat = map.getLonLatFromViewPortPx(e.xy);
        lonlat = lonlat.transform(map.getProjectionObject(), proj);
        window.location = "/location/?lon=" + lonlat.lon + "&lat=" + lonlat.lat
      },
      displayClass: 'olControlGotoLocationControl'
    });

    var myNavToolbar = new OpenLayers.Control.Panel({ displayClass: 'olControlMyNavToolbar' });
    myNavToolbar.addControls([
      new OpenLayers.Control.Navigation(),
      gotoLocationControl
    ]);
    map.addControl(myNavToolbar);

	  
  var proj = new OpenLayers.Projection("EPSG:4326");
  var gphy = new OpenLayers.Layer.Google(
    "Google Physical",
    {type: google.maps.MapTypeId.TERRAIN}
  );
  var ghyb = new OpenLayers.Layer.Google(
    "Google Hybrid",
    {type: google.maps.MapTypeId.HYBRID}
  );
  var gsat = new OpenLayers.Layer.Google(
    "Google Satellite",
    {type: google.maps.MapTypeId.SATELLITE}
  );
  var grid = new OpenLayers.Layer.Vector(
		"Data Region"
  );

	map.addLayers([gphy, gsat, ghyb, grid]);
	//var lonlat = new OpenLayers.LonLat(-138026.1791359, 6754611.1150493);
  var lonlat = new OpenLayers.LonLat(0, 0);
  map.setCenter(lonlat, 2);
