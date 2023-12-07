// Copyright (c) 2022, The Pennsylvania State University
// All rights reserved.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
// IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
// FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.

class d3ParCoord {

  constructor(div_id) {
    this.div_id = div_id;
    this.color_title = "constant";
  }

  set_data_model(data_model){
    this.data_model = data_model;
    this.displayed_titles = {};
    for(var i = 0 ; i < this.data_model.get_titles().length; i++){
      this.displayed_titles[this.data_model.get_titles()[i]] = true;
    }
  }

  set_number_of_display_variables(N){
    idx = 0
    for (var key in this.displayed_titles){
      this.displayed_titles[key] = (idx < N);
      idx += 1;
    }
  }

  update_filter(){
    this.refresh();
  }

  set_color(title){
    this.color_title = title;
    this.refresh();
    var min_value = this.data_model.get_min_values()[title];
    var max_value = this.data_model.get_max_values()[title];
    if (isNaN(min_value)){
      return [min_value, max_value];
    } else {
      return [min_value.toFixed(2), max_value.toFixed(2)];
    }
  }

  set_constant_color(){
    this.color_title = "constant";
    this.refresh();
  }

  add_variable(title){
    this.displayed_titles[title] = true;
    this.refresh();
  }

  remove_variable(title){
    this.displayed_titles[title] = false;
    this.refresh();
  }

  refresh(){

    var par_coord_data = [];

    // get a key
    var key = "";
    for (var key in this.data_model.get_data()){
    }

    var N = this.data_model.get_data()[key].length;
    for (var i = 0 ; i < N; i++){
        var row = {};
        // check filter
        var visible = true;
        for (var title in this.displayed_titles){
          row[title] = this.data_model.get_data()[title][i];

          var categorical = this.data_model.is_catergorical(title);

          // some weird tolerance issue is occurring
          if (!categorical){
            if (row[title] < this.data_model.get_min_brush_values()[title]){
              visible = false;
            }
            if (row[title] > this.data_model.get_max_brush_values()[title]){
              visible = false;
            }
          } else {
            var token = this.data_model.get_data()[title][i];
            var token_visibible = this.data_model.is_catergorical_token_visible(title, token);
            if (!token_visibible){
              visible = false;
            }
          }

        }
        if (visible){
          par_coord_data.push(row);
        }
    }

    d3.select("#" + this.div_id).selectAll('*').remove();

    var margin = {top: 30, right: 10, bottom: 10, left: 0},
      width = 720 - margin.left - margin.right,
      height = 400 - margin.top - margin.bottom;

    // Extract the list of dimensions we want to keep in the plot. Here I keep all except the column called Species
     //var dimensions = d3.keys(par_coord_data[0]);
     //console.log(dimensions);

     var dimensions = [];
     for (var title in this.displayed_titles){
       if(this.displayed_titles[title]){
         dimensions.push(title);
       }
     }

     // For each dimension, I build a linear scale. I store all in a y object
     var y = {}
     for (i in dimensions) {
       name = dimensions[i];
       var extent = d3.extent(par_coord_data, function(d) { return +d[name]; });
       console.log(extent);
       extent[0] = this.data_model.min_values[name];
       extent[1] = this.data_model.max_values[name];
       if (extent[0] > 0){
         extent[0] = 0;
       }
       y[name] = d3.scaleLinear()
         .domain( extent )
         .range([height, 0]);
     }

     // Build the X scale -> it find the best position for each Y axis
     var x = d3.scalePoint()
       .range([0, width])
       .padding(1)
       .domain(dimensions);

     // The path function take a row of the csv as input, and return x and y coordinates of the line to draw for this raw.
     function path(d) {
         return d3.line()(dimensions.map(function(p) { return [x(p), y[p](d[p])]; }));
     }

     // append the svg object to the body of the page
     var svg = d3.select("#" + this.div_id)
     .append("svg")
       .attr("width", width + margin.left + margin.right)
       .attr("height", height + margin.top + margin.bottom)
     .append("g")
       .attr("transform",
             "translate(" + margin.left + "," + margin.top + ")");

     var min_values_plot = this.data_model.get_min_values();
     var max_values_plot = this.data_model.get_max_values();
     var colorTitle = this.color_title;

     // Draw the lines
    if(colorTitle != "constant"){
      svg
         .selectAll("myPath")
         .data(par_coord_data)
         .enter().append("path")
         .attr("d",  path)
         .style("fill", "none")
         .style("stroke", function(d) { return d3.interpolateCool((d[colorTitle] - min_values_plot[colorTitle])/(max_values_plot[colorTitle] - min_values_plot[colorTitle])); } )
         .style("opacity", 1.0  );
    } else {
      svg
         .selectAll("myPath")
         .data(par_coord_data)
         .enter().append("path")
         .attr("d",  path)
         .style("fill", "none")
         .style("stroke", "purple")
         .style("opacity", 1.0);
     }

     // Draw the axis:
     svg.selectAll("myAxis")
       // For each dimension of the dataset I add a 'g' element:
       .data(dimensions).enter()
       .append("g")
       // I translate this element to its right position on the x axis
       .attr("transform", function(d) { return "translate(" + x(d) + ")"; })
       // And I build the axis with the call function
       .each(function(d) { d3.select(this).call(d3.axisLeft().scale(y[d])); })
       // Add axis title
       .append("text")
         .style("text-anchor", "middle")
         .attr("y", -9)
         .text(function(d) { return d; })
         .style("fill", "black");



  }

}
