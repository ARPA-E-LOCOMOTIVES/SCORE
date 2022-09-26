class d3ScatterMatrix {

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

  set_constant_color(title){
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

    var scatter_matrix_data = [];

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
          scatter_matrix_data.push(row);
        }
    }

    d3.select("#" + this.div_id).selectAll('*').remove();

    var width = 1000,
        size = 100,
        padding = 10;

    var x = d3.scaleLinear()
        .range([padding / 2, size - padding / 2]);

    var y = d3.scaleLinear()
        .range([size - padding / 2, padding / 2]);

    var xAxis = d3.axisBottom()
        .scale(x)
        .ticks(0);

    var yAxis = d3.axisLeft()
        .scale(y)
        .ticks(0);

    var titles_to_show = [];
    for (var key in this.displayed_titles)
      if (this.displayed_titles[key])
        titles_to_show.push(key);
    var domainByTrait = {},
      traits = titles_to_show,
      n = traits.length;

    var min_values_plot = this.data_model.get_min_values();
    var max_values_plot = this.data_model.get_max_values();
    var colorTitle = this.color_title;

    titles_to_show.forEach(function(trait) {
      domainByTrait[trait] = d3.extent(scatter_matrix_data, function(d) { return d[trait]; });
    });

    var brush = d3.brush()
        .on("start", brushstart)
        .on("brush", brushmove)
        .on("end", brushend)
        .extent([[0,0],[size,size]]);

    var svg = d3.select("#" + this.div_id).append("svg")
        .attr("width", size * n + padding)
        .attr("height", size * n + padding)
        .append("g")
        .attr("transform", "translate(" + padding + "," + padding / 2 + ")");

    svg.selectAll(".x.axis")
        .data(traits)
        .enter().append("g")
        .attr("class", "x axis")
        .attr("transform", function(d, i) { return "translate(" + (n - i - 1) * size + ",0)"; })
        .each(function(d) { x.domain(domainByTrait[d]); d3.select(this).call(xAxis); });

    svg.selectAll(".y.axis")
        .data(traits)
        .enter().append("g")
        .attr("class", "y axis")
        .attr("transform", function(d, i) { return "translate(0," + i * size + ")"; })
        .each(function(d) { y.domain(domainByTrait[d]); d3.select(this).call(yAxis); });


    var cell = svg.selectAll(".cell")
        .data(cross(traits, traits))
        .enter().append("g")
        .attr("class", "cell")
        .attr("transform", function(d) { return "translate(" + (n - d.i - 1) * size + "," + d.j * size + ")"; })
        .each(plot);

    // Titles for the diagonal.
    cell.filter(function(d) { return d.i === d.j; })
        .append("text")
        .attr("x", padding)
        .attr("y", size/2 - 10)
        .attr("dy", "1.4em")
        .style("font-size", "10px")
        .text(function(d) { return d.x; });

    // disable in plot brush for now, will implment later
    //cell.call(brush);

    function plot(p) {

        // do not show the diagonal plot
        if (p.x == p.y)
          return;

        var cell = d3.select(this);

        x.domain([Math.min(0, min_values_plot[p.x]), max_values_plot[p.x]]);
        y.domain([Math.min(0, min_values_plot[p.y]), max_values_plot[p.y]]);

        cell.append("rect")
            .attr("class", "frame")
            .attr("x", padding / 2)
            .attr("y", padding / 2)
            .attr("width", size - padding)
            .attr("height", size - padding);

        if(colorTitle != "constant"){
          cell.selectAll("circle")
            .data(scatter_matrix_data)
            .enter().append("circle")
            .attr("cx", function(d) { return x(d[p.x]); })
            .attr("cy", function(d) { return y(d[p.y]); })
            .attr("r", 4)
            .on("click", function(d, i){
              var html = '<h4>Selected</h4></br>'
              for (var key in scatter_matrix_data[i])
                 html += '<h4>' + key +  '=' + d3.format(".0f")(scatter_matrix_data[i][key]) + "</h4>";
              d3.select("#scatter_matrix_details").html(html);
           	}).style("fill", function(d) { return d3.interpolateCool((d[colorTitle] - min_values_plot[colorTitle])/(max_values_plot[colorTitle] - min_values_plot[colorTitle])); });
        } else {
          cell.selectAll("circle")
            .data(scatter_matrix_data)
            .enter().append("circle")
            .attr("cx", function(d) { return x(d[p.x]); })
            .attr("cy", function(d) { return y(d[p.y]); })
            .attr("r", 4)
            .on("click", function(d, i){
              var html = '<h4>Selected</h4></br>'
              for (var key in scatter_matrix_data[i])
                 html += '<h4>' + key +  '=' + d3.format(".0f")(scatter_matrix_data[i][key]) + "</h4>";
              d3.select("#scatter_matrix_details").html(html);
            }).style("fill", function(d) { return d3.interpolateCool(0)});
        }
      }

      var brushCell;
      // Clear the previously-active brush, if any.
      function brushstart(p) {
        if (brushCell !== this) {
          d3.select(brushCell).call(brush.move, null);
          brushCell = this;
          x.domain(domainByTrait[p.x]);
          y.domain(domainByTrait[p.y]);
        }
      }

      // Highlight the selected circles.
      function brushmove(p) {
        var e = d3.brushSelection(this);
        svg.selectAll("circle").classed("hidden", function(d) {
          return !e
            ? false
            : (
              e[0][0] > x(+d[p.x]) || x(+d[p.x]) > e[1][0]
              || e[0][1] > y(+d[p.y]) || y(+d[p.y]) > e[1][1]
            );
        });
      }

      // If the brush is empty, select all circles.
      function brushend() {
        var e = d3.brushSelection(this);
        if (e === null) svg.selectAll(".hidden").classed("hidden", false);
      }


      function cross(a, b) {
        var c = [], n = a.length, m = b.length, i, j;
        for (i = -1; ++i < n;) for (j = -1; ++j < m;) c.push({x: a[i], i: i, y: b[j], j: j});
        return c;
      }

  }

}
