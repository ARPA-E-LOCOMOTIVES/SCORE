class d3ScatterPlot {

  constructor() {
    this.dataS = undefined;
    this.dataC = undefined;
    this.custom_point_display = undefined;
    this.categorial_values = [undefined, undefined, undefined, undefined];
    this.counter = 0;
    this.point_size = 8;
  }

  set_data_model(data_model){
    this.data_model = data_model;
  }

  set_data_x(title){
    this.titleX = title;
    this.set_plot_label_x(title);
  }

  set_data_y(title){
    this.titleY = title;
    this.set_plot_label_y(title);
  }

  set_scale(title){
    this.titleS = title;
  }

  set_constant_scale(){
    this.titleS = undefined;
  }

  set_color(title){
    this.titleC = title;
    var min_value = this.data_model.get_min_values()[title];
    var max_value = this.data_model.get_max_values()[title];
    if (isNaN(min_value)){
      return [min_value, max_value];
    } else {
      return [min_value.toFixed(2), max_value.toFixed(2)];
    }

  }

  set_constant_color(){
    this.titleC = undefined;
  }

  set_div(div_id){
    this.div_id = div_id;
  }

  set_point_div(point_div_id){
    this.point_div_id = point_div_id;
  }

  set_size(width, height){
    this.width = width;
    this.height = height;
  }

  set_plot_label_x(x_label){
    this.x_label = x_label;
  }

  set_plot_label_y(y_label){
    this.y_label = y_label;
  }

  set_custom_point(custom_point_display){
    this.custom_point_display = custom_point_display;
  }

  update_filter(){
    this.refresh();
  }

  set_point_size(point_size){
    this.point_size = point_size;
  }

  refresh(){

    this.scatter_data = [];
    this.brush_indices = [];
    this.categorial_values = [undefined, undefined, undefined, undefined];
    var dataX = this.data_model.get_data()[this.titleX];
    if (isNaN(dataX[0])){
      this.categorial_values[0] = Array.from(new Set(dataX));
    }
    var dataY = this.data_model.get_data()[this.titleY];
    if (isNaN(dataY[0])){
      this.categorial_values[1] = Array.from(new Set(dataY));
    }
    // if color is set
    if(this.titleC != undefined){
      var dataC = this.data_model.get_data()[this.titleC];
      if (isNaN(dataC[0])){
        this.categorial_values[2] = Array.from(new Set(dataC));
      }
    }
    // if size is set
    if(this.titleS != undefined){
      var dataS = this.data_model.get_data()[this.titleS];
      if (isNaN(dataS[0])){
        this.categorial_values[3] = Array.from(new Set(dataS));
      }
    }

    for(var i = 0 ; i < dataX.length; i++){
      var data_row = [dataX[i], dataY[i]]
      if(this.titleC != undefined){
        var dataC = this.data_model.get_data()[this.titleC];
        if(isNaN(dataC[0])){
          data_row.push(1.0*this.categorial_values[2].indexOf(dataC[i])/this.categorial_values[2].length);
        } else {
          data_row.push((dataC[i] - this.data_model.get_min_values()[this.titleC])/(this.data_model.get_max_values()[this.titleC]- this.data_model.get_min_values()[this.titleC]));
        }
      } else {
        data_row.push(0);
      }
      if(this.titleS != undefined){
        var dataS = this.data_model.get_data()[this.titleS];
        if(isNaN(dataS[0])){
          data_row.push(1.0*this.categorial_values[3].indexOf(dataS[i])/this.categorial_values[3].length);
        } else {
          data_row.push((dataS[i] - this.data_model.get_min_values()[this.titleS])/(this.data_model.get_max_values()[this.titleS]- this.data_model.get_min_values()[this.titleS]));
        }
      } else {
        data_row.push(0);
      }

      // check filter
      var visible = true;
      for (var j = 0; j < this.data_model.get_titles().length; j++) {
        var key = this.data_model.get_titles()[j];
        var categorical = this.data_model.is_catergorical(key);
        if (!categorical){
          // some weird tolerance issue is occurring
          if (this.data_model.get_data()[key][i] < this.data_model.get_min_brush_values()[key] ){
            visible = false;
          }
          if (this.data_model.get_data()[key][i] > this.data_model.get_max_brush_values()[key] ){
            visible = false;
          }
        } else {
          var token = this.data_model.get_data()[key][i];
          var token_visibible = this.data_model.is_catergorical_token_visible(key, token);
          if (!token_visibible){
            visible = false;
          }
        }
      }

      if (visible){
        this.scatter_data.push(data_row);
        this.brush_indices.push(i);
      }

    }

    // reference variable for internal function calls
    var data_ref = this.data_model.get_data();
    var titles_ref = this.data_model.get_titles();
    var custom_point_display = this.custom_point_display;
    var types_ref = [this.categorial_values[0] != undefined,this.categorial_values[1] != undefined] ;
    var brush_indices = this.brush_indices;

    function get_point_html(id){
      idx = brush_indices[id];
      if (custom_point_display == undefined){
        var html = '<h4>Selected</h4></br>'
        for (var i = 0; i < titles_ref.length; i++){
           html += '<h4>' + titles_ref[i] +  '=' + d3.format(".1f")(data_ref[titles_ref[i]][idx]) + "</h4>";
        }
        return html;
      } else {
        return custom_point_display.get_point_html(data_ref, idx)
      }
    }

    //d3.select('svg').remove();
    d3.select("#" + this.div_id).selectAll('*').remove();
    d3.select("#" + this.point_div_id).selectAll('*').remove();

    var div = d3.select("body").append("div")
       .attr("class", "tooltip")
       .style("opacity", 0);

    var point_details = d3.select("#" + this.point_div_id).append("div")
       .style("opacity", 0)
       .style("color",'#000000');

  //  var margin = {top: 40, right: 30, bottom: 100, left: 100},
  //    width = this.width - margin.left - margin.right,
  //    height = this.height - margin.top - margin.bottom;

      var margin = {top: 10, right: 20, bottom: 40, left: 100},
        width = this.width - margin.left - margin.right,
        height = this.height - margin.top - margin.bottom;

   // append the svg object to the body of the page
   var svg = d3.select("#" + this.div_id)
     .append("svg")
       .attr("width", width + margin.left + margin.right)
       .attr("height", height + margin.top + margin.bottom)
     .append("g")
       .attr("transform",
             "translate(" + margin.left + "," + margin.top + ")");

   // Add X axis
   if (types_ref[0]){
     var xScale = d3.scalePoint()
       .domain(this.categorial_values[0])
       .range([ 0, width ]);
   } else {
     var xScale = d3.scaleLinear()
       .domain([0, this.data_model.get_max_values()[this.titleX]])
       .range([ 0, width ]);
   }

   // Add Y axis
   if (types_ref[1]){
     var yScale = d3.scalePoint()
       .domain(this.categorial_values[1])
       .range([ height, 0 ]);
   } else {
     var yScale = d3.scaleLinear()
       .domain([0, this.data_model.get_max_values()[this.titleY]])
       .range([ height, 0]);
   }

   var xAxisGrid = d3.axisBottom(xScale).tickSize(-height).tickFormat('').ticks(5);
   svg.append('g')
      .attr("transform", "translate(0," + height + ")")
      .attr('class', 'x axis-grid')
      .call(xAxisGrid);

   var yAxisGrid = d3.axisLeft(yScale).tickSize(-width).tickFormat('').ticks(5);
      svg.append('g')
      .attr('class', 'y axis-grid')
      .call(yAxisGrid);

  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .attr("class", "axis")
    .call(d3.axisBottom(xScale).ticks(5));

  svg.append("g")
     .attr("class", "axis")
     .call(d3.axisLeft(yScale).ticks(5));

    // title
   svg.append('text').attr('x', width/2).attr('y', -20).attr('text-anchor', 'middle')
     .style('font-family', 'Helvetica').style('font-size', 18).text(this.title);

   // x label
   svg.append('text').attr('x', width/2).attr('y', height + 32).attr('text-anchor', 'middle')
     .style('font-family', 'Helvetica').style('font-size', 18).text(this.x_label);

   // y label
   svg.append('text').attr('text-anchor', 'middle').attr('transform', 'translate(-60,' + height/2 + ')rotate(-90)')
     .style('font-family', 'Helvetica').style('font-size', 18).text(this.y_label);

   var point_size = this.point_size;

   // Add dots
   svg.append('g')
     .selectAll("dot")
     .data(this.scatter_data)
     .enter()
     .append("circle")
       .attr("cx", function (d) { return xScale(d[0]); } )
       .attr("cy", function (d) { return yScale(d[1]); } )
       .attr("r", function (d) { return point_size + point_size*d[3]; } )
       .attr('fill',  function (d) { return d3.interpolateCool(d[2]); }).on("click", function(d, i){
         point_details.transition().duration(100).style("opacity", 1);
         point_details.html(get_point_html(i))
                    .style("left", (0) + "px")
                    .style("top", (400) + "px");
      	}).on('mouseover', function (d, i) {
           point_details.transition().duration(100).style("opacity", 0);
           d3.select(this).transition().duration('100').attr("r", 12 + 8*d[3]);
           //Makes div appear
           div.transition().duration(100).style("opacity", 1);

           var x_tooltip_str = d[0]
           if (!types_ref[0])
             x_tooltip_str = d3.format(".0f")(d[0]);

           var y_tooltip_str = d[1]
           if (!types_ref[1])
             y_tooltip_str = d3.format(".0f")(d[1]);

           div.html(
             "<h4>x=" + x_tooltip_str
                + ",y=" + y_tooltip_str + "</h4>")
             .style("left", (d3.event.pageX + 10) + "px")
             .style("top", (d3.event.pageY - 15) + "px");
       }).on('mouseout', function (d, i) {
           //d3.select(this).transition().duration('200').attr("r", 8);
           d3.select(this).transition().duration('400').attr("r", 8 + 8*d[3]);
           //Makes div appear
           div.transition().duration(400).style("opacity", 0);
       });

  }

}
