class d3BarSummaryChart {

  constructor(data, div_id) {
    this.data = data;
    this.div_id = div_id;
    this.minX = 0;
    this.maxX = 5;
    this.minY = 0;
    this.maxY = 100;
  }

  draw(){

    // set the dimensions and margins of the graph
    var margin = {top: 10, right: 30, bottom: 100, left: 60},
        width = 240 - margin.left - margin.right,
        height = 200 - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3.select("#" + this.div_id)
      .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform",
              "translate(" + margin.left + "," + margin.top + ")");

    // create the bar chart
    var x = d3.scaleBand()
      .domain(this.data.map(d => d.label))
      .range([ 0, width ]);

    // add x labels
    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x))
      .selectAll("text")
        .attr("y", -2)
        .attr("x", 20)
        .attr("font-size", "14")
        .attr("dy", ".35em")
        .attr("transform", "rotate(90)")
        .style("text-anchor", "start");

    // Add Y axis
    var y = d3.scaleLinear()
      .domain([this.minY, this.maxY])
      .range([ height, 0 ]);
    svg.append("g")
      .call(d3.axisLeft(y));

    // add bar data
    var bar_data = [];
    for (var row in this.data){
      bar_data.push({x : this.data[row]['label'] , value : this.data[row]['y'], color : this.data[row]['color']});
    }


    // need to make this better
    var x_buffer = 40/this.data.length;
    svg.selectAll("bar")
      .data(bar_data)
      .enter()
      .append("rect")
        .attr("x", function(d) { return x(d.x) + x_buffer })
        .attr("y", function(d) { return y(d.value) })
        .attr("width", 20)
        .attr("height", function(d) { return height - y(d.value); } )
        .attr("fill", function(d) { return d.color;})

  }

}
