// line plot based on d3
//
// assume a data object , where the object is a list of dictionaries, where the dictionary
// include a x value, and all other keys will be drawn as lines. An optional color_map variable
// can be included to color the lines based on the key value
class d3LinePlot {

  constructor(data, div_id, color_map=undefined) {

    // data objects, assume one of the keys is 'x' for the the x-axis
    this.data = data;
    this.data_keys = [];
    this.x_values = [];
    this.y_values = [];

    // maps the line color to the key
    this.color_map = color_map;

    this.div_id = div_id;

    // min and max bounds of the x and y axis
    this.minX = 100000000000;
    this.maxX = -100000000000;
    this.minY = 100000000000;
    this.maxY = -100000000000;
    this.line_precision = 1;

    // width and height of the plot
    this.w = 1200;
    this.h = 200;

    // margin to show or not show a legend (200), or add as a buffer to line up with other plots
    this.right_margin = 30;

    // array to store plot listeners
    this.listeners = [];

    // x and y axes label
    this.x_title = "";
    this.y_title = "";

    // store all titles or keys in the data
    for (var key in data[0]){
      this.data_keys.push(key);
    }

    // iterate through the rows to get the min and max values for the x and y axis
    for (var row in data){
      for (var key in data[row]){
        var v = data[row][key];
        if (key == 'x'){
          this.minX = Math.min(this.minX, v);
          this.maxX = Math.max(this.maxX, v);
          this.x_values.push(v);
        } else {
          this.minY = Math.min(this.minY, v);
          this.maxY = Math.max(this.maxY, v);
          if (this.data_keys.length == 2){
            this.y_values.push(v);
          }
        }
      }
    }

    if (this.maxY - this.minY < 1)
      this.line_precision = 4;

  }

  // sets the size of the plot
  set_size(w, h){
    this.w = w;
    this.h = h;
  }

  // sets the x and y axis
  set_titles(x_title, y_title){
    this.x_title = x_title;
    this.y_title = y_title;
  }

  // includes the legend area, it will show the legend labels if a color_map is passed in the constructor
  include_legend_area(){
    this.right_margin = 200;
  }

  // add plot listeners
  add_listener(listener){
    this.listeners.push(listener);
  }

  set_y_range(min_value, max_value){
    this.minY = min_value;
    this.maxY = max_value;
  }

  // method to create the plot
  draw(){

    // set the dimensions and margins of the graph
    var margin = {top: 10, right: this.right_margin, bottom: 30, left: 60},
        width = this.w - margin.left - margin.right,
        height = this.h - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select("#" + this.div_id)
      .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .on('mousemove', mousemove)
      .append("g")
        .attr("transform",
              "translate(" + margin.left + "," + margin.top + ")");

    // set x properties
    var x = d3.scaleLinear()
      .domain([this.minX, this.maxX])
      .range([ 0, width ]);

    // set x axis properties
    var xAxis = svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x));

    // set y properties
    var y = d3.scaleLinear()
      .domain([this.minY, this.maxY])
      .range([ height, 0 ]);


    // add y axis
    svg.append("g")
      .call(d3.axisLeft(y).ticks(4));

    // initialize line data for each key besides x
    var line_data = {};
    for (var key_id in this.data_keys){
      var key = this.data_keys[key_id];
      if (key != "x"){
        line_data[key] = [];
      }
    }

    // set the line data for each key, where the x key is the x value
    for (var row in this.data){
      for (var key_id in this.data_keys){
        var key = this.data_keys[key_id];
        if (key != "x"){
          line_data[key].push({x : this.data[row]['x'], value : this.data[row][key]});
        }
      }
    }

    // add legend
    if (this.right_margin == 200){
      var counter = 0;
      for (var key in this.color_map){
        svg.append("rect").attr("x",width + 10).attr("y", margin.top + counter*20).attr("width", 8).attr("height", 8).style("fill", this.color_map[key])
        svg.append("text").attr("x",width + 24).attr("y", margin.top + counter*20 + 4).text(key).style("font-size", "12px").attr("alignment-baseline","middle")
        counter += 1;
      }
    }

    // add x label
    svg.append("text")
     .attr("transform", "translate(" + (width/2 - 6*this.x_title.length/2) + "," + (height + 3*margin.bottom/4) + ")")
     .attr("dy", ".35em")
     .attr("text-anchor", "start")
     .style("fill", "black")
     .text(this.x_title);

   // add y label
   svg.append("text")
     .attr("transform", "translate(" + (-3*margin.left/4) + "," + (margin.top + height/2 + 6*this.y_title.length/2) + "),rotate(-90)")
     .attr("dy", ".35em")
     .attr("text-anchor", "start")
     .style("fill", "black")
     .text(this.y_title);

    // create the d3 line function, to map the x to x and the value to y
    var line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.value))

    // Add a clipPath: everything out of this area won't be drawn.
    var clip = svg.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("width", width )
        .attr("height", height )
        .attr("x", 0)
        .attr("y", 0);

    // Create the line variable: where both the line and the brush take place
    var line_brush = svg.append('g')
       .attr("clip-path", "url(#clip)")

    var vertical = line_brush
      .append("line")
      .attr("x1",0)
      .attr("y1",0)
      .attr("x2",0)
      .attr("y2",height)
      .style("stroke", "black")
      .attr('class', 'verticalLine');
    this.vertical = vertical;

    var circle = line_brush
      .append('circle')
      .style("stroke", "gray")
      .attr("r", 3)
      .attr("cx", 0)
      .attr("cy", 0);
    this.circle = circle;

    this.info_label = line_brush.append("text")
        .attr("transform", "translate(0,0)")
        .attr("font-size", "1em")
        .attr("color", "black")
        .text("test");

    // Add x zoom in the plot
    var brush = d3.brushX()
        .extent( [ [0,0], [width,height] ] )
        .on("end", updateChart);

    // Add the brushing
    svg.append("g")
       .attr("class", "brush")
       .call(brush);



    // set object variables for brush updates
    this.x = x;
    this.y = y;
    this.xAxis = xAxis;
    this.line_data = line_data;
    this.line = line;
    this.line_brush = line_brush;
    this.width = width;
    this.set_brush(this.minX, this.maxX);

    var idleTimeout
        function idled() { idleTimeout = null; }

    // set variable for the below zoom update function
    var minX = this.minX;
    var maxX = this.maxX;
    var me = this;

    function mousemove(){
      var x0 = d3.mouse(this)[0] - margin.left;
      if (x0 >= 0 && x0 <= width){
        me.set_vertical_line(x0, x.invert(x0));
        me.vertical_line_update(x0);
      }
    }

    // A function that update the chart for given boundaries
    function updateChart() {

      // What are the selected boundaries?
      var extent = d3.event.selection

      // If no selection, back to initial coordinate. Otherwise, update X axis domain
      if(!extent){
        if (!idleTimeout) return idleTimeout = setTimeout(idled, 350); // This allows to wait a little bit
        x.domain([ minX, maxX])
        me.brush_updated(minX, maxX);
      }else{
        x.domain([ x.invert(extent[0]), x.invert(extent[1]) ]);
        me.brush_updated(x.domain()[0], x.domain()[1]);
        svg.select(".brush").call(brush.move, null) // This remove the grey brush area as soon as the selection has been done
      }
      me.set_brush(x.domain()[0],x.domain()[1]);

    }


  }

  set_brush(min, max){

    // set the range
    this.x.domain([ min, max ]);

    // update the axis
    this.xAxis.transition().duration(100).call(d3.axisBottom(this.x))

    // remove all existing lines
    this.line_brush.selectAll("path").remove();

    // reference variables for internal functions below
    var color_map = this.color_map;
    var line_data = this.line_data;
    var line = this.line;

    // for each key that is not equal to x
    for (var key_id in this.data_keys){
      var key = this.data_keys[key_id];
      if (key != "x"){

          // add a line path
          var line_path = this.line_brush.append("path")
            .datum(this.data)
            .attr("fill", "none")
            .attr("stroke",  function(d) {
              if (color_map == undefined){
                return "steelblue";
              } else {
                return color_map[key];
              }
            })
            .attr("stroke-width", 1.5)
            .attr("d", line(line_data[key]))
      }
    }

  }

  // call this method to update other listeners bounds
  brush_updated(min, max){
    for (var i = 0; i < this.listeners.length; i++){
      this.listeners[i].set_brush(min, max);
    }
  }


  set_vertical_line(x0, dist){
    this.vertical.attr("transform", "translate(" + Math.min(x0,this.width) + ",0)");
    if (this.y_values.length > 0){
      var i = d3.bisect(this.x_values, dist);
      var i_before = Math.max(0, i - 1);
      var prop = (dist - this.x_values[i_before])/(this.x_values[i] - this.x_values[i_before]);
      var actual_y_value = this.y_values[i_before] + prop*(this.y_values[i] - this.y_values[i_before]);
      var x_point = this.x(dist);
      var y_point = this.y(actual_y_value);
      this.circle.attr("transform", "translate(" + x_point + "," + y_point + ")");
      var x_point_label = Math.max(0, x_point);
      x_point_label = Math.min(x_point_label, this.width - 40);
      //var y_point_label = Math.max(12, y_point);
      var y_point_label = 12;
      this.info_label.attr("transform", "translate(" + (x_point_label + 4) + "," + y_point_label + ")");
      if (this.y_values[i] != undefined){
        this.info_label.text(actual_y_value.toFixed(this.line_precision));
      }
    }
  }

  vertical_line_update(x0){
    for (var i = 0; i < this.listeners.length; i++){
      this.listeners[i].set_vertical_line(x0, this.x.invert(x0));
    }
  }

}
