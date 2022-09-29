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

class d3BarPlot {

  constructor(data, div_id, color_map=undefined) {

    // data objects, assume one of the keys is 'x' for the the x-axis
    this.data = data;

    // maps the line color to the key
    this.color_map = color_map;

    this.div_id = div_id;

    // min and max bounds of the x and y axis
    this.minX = 100000000000;
    this.maxX = -100000000000;
    this.minY = 100000000000;
    this.maxY = -100000000000;

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

    // iterate through the rows to get the min and max values for the x and y axis
    for (var row in data){
      for (var key in data[row]){
        var v = data[row][key];
        if (key == 'x'){
          this.minX = Math.min(v,this.minX);
          this.maxX = Math.max(v,this.maxX);
        }
        if (key == 'total'){
          this.minY = Math.min(v,this.minY);
          this.maxY = Math.max(v,this.maxY);
        }
      }
    }
  }

  // sets the size of the plot
  set_size(w, h){
    this.w = w;
    this.h = h;
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
    var margin = {top: 10, right: 200, bottom: 30, left: 60},
        width = this.w - margin.left - margin.right,
        height = this.h - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select("#" + this.div_id)
      .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
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
      .call(d3.axisLeft(y));

    // initialize the bar data
    var total_power = [];
    for (var row in this.data){
      total_power.push({x : this.data[row]['x'], dx : this.data[row]['x'], value : this.data[row]['total']});
    }

    // update data to set dx correctly
    for (var i = 0; i < total_power.length - 1; i++){
      total_power[i]['dx'] = total_power[i + 1]['x'] - total_power[i]['x'];
    }
    total_power[total_power.length - 1]['dx'] = total_power[total_power.length - 2]['dx'];

    // Add a clipPath: everything out of this area won't be drawn.
    var clip = svg.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("width", width )
        .attr("height", height )
        .attr("x", 0)
        .attr("y", 0);

    // Add x axis zooming
    var brush = d3.brushX()
        .extent( [ [0,0], [width,height]] )
        .on("end", updateChart);

    // Create the bar zoom variable: where both the bars and brush take place
    var bar_brush = svg.append('g')
        .attr("clip-path", "url(#clip)")

    // Add the zoom capability
    svg.append("g")
        .attr("class", "brush")
        .call(brush);

    var idleTimeout
       function idled() { idleTimeout = null; }

    // setup bar graph
    var bar_graph = bar_brush.selectAll("bar")
      .data(total_power)
      .enter();

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
    var counter = 0;
    for (var key in this.legend){
      svg.append("rect").attr("x",width + 10).attr("y", margin.top + counter*20).attr("width", 8).attr("height", 8).style("fill", this.legend[key])
      svg.append("text").attr("x",width + 24).attr("y", margin.top + counter*20 + 4).text(key).style("font-size", "12px").attr("alignment-baseline","middle")
      counter += 1;
    }

    // set variables for brush for listeners
    this.bar_graph = bar_graph;
    this.bar_brush = bar_brush;
    this.width = width;
    this.x = x;
    this.y = y;
    this.xAxis = xAxis;

    this.set_brush(this.minX, this.maxX);

    // set variables for self brush
    var minX = this.minX;
    var maxX = this.maxX;
    var bar_width_of_mile = width/(x.domain()[1] - x.domain()[0]);
    var color_map = this.color_map;
    var me = this;

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
      .append("rect")
        .attr("x", function(d) { return x(d.x) })
        .attr("y", function(d) { if (d.value > 0) { return y(d.value); } else { return y(0); } })
        .attr("width", function(d) { return bar_width_of_mile*d.dx })
        .attr("height", function(d) { if (d.value > 0) { return y(0) - y(d.value); } else { return y(d.value) - y(0) } })
        .attr("fill", function(d) {
          if (color_map == undefined){
            return "steelblue";
          } else {
            var v = d.value;
            for (var key in color_map){
              var rng = color_map[key];
              if (d.value >= rng[0] && d.value <= rng[1]){
                return key;
              }
            }
          }
        })
  }

  // call this method to update other listeners bounds
  brush_updated(min, max){
    for (var i = 0; i < this.listeners.length; i++){
      this.listeners[i].set_brush(min, max);
    }
  }


}
