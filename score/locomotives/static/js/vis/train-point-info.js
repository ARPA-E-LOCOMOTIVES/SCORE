class TrainPointInfo{

  constructor() {}

  get_point_html(data_ref, idx){

    var titles = [];
    for (var key in data_ref ) {
        titles.push(key);
    }

    var html = '<br>'
    for (var i = 0; i < titles.length; i++){
      if (titles[i] != "route_id" && titles[i] != "consist_id" && titles[i] != "route_name" && titles[i] != "consist_name"){
          const data_type = isNaN(data_ref[titles[i]][idx]);
          if (data_type){
            html += '<h4>' + titles[i] +  '=' + data_ref[titles[i]][idx] + "</h4>";
          } else {
            html += '<h4>' + titles[i] +  '=' + d3.format(".1f")(data_ref[titles[i]][idx]) + "</h4>";
          }
      }
    }

    for (var i = 0; i < titles.length; i++){
      if (titles[i] != "route_id" && titles[i] != "consist_id" ){
        if (titles[i] == "route_name"){
          html += '<h4>Route :' + '<a href= "/route-info/' + data_ref['route_id'][idx] + '" target="_blank">' + data_ref[titles[i]][idx] +'</a></h4>';
        } else if (titles[i] == "consist_name"){
          html += '<h4>Consist :' + '<a href= "/consist-info/' + data_ref['consist_id'][idx] + '" target="_blank">' + data_ref[titles[i]][idx] +'</a></h4>';
        }
      }
    }

    return html;

  }

}
