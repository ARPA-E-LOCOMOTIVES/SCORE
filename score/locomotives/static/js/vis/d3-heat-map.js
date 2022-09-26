class d3HeatMap {

  constructor(data, myGroups, myVars, div_id, min, max, x_label, y_label, x_min, x_max, title_label) {

    // set the dimensions and margins of the graph
    var margin = {top: 30, right: 30, bottom: 30, left: 40},
      width = 400 - margin.left - margin.right,
      height = 400 - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select("#" + div_id)
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    // Build X scales and axis:
    var x = d3.scaleBand()
      .range([ 0, width ])
      .domain(myGroups)
      .padding(0.01);
    var xaxis = svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x))

    // Build X scales and axis:
    var y = d3.scaleBand()
      .range([ height, 0 ])
      .domain(myVars)
      .padding(0.01);
    var yaxis = svg.append("g")
      .call(d3.axisLeft(y));

    xaxis.selectAll("text").remove();

    var posColor = d3.scaleLinear()
      .range(["white", "#69b3a2"])
      .domain([0, max]);

    var negColor = d3.scaleLinear()
      .range(["orange", "white"])
      .domain([min, 0]);

    svg.append('text').attr('x', width/2).attr('y', -14).attr('text-anchor', 'middle')
      .style('font-family', 'Helvetica').style('font-size', 18).text(title_label + " " + min.toFixed(2) + " to " + max.toFixed(2));

    // x label
    svg.append('text').attr('x', width/2).attr('y', height + 20).attr('text-anchor', 'middle')
      .style('font-family', 'Helvetica').style('font-size', 18).text(x_label);

    svg.append('text').attr('x', 0).attr('y', height + 20).attr('text-anchor', 'middle')
      .style('font-family', 'Helvetica').style('font-size', 18).text(x_min);

    svg.append('text').attr('x', width).attr('y', height + 20).attr('text-anchor', 'middle')
      .style('font-family', 'Helvetica').style('font-size', 18).text(x_max);

    // y label
    svg.append('text').attr('text-anchor', 'middle').attr('transform', 'translate(-22,' + height/2 + ')rotate(-90)')
      .style('font-family', 'Helvetica').style('font-size', 18).text(y_label);

    svg.selectAll()
        .data(data, function(d) {return d.group+':'+d.variable;})
        .enter()
        .append("rect")
        .attr("x", function(d) { return x(d.group) })
        .attr("y", function(d) { return y(d.variable) })
        .attr("width", x.bandwidth() )
        .attr("height", y.bandwidth() )
        .style("fill", function(d) {
          if (d.value > 0) {
            return posColor(d.value);
          } else {
            return negColor(d.value);
          }
        }
      )

  }

}
