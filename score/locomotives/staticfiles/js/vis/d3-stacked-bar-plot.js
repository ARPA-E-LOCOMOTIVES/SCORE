// Copyright (c) 2022, The Pennsylvania State University
// All rights reserved.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
// IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
// FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

// bar plot based on d3
//
// assume a data object , where the object is a list of dictionaries, where the dictionary
// includes an x value, and total is assumed to be the height of the bars. An optional color_map variable
// can be included to color the bars based on the total value
class d3StackedBarPlot {

  constructor(data, div_id, color_map=undefined, user_min=undefined, user_max=undefined) {

    // maps the line color to the key
    this.color_map = color_map;

    this.div_id = div_id;

    // min and max bounds of the x and y axis
    this.minX = 0;
    this.maxX = -100000000000;
    this.minY = 0;
    this.maxY = -100000000000;
    this.user_min = user_min;
    this.user_max = user_max;

    // width and height of the plot
    this.w = 1200;
    this.h = 200;

    // x and y axis labels
    this.x_title = "";
    this.y_title = "";

    // array to store plot listeners
    this.listeners = [];

    // maps the color of bar to a plot legend label, since bar color is based on height and color_map,
    // this map is needed to display descriptive labels for the legend
    this.legend = {};
    this.neg_bar_graph = undefined;

    this.right_margin = 30;

    // get all data keys
    this.data_keys = [];
    for (var key in data[0]){
      this.data_keys.push(key);
    }

    // iterate through the rows to get the min and max values for the x and y axis
    var counter = 0;
    for (var row in data){
      var total_row_stack = 0;
      for (var key in data[row]){
        var v = data[row][key];
        if (key == 'x'){
          this.maxX = Math.max(v,this.maxX);
        } else {
          total_row_stack += v;
        }
      }
      this.maxY = Math.max(total_row_stack,this.maxY);

      // append the change in x distance for each segment
      if (counter < data.length - 1){
        data[row]['dx'] = data[counter + 1]['x'] - data[counter]['x'];
      } else {
        data[row]['dx'] = data[counter]['dx'];
      }

      counter += 1;

    }

    if (this.user_max != undefined)
      this.maxY = Math.max(this.maxY, this.user_max); 

    // data objects, assume one of the keys is 'x' for the the x-axis
    this.data = data;

  }

  assign_negative_bars(negative_data){
    // iterate through the rows to get the min and max values for the x and y axis
    if (negative_data != undefined){

      this.neg_data_keys = [];
      for (var key in negative_data[0]){
        this.neg_data_keys.push(key);
      }

      var counter = 0;
      for (var row in negative_data){
        var total_row_stack = 0;
        for (var key in negative_data[row]){
          var v = negative_data[row][key];
          if (key == 'x'){
            this.maxX = Math.max(v,this.maxX);
          } else {
            total_row_stack += v;
          }
        }
        this.minY = Math.min(total_row_stack,this.minY);

        // append the change in x distance for each segment
        if (counter < negative_data.length - 1){
          negative_data[row]['dx'] = negative_data[counter + 1]['x'] - negative_data[counter]['x'];
        } else {
          negative_data[row]['dx'] = negative_data[counter]['dx'];
        }

        counter += 1;

      }

      // user defined limit
      if (this.user_min != undefined)
        this.minY = Math.min(this.minY, this.user_min);     

    }

    this.negative_data = negative_data;
  }

  // sets the size of the plot
  set_size(w, h){
    this.w = w;
    this.h = h;
  }

  // includes the legend area, it will show the legend labels if a color_map is passed in the constructor
  include_legend_area(){
    this.right_margin = 200;
  }

  // sets the axis labels
  set_titles(x_title, y_title){
    this.x_title = x_title;
    this.y_title = y_title;
  }

  // set the legend map
  set_legend(legend){
    this.legend = legend;
  }

  // add listener for this plot
  add_listener(listener){
    this.listeners.push(listener);
  }

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

    // set the x axis proerties
    var x = d3.scaleLinear()
      .domain([this.minX, this.maxX])
      .range([ 0, width ]);

    // add the x axis
    var xAxis = svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x));

    // set the y axis properties
    var y = d3.scaleLinear()
      .domain([this.minY, this.maxY])
      .range([ height, 0 ]);

    // add the y axis
    var yAxis = svg.append("g")
      .call(d3.axisLeft(y).ticks(4));

    // get all sub , remove x and dx
    var subgroups = this.data_keys.slice(1);

    // stack the data
    var stackedData = d3.stack()
        .keys(subgroups)
        (this.data)

    // Add a clipPath: everything out of this area won't be drawn.
    var clip = svg.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("width", width )
        .attr("height", height )
        .attr("x", 0)
        .attr("y", 0);

    // Create the bar zoom variable: where both the bars and brush take place
    var bar_brush = svg.append('g')
        .attr("clip-path", "url(#clip)")

    // Add x axis zooming
    var brush = d3.brushX()
        .extent( [ [0,0], [width,height]] )
        .on("end", updateChart);

    // Add the zoom capability
    svg.append("g")
        .attr("class", "brush")
        .call(brush);

    var idleTimeout
       function idled() { idleTimeout = null; }

    // setup bar graph
    var bar_graph = bar_brush.selectAll("rect")
      .data(stackedData)
      .enter();

    // check for negative bars
    if (this.negative_data != undefined){

      // get all sub , remove x and dx
      var negsubgroups = this.neg_data_keys.slice(1);

      // stack the data
      var negstackedData = d3.stack()
          .keys(negsubgroups)
          (this.negative_data)

      var neg_bar_graph = bar_brush.selectAll("rect")
        .data(negstackedData)
        .enter();
      this.neg_bar_graph = neg_bar_graph;

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

    // add legend
    if (this.right_margin == 200){
      var counter = 0;
      for (var key in this.color_map){
        svg.append("rect").attr("x",width + 10).attr("y", margin.top + counter*20).attr("width", 8).attr("height", 8).style("fill", this.color_map[key])
        svg.append("text").attr("x",width + 24).attr("y", margin.top + counter*20 + 4).text(key).style("font-size", "12px").attr("alignment-baseline","middle")
        counter += 1;
      }
    }

    var vertical = bar_brush
      .append("line")
      .attr("x1",0)
      .attr("y1",0)
      .attr("x2",0)
      .attr("y2",height)
      .style("stroke", "black")
      .attr('class', 'verticalLine');

    this.vertical = vertical;

    // set variables for brush for listeners
    this.bar_graph = bar_graph;
    this.bar_brush = bar_brush;
    this.width = width;
    this.x = x;
    this.y = y;
    this.xAxis = xAxis;
    this.subgroups = subgroups;

    this.set_brush(this.minX, this.maxX);

    // set variables for self brush
    var minX = this.minX;
    var maxX = this.maxX;
    var bar_width_of_mile = width/(x.domain()[1] - x.domain()[0]);
    var color_map = this.color_map;
    var me = this;

    function mousemove(){
      var x0 = d3.mouse(this)[0] - margin.left;
      if (x0 >= 0 && x0 <= width){
        me.set_vertical_line(x0);
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
          x.domain([ minX, maxX]);
          me.brush_updated(minX,maxX);
        }else{
          x.domain([ x.invert(extent[0]), x.invert(extent[1]) ]);
          me.brush_updated(x.domain()[0],x.domain()[1]);
          svg.select(".brush").call(brush.move, null) // This remove the grey brush area as soon as the selection has been done
        }

        me.set_brush(x.domain()[0],x.domain()[1]);

      }

  }

  // updates the bar plot based on the x axis range of values
  set_brush(min, max){

    // update x axis
    this.x.domain([ min, max ]);
    this.xAxis.transition().duration(100).call(d3.axisBottom(this.x))

    // remove all bars
    this.bar_brush.selectAll("rect").remove();

    // set variables for internal functions
    var color_map = this.color_map;
    var bar_width_of_mile = this.width/(this.x.domain()[1] - this.x.domain()[0]);
    var x = this.x;
    var y = this.y;

    // add bars based on x axis bounds
    this.bar_graph
      .append("g")
      .attr("fill", function(d) { return color_map[d.key]; })
      .selectAll("rect")
      // enter a second time = loop subgroup per subgroup to add all rectangles
      .data(function(d) { return d; })
      .enter().append("rect")
        .attr("x", function(d) { return x(d.data.x); })
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function(d) { return y(d[0]) - y(d[1]); })
        .attr("width", function(d) { return bar_width_of_mile*d.data.dx || 0; })

    // check for negative bars
    if (this.neg_bar_graph != undefined){
      // add bars based on x axis bounds
      this.neg_bar_graph
        .append("g")
        .attr("fill", function(d) { return color_map[d.key]; })
        .selectAll("rect")
        // enter a second time = loop subgroup per subgroup to add all rectangles
        .data(function(d) { return d; })
        .enter().append("rect")
          .attr("x", function(d) { return x(d.data.x); })
          .attr("y", function(d) { return y(d[0]); })
          .attr("height", function(d) { return y(d[1]) - y(d[0]); })
          .attr("width", function(d) { return bar_width_of_mile*d.data.dx || 0; })
    }

  }

  // call this method to update other listeners bounds
  brush_updated(min, max){
    for (var i = 0; i < this.listeners.length; i++){
      this.listeners[i].set_brush(min, max);
    }
  }

  set_vertical_line(x0, dist){
    this.vertical.attr("transform",  "translate(" + x0 + ",0)");
  }

  vertical_line_update(x0){
    for (var i = 0; i < this.listeners.length; i++){
      this.listeners[i].set_vertical_line(x0, this.x.invert(x0));
    }
  }


}
