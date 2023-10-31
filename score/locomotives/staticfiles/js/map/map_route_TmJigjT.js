class MapRoute {

  constructor(routeLines, routeDistances=undefined) {

    this.routeLines = routeLines;
    this.routeDistances = routeDistances;

    var open_railway_map_layer = new L.TileLayer('http://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png',
    {
      attribution: '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a>, Style: <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA 2.0</a> <a href="http://www.openrailwaymap.org/">OpenRailwayMap</a> and OpenStreetMap',
      minZoom: 2,
      maxZoom: 19,
      tileSize: 256,
      opacity: 0.4
    });

    // var google_map_layer = new L.tileLayer.grayscale('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',{
    //     maxZoom: 19,
    //     subdomains:['mt0','mt1','mt2','mt3']
    // });

    var google_map_layer = new L.tileLayer('http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}',{
        maxZoom: 19,
        subdomains:['mt0','mt1','mt2','mt3']
    });

    //var open_street_map_layer = new L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    //	maxZoom: 19,
    //	attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    //})

    this.map = new L.Map("map", {
      center: new L.LatLng(40.0, -88.86),
      zoom: 4,
      layers: [google_map_layer, open_railway_map_layer]
    });

    //var linestyle = {
    //    "color": "#0044ff",
    //};

    this.route_layer = L.geoJSON(routeLines).addTo(this.map);
    this.point_layer = undefined;

  }

  add_listener(obj){}

  set_brush(min, max){
    this.map.removeLayer(this.route_layer);
    var brushed_layer = [];
    for (var i = 0 ; i < this.routeDistances.length; i++){
      if (this.routeDistances[i] >= min && this.routeDistances[i] <= max){
        brushed_layer.push(this.routeLines[i]);
      }
    }
    this.route_layer = L.geoJSON(brushed_layer).addTo(this.map);
  }

  set_vertical_line(x0, dist){

    if (this.point_layer != undefined){
      this.map.removeLayer(this.point_layer);
    }

    var point_line = [];
    for (var i = 0 ; i < this.routeDistances.length - 1; i++){
      if (this.routeDistances[i] <= dist  && this.routeDistances[i + 1] >= dist){
        point_line.push(this.routeLines[i]);
      }
    }
    var myStyle = {
        "color": "#ff7800",
        "weight": 10,
        "opacity": 1.0
    };
    this.point_layer = L.geoJSON(point_line, {style: myStyle}).addTo(this.map);
  }


}
