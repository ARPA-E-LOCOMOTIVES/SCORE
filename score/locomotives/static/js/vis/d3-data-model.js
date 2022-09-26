class d3DataModel {
  constructor(data) {
    this.set_data(data);
  }
  // Getter
  get_data() {
    return this.data;
  }

  set_data(data) {
    this.data = data;
    this.titles = [];
    //this.listeners = [];
    this.min_values = {};
    this.max_values = {};
    this.min_brush_values = {};
    this.max_brush_values = {};
    this.categorical_values = {};
    this.visible_categorical_values = {};
    for (var key in this.data) {
        if (this.data.hasOwnProperty(key)) {
            this.titles.push(key);
            this.min_values[key] = d3.min(this.data[key]);
            this.max_values[key] = d3.max(this.data[key]);
            this.min_brush_values[key] = d3.min(this.data[key]);
            this.max_brush_values[key] = d3.max(this.data[key]);
            if (isNaN(this.data[key][0])){
              this.categorical_values[key] = Array.from(new Set(this.data[key]));
              this.visible_categorical_values[key] = Array.from(new Set(this.data[key]));
            }
        }
    }
  }

  get_titles(){
    return this.titles;
  }

  get_min_values(){
    return this.min_values;
  }

  get_max_values(){
    return this.max_values;
  }

  get_min_brush_values(){
    return this.min_brush_values;
  }

  get_max_brush_values(){
    return this.max_brush_values;
  }

  get_categorical_values(){
    return this.categorical_values;
  }

  set_filter_values(title, min, max){
    this.min_brush_values[title] = min;
    this.max_brush_values[title] = max;
    //for (var listener in this.listeners){
    //  listener.update_filter();
    //}
  }

  is_catergorical(title){
    return this.categorical_values[title] != undefined;
  }

  is_catergorical_token_visible(title, token){
    return this.visible_categorical_values[title].includes(token);
  }

  add_listener(listener){
    //this.listeners.push(listener);
  }

  update_visible_token(title, token, visible){
    console.log("before", this.visible_categorical_values[title]);
    if (visible && !this.visible_categorical_values[title].includes(token)){
      this.visible_categorical_values[title].push(token);
    }
    if (!visible && this.visible_categorical_values[title].includes(token)){
      const index = this.visible_categorical_values[title].indexOf(token);
      if (index > -1) {
        this.visible_categorical_values[title].splice(index, 1); // 2nd parameter means remove one item only
      }
    }
    console.log("after", this.visible_categorical_values[title]);
  }

}