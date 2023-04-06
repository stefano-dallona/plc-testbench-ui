class RunAnalysisView {
  i = 0
  fileDir;
  filename;
  loss_file;
  zeroEccFilename;
  lowCostEccFilename;
  packet_size;
  samplesJson;
  zeroEccFileSamplesJson;
  lowCostFileSamplesJson;
  breakpointLayer;
  zeroEccBreakpointLayer;
  lowCostEccBreakpointLayer;
  segmentLayer;
  segmentLayerOnWaveform;
  cursorLayer;
  timelineLostPackets;
  totalSamples;
  timelineSamples;
  timelineWaveform;
  audioDuration;
  selectedLoss;
  startTime;
  endTime;
  pixelsPerSecond;
  layersMap = new Map();
  waveformTrack;

  margin = { top: 20, right: 120, bottom: 20, left: 120 }
  canvas_height = 400
  canvas_width = 960
  tree_width = this.canvas_width - this.margin.right - this.margin.left
  tree_height = this.canvas_height - this.margin.top - this.margin.bottom
  tree_level_depth = 180
  tree;
  diagonal;
  svg;
  

  constructor(controller, options) {
    this.controller = controller
    this.controller.view = this
    this.fileDir = options && options.fileDir || './assets';
    this.filename = options && options.fileDir || 'Blues_Bass.wav';
    this.zeroEccFilename = options && options.fileDir || "ZerosEcc.wav"
    this.lowCostEccFilename = options && options.fileDir || "LowCostEcc.wav"
    this.packet_size = options && options.fileDir || 64;
    this.layersMap = new Map();
    this.colorMap = [[0, 0, 0, 1], [0.011764705882352941, 0, 0, 1], [0.023529411764705882, 0, 0, 1], [0.03529411764705882, 0, 0, 1], [0.047058823529411764, 0, 0, 1], [0.058823529411764705, 0, 0, 1], [0.07058823529411765, 0, 0, 1], [0.08235294117647059, 0, 0, 1], [0.09411764705882353, 0, 0, 1], [0.10588235294117647, 0, 0, 1], [0.11764705882352941, 0, 0, 1], [0.12941176470588237, 0, 0, 1], [0.1411764705882353, 0, 0, 1], [0.15294117647058825, 0, 0, 1], [0.16470588235294117, 0, 0, 1], [0.17647058823529413, 0, 0, 1], [0.18823529411764706, 0, 0, 1], [0.2, 0, 0, 1], [0.21176470588235294, 0, 0, 1], [0.2235294117647059, 0, 0, 1], [0.23529411764705882, 0, 0, 1], [0.24705882352941178, 0, 0, 1], [0.25882352941176473, 0, 0, 1], [0.27058823529411763, 0, 0, 1], [0.2823529411764706, 0, 0, 1], [0.29411764705882354, 0, 0, 1], [0.3058823529411765, 0, 0, 1], [0.3176470588235294, 0, 0, 1], [0.32941176470588235, 0, 0, 1], [0.3411764705882353, 0, 0, 1], [0.35294117647058826, 0, 0, 1], [0.36470588235294116, 0, 0, 1], [0.3764705882352941, 0, 0, 1], [0.38823529411764707, 0, 0, 1], [0.4, 0, 0, 1], [0.4117647058823529, 0, 0, 1], [0.4235294117647059, 0, 0, 1], [0.43529411764705883, 0, 0, 1], [0.4470588235294118, 0, 0, 1], [0.4549019607843137, 0, 0, 1], [0.4666666666666667, 0, 0, 1], [0.47843137254901963, 0, 0, 1], [0.49019607843137253, 0, 0, 1], [0.5019607843137255, 0, 0, 1], [0.5137254901960784, 0, 0, 1], [0.5254901960784314, 0, 0, 1], [0.5372549019607843, 0, 0, 1], [0.5490196078431373, 0, 0, 1], [0.5607843137254902, 0, 0, 1], [0.5725490196078431, 0, 0, 1], [0.5843137254901961, 0, 0, 1], [0.596078431372549, 0, 0, 1], [0.6078431372549019, 0, 0, 1], [0.6196078431372549, 0, 0, 1], [0.6313725490196078, 0, 0, 1], [0.6431372549019608, 0, 0, 1], [0.6549019607843137, 0, 0, 1], [0.6666666666666666, 0, 0, 1], [0.6784313725490196, 0, 0, 1], [0.6901960784313725, 0, 0, 1], [0.7019607843137254, 0, 0, 1], [0.7137254901960784, 0, 0, 1], [0.7254901960784313, 0, 0, 1], [0.7372549019607844, 0, 0, 1], [0.7490196078431373, 0, 0, 1], [0.7607843137254902, 0, 0, 1], [0.7725490196078432, 0, 0, 1], [0.7843137254901961, 0, 0, 1], [0.796078431372549, 0, 0, 1], [0.807843137254902, 0, 0, 1], [0.8196078431372549, 0, 0, 1], [0.8313725490196079, 0, 0, 1], [0.8431372549019608, 0, 0, 1], [0.8549019607843137, 0, 0, 1], [0.8666666666666667, 0, 0, 1], [0.8784313725490196, 0, 0, 1], [0.8901960784313725, 0, 0, 1], [0.9019607843137255, 0, 0, 1], [0.9019607843137255, 0.011764705882352941, 0, 1], [0.9058823529411765, 0.023529411764705882, 0, 1], [0.9058823529411765, 0.03137254901960784, 0, 1], [0.9058823529411765, 0.043137254901960784, 0, 1], [0.9098039215686274, 0.054901960784313725, 0, 1], [0.9098039215686274, 0.06666666666666667, 0, 1], [0.9098039215686274, 0.07450980392156863, 0, 1], [0.9137254901960784, 0.08627450980392157, 0, 1], [0.9137254901960784, 0.09803921568627451, 0, 1], [0.9137254901960784, 0.10980392156862745, 0, 1], [0.9176470588235294, 0.11764705882352941, 0, 1], [0.9176470588235294, 0.12941176470588237, 0, 1], [0.9176470588235294, 0.1411764705882353, 0, 1], [0.9215686274509803, 0.15294117647058825, 0, 1], [0.9215686274509803, 0.1607843137254902, 0, 1], [0.9215686274509803, 0.17254901960784313, 0, 1], [0.9254901960784314, 0.1843137254901961, 0, 1], [0.9254901960784314, 0.19607843137254902, 0, 1], [0.9254901960784314, 0.20784313725490197, 0, 1], [0.9294117647058824, 0.21568627450980393, 0, 1], [0.9294117647058824, 0.22745098039215686, 0, 1], [0.9294117647058824, 0.23921568627450981, 0, 1], [0.9333333333333333, 0.25098039215686274, 0, 1], [0.9333333333333333, 0.25882352941176473, 0, 1], [0.9333333333333333, 0.27058823529411763, 0, 1], [0.9372549019607843, 0.2823529411764706, 0, 1], [0.9372549019607843, 0.29411764705882354, 0, 1], [0.9372549019607843, 0.30196078431372547, 0, 1], [0.9411764705882353, 0.3137254901960784, 0, 1], [0.9411764705882353, 0.3254901960784314, 0, 1], [0.9411764705882353, 0.33725490196078434, 0, 1], [0.9450980392156862, 0.34509803921568627, 0, 1], [0.9450980392156862, 0.3568627450980392, 0, 1], [0.9450980392156862, 0.3686274509803922, 0, 1], [0.9490196078431372, 0.3803921568627451, 0, 1], [0.9490196078431372, 0.38823529411764707, 0, 1], [0.9490196078431372, 0.4, 0, 1], [0.9529411764705882, 0.4117647058823529, 0, 1], [0.9529411764705882, 0.4235294117647059, 0, 1], [0.9529411764705882, 0.43529411764705883, 0, 1], [0.9529411764705882, 0.44313725490196076, 0, 1], [0.9568627450980393, 0.4549019607843137, 0, 1], [0.9568627450980393, 0.4666666666666667, 0, 1], [0.9568627450980393, 0.47843137254901963, 0, 1], [0.9607843137254902, 0.48627450980392156, 0, 1], [0.9607843137254902, 0.4980392156862745, 0, 1], [0.9607843137254902, 0.5098039215686274, 0, 1], [0.9647058823529412, 0.5215686274509804, 0, 1], [0.9647058823529412, 0.5294117647058824, 0, 1], [0.9647058823529412, 0.5411764705882353, 0, 1], [0.9686274509803922, 0.5529411764705883, 0, 1], [0.9686274509803922, 0.5647058823529412, 0, 1], [0.9686274509803922, 0.5725490196078431, 0, 1], [0.9725490196078431, 0.5843137254901961, 0, 1], [0.9725490196078431, 0.596078431372549, 0, 1], [0.9725490196078431, 0.6078431372549019, 0, 1], [0.9764705882352941, 0.6196078431372549, 0, 1], [0.9764705882352941, 0.6274509803921569, 0, 1], [0.9764705882352941, 0.6392156862745098, 0, 1], [0.9803921568627451, 0.6509803921568628, 0, 1], [0.9803921568627451, 0.6627450980392157, 0, 1], [0.9803921568627451, 0.6705882352941176, 0, 1], [0.984313725490196, 0.6823529411764706, 0, 1], [0.984313725490196, 0.6941176470588235, 0, 1], [0.984313725490196, 0.7058823529411765, 0, 1], [0.9882352941176471, 0.7137254901960784, 0, 1], [0.9882352941176471, 0.7254901960784313, 0, 1], [0.9882352941176471, 0.7372549019607844, 0, 1], [0.9921568627450981, 0.7490196078431373, 0, 1], [0.9921568627450981, 0.7568627450980392, 0, 1], [0.9921568627450981, 0.7686274509803922, 0, 1], [0.996078431372549, 0.7803921568627451, 0, 1], [0.996078431372549, 0.792156862745098, 0, 1], [0.996078431372549, 0.8, 0, 1], [1, 0.8117647058823529, 0, 1], [1, 0.8235294117647058, 0, 1], [1, 0.8235294117647058, 0.011764705882352941, 1], [1, 0.8274509803921568, 0.0196078431372549, 1], [1, 0.8274509803921568, 0.03137254901960784, 1], [1, 0.8313725490196079, 0.0392156862745098, 1], [1, 0.8313725490196079, 0.050980392156862744, 1], [1, 0.8352941176470589, 0.058823529411764705, 1], [1, 0.8352941176470589, 0.07058823529411765, 1], [1, 0.8392156862745098, 0.0784313725490196, 1], [1, 0.8392156862745098, 0.09019607843137255, 1], [1, 0.8392156862745098, 0.09803921568627451, 1], [1, 0.8431372549019608, 0.10980392156862745, 1], [1, 0.8431372549019608, 0.11764705882352941, 1], [1, 0.8470588235294118, 0.12941176470588237, 1], [1, 0.8470588235294118, 0.13725490196078433, 1], [1, 0.8509803921568627, 0.14901960784313725, 1], [1, 0.8509803921568627, 0.1568627450980392, 1], [1, 0.8549019607843137, 0.16862745098039217, 1], [1, 0.8549019607843137, 0.17647058823529413, 1], [1, 0.8549019607843137, 0.18823529411764706, 1], [1, 0.8588235294117647, 0.19607843137254902, 1], [1, 0.8588235294117647, 0.20784313725490197, 1], [1, 0.8627450980392157, 0.21568627450980393, 1], [1, 0.8627450980392157, 0.22745098039215686, 1], [1, 0.8666666666666667, 0.23529411764705882, 1], [1, 0.8666666666666667, 0.24705882352941178, 1], [1, 0.8666666666666667, 0.2549019607843137, 1], [1, 0.8705882352941177, 0.26666666666666666, 1], [1, 0.8705882352941177, 0.27450980392156865, 1], [1, 0.8745098039215686, 0.28627450980392155, 1], [1, 0.8745098039215686, 0.29411764705882354, 1], [1, 0.8784313725490196, 0.3058823529411765, 1], [1, 0.8784313725490196, 0.3137254901960784, 1], [1, 0.8823529411764706, 0.3254901960784314, 1], [1, 0.8823529411764706, 0.3333333333333333, 1], [1, 0.8823529411764706, 0.34509803921568627, 1], [1, 0.8862745098039215, 0.35294117647058826, 1], [1, 0.8862745098039215, 0.36470588235294116, 1], [1, 0.8901960784313725, 0.37254901960784315, 1], [1, 0.8901960784313725, 0.3843137254901961, 1], [1, 0.8941176470588236, 0.39215686274509803, 1], [1, 0.8941176470588236, 0.403921568627451, 1], [1, 0.8980392156862745, 0.4117647058823529, 1], [1, 0.8980392156862745, 0.4235294117647059, 1], [1, 0.8980392156862745, 0.43137254901960786, 1], [1, 0.9019607843137255, 0.44313725490196076, 1], [1, 0.9019607843137255, 0.45098039215686275, 1], [1, 0.9058823529411765, 0.4627450980392157, 1], [1, 0.9058823529411765, 0.47058823529411764, 1], [1, 0.9098039215686274, 0.4823529411764706, 1], [1, 0.9098039215686274, 0.49019607843137253, 1], [1, 0.9137254901960784, 0.5019607843137255, 1], [1, 0.9137254901960784, 0.5098039215686274, 1], [1, 0.9137254901960784, 0.5215686274509804, 1], [1, 0.9176470588235294, 0.5294117647058824, 1], [1, 0.9176470588235294, 0.5411764705882353, 1], [1, 0.9215686274509803, 0.5490196078431373, 1], [1, 0.9215686274509803, 0.5607843137254902, 1], [1, 0.9254901960784314, 0.5686274509803921, 1], [1, 0.9254901960784314, 0.5803921568627451, 1], [1, 0.9254901960784314, 0.5882352941176471, 1], [1, 0.9294117647058824, 0.6, 1], [1, 0.9294117647058824, 0.6078431372549019, 1], [1, 0.9333333333333333, 0.6196078431372549, 1], [1, 0.9333333333333333, 0.6274509803921569, 1], [1, 0.9372549019607843, 0.6392156862745098, 1], [1, 0.9372549019607843, 0.6470588235294118, 1], [1, 0.9411764705882353, 0.6588235294117647, 1], [1, 0.9411764705882353, 0.6666666666666666, 1], [1, 0.9411764705882353, 0.6784313725490196, 1], [1, 0.9450980392156862, 0.6862745098039216, 1], [1, 0.9450980392156862, 0.6980392156862745, 1], [1, 0.9490196078431372, 0.7058823529411765, 1], [1, 0.9490196078431372, 0.7176470588235294, 1], [1, 0.9529411764705882, 0.7254901960784313, 1], [1, 0.9529411764705882, 0.7372549019607844, 1], [1, 0.9568627450980393, 0.7450980392156863, 1], [1, 0.9568627450980393, 0.7568627450980392, 1], [1, 0.9568627450980393, 0.7647058823529411, 1], [1, 0.9607843137254902, 0.7764705882352941, 1], [1, 0.9607843137254902, 0.7843137254901961, 1], [1, 0.9647058823529412, 0.796078431372549, 1], [1, 0.9647058823529412, 0.803921568627451, 1], [1, 0.9686274509803922, 0.8156862745098039, 1], [1, 0.9686274509803922, 0.8235294117647058, 1], [1, 0.9725490196078431, 0.8352941176470589, 1], [1, 0.9725490196078431, 0.8431372549019608, 1], [1, 0.9725490196078431, 0.8549019607843137, 1], [1, 0.9764705882352941, 0.8627450980392157, 1], [1, 0.9764705882352941, 0.8745098039215686, 1], [1, 0.9803921568627451, 0.8823529411764706, 1], [1, 0.9803921568627451, 0.8941176470588236, 1], [1, 0.984313725490196, 0.9019607843137255, 1], [1, 0.984313725490196, 0.9137254901960784, 1], [1, 0.984313725490196, 0.9215686274509803, 1], [1, 0.9882352941176471, 0.9333333333333333, 1], [1, 0.9882352941176471, 0.9411764705882353, 1], [1, 0.9921568627450981, 0.9529411764705882, 1], [1, 0.9921568627450981, 0.9607843137254902, 1], [1, 0.996078431372549, 0.9725490196078431, 1], [1, 0.996078431372549, 0.9803921568627451, 1], [1, 1, 0.9921568627450981, 1], [1, 1, 1, 1]]
    this.colors = [];   
    this.initColorsPalette()
  }

  initColorsPalette() {
    while (this.colors.length < 100) {
      let newColor = null
      do {
        newColor = Math.floor((Math.random() * 1000000) + 1);
      } while (this.colors.indexOf(newColor) >= 0);
      this.colors.push("#" + ("000000" + newColor.toString(16)).slice(-6));
    }
  }

  renderInputFiles(input_files) {
    let mySelect = document.getElementById('selectedInputFile');

    mySelect.innerHTML = ""
    input_files.forEach((it) => {
      let myOption = document.createElement("option");
      myOption.text = it;
      myOption.value = it;
      mySelect.appendChild(myOption);
    })
  }

  populatePlayableFiles(playableFiles) {
    let mySelect = document.getElementById('aufiofileToBePlayed');
    mySelect.innerHTML = ""
    playableFiles.forEach((it, index) => {
      let myOption = document.createElement("option");
      myOption.text = it.name + (it.parent ? " - " + it.parent.name : "")
      myOption.value = index;
      mySelect.appendChild(myOption);
    })
  }

  updateRunHierarchy(source) {

    // Compute the new tree layout.
    var nodes = this.tree.nodes(this.controller.model.root),
      links = this.tree.links(nodes);

    // Normalize for fixed-depth.
    const _view = this
    nodes.forEach(function (d) { d.y = d.depth * _view.tree_level_depth; });

    // Set unique ID for each node
    var node = this.svg.selectAll("g.node")
      .data(nodes, function (d) { return d.id || (d.id = ++_view.i); });

    // Enter any new nodes at the parent's previous position.
    var new_nodes = node.enter().append("g")
      .attr("class", "node")
      .attr("transform", function (d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
      .on("click", controller.handleTreeClick())
      .on("dblclick", controller.handleTreeDblclick());

    new_nodes.append("image")
      .attr("xlink:href", function (d) { return "./assets/" + d.type + ".png"; }) //d.icon; })
      .attr("x", "-5px")
      .attr("y", "-12px")
      .attr("width", "24px")
      .attr("height", "24px");

    new_nodes.append("text")
      .attr("x", function (d) { return d.children || d._children ? -35 : 25; })
      .attr("dy", ".35em")
      .attr("text-anchor", function (d) { return d.children || d._children ? "end" : "start"; })
      .text(function (d) { return d.name; })
      .style("fill-opacity", 1e-6)
      .style("fill", "black");

    // Transition nodes to their new position.
    var moved_node = node.transition().duration(controller.model.duration)
      .attr("transform", function (d) { return "translate(" + d.y + "," + d.x + ")"; });
    moved_node.select("circle")
      .attr("r", 4.5)
      .style("fill", function (d) { return d._children ? "lightsteelblue" : "#fff"; });
    moved_node.select("text")
      .style("fill-opacity", 1);


    // Transition exiting nodes to the parent's new position.
    var hidden_nodes = node.exit().transition().duration(controller.model.duration)
      .attr("transform", function (d) { return "translate(" + source.y + "," + source.x + ")"; })
      .remove();
    hidden_nodes.select("circle")
      .attr("r", 1e-6);
    hidden_nodes.select("text")
      .style("fill-opacity", 1e-6);

    // Update the links…
    var link = this.svg.selectAll("path.link")
      .data(links, function (d) { return d.target.id; });


    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
      .attr("class", "link")
      .attr("d", function (d) {
        var o = { x: source.x0, y: source.y0 };
        return _view.diagonal({ source: o, target: o });
      })
      .append("svg:title")
      .text(function (d, i) { return d.target.edge_name; });

    //Transition links to their new position.
    link.transition().duration(controller.model.duration)
      .attr("d", _view.diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition().duration(controller.model.duration)
      .attr("d", function (d) {
        var o = { x: source.x, y: source.y };
        return _view.diagonal({ source: o, target: o });
      })
      .remove();


    // Stash the old positions for transition.
    nodes.forEach(function (d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });

  }

  toggleWaveform(waveformTrack, layersMap, filename) {
    const waveformLayer = layersMap.get(filename)
    const found = waveformTrack.layers.indexOf(waveformLayer) != -1
    if (found) {
      waveformTrack.remove(waveformLayer)
    } else {
      waveformTrack.add(waveformLayer)
    }
    waveformTrack.render()
    waveformTrack.update()
  }

  segmentLayerListener() {
    const _view = this
    return function (e) {
      var eventType = e.type;

      let segmentLayers = Array.from(_view.layersMap).filter(([name, value]) => value instanceof wavesUI.helpers.SegmentLayer).map(([name, value]) => value)
      for (let l of segmentLayers) {
        if (l.getItemFromDOMElement(e.target)) {
          _view.segmentLayerOnWaveform = l
          _view.segment = _view.segmentLayerOnWaveform.getItemFromDOMElement(e.target)
        }
      }

      if (!_view.segment) return;

      var datum = _view.segmentLayerOnWaveform.getDatumFromItem(_view.segment);
      console.log("datum: (x:" + datum.lossstart + ", width:" + datum.losswidth + ")")

      if (eventType == 'mouseover' || eventType == 'mouseout') {
        datum.opacity = eventType === 'mouseover' ? 1 : 0.8;
        _view.segmentLayerOnWaveform.updateShapes();
      }
      if (eventType == 'click') {
        _view.segmentLayerOnWaveform.updateShapes();
        if (_view.controller.model.selectedLoss) _view.controller.model.selectedLoss.color = undefined
        _view.controller.model.selectedLoss = datum
        _view.controller.model.selectedLoss.color = "red"
        _view.controller.selectSamples(datum.start_sample, datum.num_samples)
      }
    }
  }

  updateCursor() {
    const _view = this
    // listen for time passing...
    return function loop() {
      if (_view.cursorLayer) {
        //console.log("startOffset:" + _view.controller.model.startOffset)
        let offset = _view.controller.audioContext.currentTime - _view.controller.model.startTime
        let position = offset < _view.controller.bufferLoader.bufferList[0].duration ? offset : 0
        _view.cursorLayer.currentPosition = position
        _view.cursorLayer.update();
      }
      window.requestAnimationFrame(loop);
    };
  }

  renderWaveforms() {
    const _this = this
    return (bufferList) => {

      var $track = document.querySelector('#track-2');
      var width = $track.getBoundingClientRect().width;
      var height = 200;
      var duration = bufferList[0].duration;
      this.audioDuration = duration;


      // define the numbr of pixels per seconds the timeline should display
      var pixelsPerSecond = width / duration;
      // create a timeline
      _this.timeline = new wavesUI.core.Timeline(pixelsPerSecond, width);
      // create a new track into the `track-1` element and give it a id ('main')
      _this.waveformTrack = _this.timeline.createTrack($track, height, 'waveform');


      //const colors = ["blue", "red", "green", "red", "green"]

      // create the layer
      bufferList.map((buffer, index) => {
        _this.waveformLayer = new wavesUI.helpers.WaveformLayer(buffer, {
          height: 200,
          color: this.colors[index]
        });
        return _this.waveformLayer
      }).forEach((waveformLayer, index) => {
        // insert the layer inside the 'main' track
        //if ([-1].indexOf(index) != -1) {
        _this.timeline.addLayer(waveformLayer, 'waveform');
        _this.layersMap.set(_this.controller.model.audioFiles[index], waveformLayer);
        //}
      })

      _this.cursorLayer = new wavesUI.helpers.CursorLayer({
        height: height
      });

      _this.timeline.addLayer(_this.cursorLayer, 'waveform')

      _this.timeline.state = new wavesUI.states.BrushZoomState(_this.timeline);

      _this.timelineWaveform = _this.timeline;

      _this.controller.model.lossFiles.forEach((lossFile, index) => {
        //if ([0].indexOf(index) != -1) {
          _this.displayLostPacketsOnWaveForm(_this.controller.model.audioFiles[0], lossFile);
        //}
      })

      const audioFileURLs = _this.controller.model.audioFiles.map((file) => {
        return `${_this.controller.baseUrl}/analysis/runs/${_this.controller.model.run_id}/input-files/${file.uuid}/output-files/${file.uuid}`
      })
      this.renderSpectrogrom("#spectrogram-waveform", "#spectrogram", audioFileURLs[0])
    }
  }

  async displayLostPacketsOnWaveForm(original_audio_node, loss_simulation_node) {
    if (!loss_simulation_node) return;
    if (this.layersMap.get(loss_simulation_node)) return;
    const lostPacketsJson = await this.controller.fetchLostSamples(original_audio_node, loss_simulation_node)

    // create the layer
    this.segmentLayerOnWaveform = new wavesUI.helpers.SegmentLayer(lostPacketsJson.lost_intervals, {
      height: 200,
      displayHandlers: false,
    });

    this.layersMap.set(loss_simulation_node, this.segmentLayerOnWaveform)

    // insert the layer inside the 'main' track
    this.timelineWaveform.addLayer(this.segmentLayerOnWaveform, 'waveform');

    this.timelineWaveform.tracks.render(this.segmentLayerOnWaveform);
    this.timelineWaveform.tracks.update(this.segmentLayerOnWaveform);

    // add an hover effect on the segments
    this.timelineWaveform.on('event', this.segmentLayerListener());
  }

  renderRunHierarchy() {
    d3.select("#tree-1").html(null)

    this.tree = d3.layout.tree()
      .size([this.tree_height, this.tree_width]);

    this.diagonal = d3.svg.diagonal()
      .projection(function (d) { return [d.y, d.x]; });

    this.svg = d3.select("#tree-1").append("svg")
      .attr("width", this.canvas_width)
      .attr("height", this.canvas_height)
      .attr("class", "hierarchy")
      .append("g")
      .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
  }

  renderSamples(data) {
    function extractChannelData(data, channel) {
      return data.map((it) => {
        var point = { "sample": it["sample"], "value": it["values"][channel - 1] }
        return point
      })
    }

    function extractSampleData(data) {
      return data.map((it) => {
        var point = { "sample": it["cx"], "value": it["cy"] }
        return point
      })
    }

    function display() {
      var viewportExtent = navViewport.empty() ? navXScale.domain() : navViewport.extent();
      console.log("viewportExtent: (" + viewportExtent[0] + "," + viewportExtent[1] + ")")
      zoomToPeriod(viewportExtent[0], viewportExtent[1]);
    }

    function drawLine(lineData, lineColor, lineLabel, lineId) {
      // append line to svg
      var group = chartsContainer.append("g")
        .attr('class', lineId);

      var l = group.append("svg:path")
        .attr('id', lineId)
        .attr('d', line(lineData))
        .attr('stroke', lineColor)
        .attr('stroke-width', 2)
        .attr('fill', 'none');

      return group;
    }

    function drawPoints(pointData, pointColor, onLine) {
      // create points for line
      var points = onLine.selectAll(".points")
        .data(pointData)
        .enter().append("svg:circle")
        .style("cursor", "pointer")
        .attr("stroke", pointColor)
        .attr("fill", function (d, i) { return pointColor })
        .attr("cx", function (d, i) { return xScale(d.sample) })
        .attr("cy", function (d, i) { return yScale(d.value) })
        .attr("r", function (d, i) { return 3 })
        .on("mouseover", function (d) {

          // animate point useful when we have points ploted close to each other.
          d3.select(this)
            .transition()
            .duration(300)
            .attr("r", 6);

          // code block for tooltip
          tooltipDiv.transition()
            .duration(200)
            .style("opacity", .9);
          tooltipDiv.html(d.sample + ' : ' + d.value)
            .style("background", pointColor)
            .style("left", (d3.event.pageX) - 30 + "px")
            .style("top", (d3.event.pageY - 40) + "px");
        })
        .on("mouseout", function (d) {

          // animate point back to origional style
          d3.select(this)
            .transition()
            .duration(300)
            .attr("r", 3);

          tooltipDiv.transition()
            .duration(500)
            .style("opacity", 0);
        });
      return points;
    }

    function createLegend(legendColor, lineId, legendText) {

      var legendGroup = svg.append("g");

      legendGroup.append("rect")
        .attr("width", chartConfig.lineLabel.width + 5)
        .attr("height", chartConfig.lineLabel.height)
        .attr("x", (width/2 + marginLegend - 45) / 1.3)
        .attr("y", (margin.top - 15))
        .attr("stroke", legendColor)
        .attr("fill", legendColor)
        .attr("stroke-width", 1).style("opacity", 0).transition()
        .duration(600)
        .style("opacity", 1)


      legendGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('font-family', 'sans-serif')
        .style('cursor', 'pointer')
        .attr('font-size', '12px')
        .attr('fill', 'white')
        .attr("transform", "translate(" + ((width/2 + marginLegend) / 1.3) + "," + (margin.top) + ")")
        .text("X  " + legendText)
        .on("click", function () {
          var display = d3.select("." + lineId).style("display") != "none" ? 'none' : '';
          d3.select("." + lineId)
            .transition()
            .duration(500)
            .style("display", display)
        });
      marginLegend += 100;
    }

    function zoomToPeriod(from, to) {
      chartsContainer.call(zoom.x(xScale.domain([from, to])));
      updateAxis();
      updateCharts();
    }

    function updateCharts() {
      chartConfig.data.forEach(function (v, i) {
        const lineId = 'line-' + i
        updateLine(lineId, v)
        updatePoints(lineId, v);
      })
    }

    function updateAxis() {
      mainGroup.select(".x.axis").call(xAxis);
      mainGroup.select(".y.axis").call(yAxis);

      navViewport.extent(xScale.domain());
      navigatorGroup.select('.nav-viewport').call(navViewport);
    }

    function updateLine(lineId, lineData) {
      d3.select("#" + lineId)
        .data([lineData])
        .attr("d", line(lineData));
    }

    function updatePoints(lineId, pointData) {
      const points = d3.select("." + lineId).selectAll("circle");
      points.data(pointData)
        .attr("cx", function (d, i) {
          return xScale(d.sample)
        })
        .attr("cy", function (d, i) {
          return yScale(d.value)
        })
    }

    // chart data
    var chartConfig = {
      lineConnectorLength: 40,
      axisLabel: {
        xAxis: 'Sample',
        yAxis: 'Value'
      },
      lineLabel: {
        height: 20,
        width: 60,
      },

      data: data.map((series) => extractSampleData(series))
    };

    var minSample = d3.min(chartConfig.data.flat(), function (d) { return d.sample; })
    var maxSample = d3.max(chartConfig.data.flat(), function (d) { return d.sample; })

    var minValue = d3.min(chartConfig.data.flat(), function (d) { return d.value; })
    var maxValue = d3.max(chartConfig.data.flat(), function (d) { return d.value; })

    var margin = { top: 20, right: 20, bottom: 30, left: 100 },
      navigatorMarginTop = 30,
      navigatorHeight = 60,
      width = 1200 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom - navigatorHeight - navigatorMarginTop;
    var marginLegend = 0;

    var tickHeight = height, tickWidth = width
    var tickHeight = 0, tickWidth = 0

    var xScale = d3.scale.linear()
      .domain([minSample, maxSample])
      .range([0, width]);

    var yScale = d3.scale.linear()
      .domain([minValue, maxValue])
      .range([height, 0]);

    var xAxis = d3.svg.axis()
      .scale(xScale)
      .orient("bottom")
      .tickSize(-tickHeight)

    var yAxis = d3.svg.axis()
      .scale(yScale)
      .orient("left")
      .ticks(6)
      .tickSize(-tickWidth);

    var zoom = d3.behavior.zoom()
      .x(xScale);


    d3.select("body").select(".tooltip").html(null)
    d3.select("#track-3").html(null)

    // Define the div for the tooltip
    var tooltipDiv = d3.select("body").append("div")
      .attr("class", "tooltip");

    var svg = d3.select("#track-3").append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom + navigatorHeight + navigatorMarginTop);

    var mainGroup = svg.append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Clip-path
    var chartsContainer = mainGroup.append('g')
      .attr('clip-path', 'url(#plotAreaClip)')
      .call(zoom);

    chartsContainer.append('clipPath')
      .attr('id', 'plotAreaClip')
      .append('rect')
      .attr({ width: width, height: height });

    // Line chart
    var line = d3.svg.line()
      .x(function (d) {
        return xScale(d.sample);
      })
      .y(function (d) {
        return yScale(d.value);
      });

    let _this = this
    //const colorsMap = ["#00b7d4", "#f57738", "#f50038", "#f57738", "#f50038"]
    const colorsMap = _this.colors
    chartConfig.data.forEach(function (v, i) {
      const lineId = "line-" + i
      const fileName = _this.controller.model.audioFiles[i].name
      const line = drawLine(v, colorsMap[i], fileName, lineId);
      const points = drawPoints(v, colorsMap[i], line);
      createLegend(colorsMap[i], lineId, fileName);
    })

    // Axis
    mainGroup.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

    mainGroup.append("g")
      .attr("class", "y axis")
      .call(yAxis);

    // Navigator
    var navXScale = d3.scale.linear()
      .domain([minSample, maxSample])
      .range([0, width]);

    var navYScale = d3.scale.linear()
      .domain([minValue || 0, maxValue || 1])
      .range([navigatorHeight, 0]);

    var navXAxis = d3.svg.axis()
      .scale(navXScale)
      .orient("bottom");

    var navData = d3.svg.area()
      .interpolate("basis")
      .x(function (d) {
        return navXScale(d.sample);
      })
      .y0(navigatorHeight)
      .y1(function (d) {
        return navYScale(d.value);
      });

    var navigatorGroup = svg.append("g")
      .attr("class", "navigator")
      .attr("width", width + margin.left + margin.right)
      .attr("height", navigatorHeight + margin.top + margin.bottom)
      .attr("transform", "translate(" + margin.left + "," + (margin.top + height + navigatorMarginTop) + ")");

    navigatorGroup.append("path")
      .attr("class", "data")
      .attr("d", navData(chartConfig.data[0]));

    svg.append("g")
      .attr("class", "x nav-axis")
      .attr("transform", "translate(" + margin.left + "," + (margin.top + height + navigatorHeight + navigatorMarginTop) + ")")
      .call(navXAxis);

    // Navigator viewport
    var navViewport = d3.svg.brush()
      .x(navXScale)
      .extent(xScale.domain())
      .on("brush", display);

    navigatorGroup.append("g")
      .attr("class", "nav-viewport")
      .call(navViewport)
      .selectAll("rect")
      .attr("height", navigatorHeight);
  }

  renderSpectrogrom(waveformContainerSelector, spectrogramContainerSelector, filename) {
    d3.select(waveformContainerSelector).html(null)
    d3.select(spectrogramContainerSelector).html(null)

    var wavesurfer = WaveSurfer.create({
      // your options here
      container: waveformContainerSelector,
      waveColor: '#D2EDD4',
      progressColor: '#46B54D',
      plugins: [
        WaveSurfer.spectrogram.create({
          wavesurfer: wavesurfer,
          labels: true,
          container: spectrogramContainerSelector,
          //map generated via node.js repl and put into json.file
          colorMap: this.colorMap
        })
      ]
    });

    wavesurfer.load(filename);
  }

}


