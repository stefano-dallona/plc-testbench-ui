class RunAnalysisController {
  audioContext
  view
  bufferLoader
  audioSource
  baseUrl

  constructor(model, plctestbenchService, runService) {
    this.model = model
    this.plctestbenchService = plctestbenchService
    this.baseUrl = plctestbenchService.baseUrl
    this.runService = runService
  }

  init() {
    this.loadInputFiles(this.model.run_id)
    d3.select(self.frameElement).style("height", "800px");

    const audioSelect = document.querySelector("#selectedInputFile");
    audioSelect.addEventListener('change', (e) => this.changeTrack(e.target));
    audioSelect.value = this.model.filename

    const playableFileSelect = document.querySelector("#aufiofileToBePlayed");
    playableFileSelect.addEventListener('change', (e) => this.model.selectedTrackToPlay = e.target.value);

    const startButton = document.querySelector("#Start");
    const pauseButton = document.querySelector("#Pause");
    startButton.onclick = () => {
      this.playSound(0, 0);
    }
    pauseButton.onclick = () => {
      this.pauseSound();
    }

    const leftButton = document.querySelector("#Left");
    const rightButton = document.querySelector("#Right");
    const prevousLossButton = document.querySelector("#LeftLoss");
    const nextLossButton = document.querySelector("#RightLoss");
    const playZoomedButton = document.querySelector("#PlayZoomed");

    leftButton.onclick = () => {
      const startat = Math.max(0, startat - numsamples)
      this.selectSamples(startat, numsamples)
    }
    rightButton.onclick = () => {
      const startat = Math.min(startat + numsamples, totalSamples - numsamples);
      this.selectSamples(startat, numsamples)
    }
    prevousLossButton.onclick = () => {
      var currentlySelectedSegmentIndex = this.view.segmentLayerOnWaveform.data.findIndex(element => element === this.model.selectedLoss);
      this.selectSegment(this.view.segmentLayerOnWaveform, Math.max(0, currentlySelectedSegmentIndex - 1))
    }
    nextLossButton.onclick = () => {
      var currentlySelectedSegmentIndex = this.view.segmentLayerOnWaveform.data.findIndex(element => element === this.model.selectedLoss);
      this.selectSegment(this.view.segmentLayerOnWaveform, Math.min(currentlySelectedSegmentIndex + 1, this.view.segmentLayerOnWaveform.data.length - 1))
    }
    playZoomedButton.onclick = () => {
      this.playInterval(Math.floor(-this.view.timelineWaveform.timeContext.offset), Math.ceil(this.view.timelineWaveform.timeContext.visibleDuration))
      this.view.updateCursor()
    }

    this.changeTrack(audioSelect)
  }

  async loadInputFiles(run_id) {
    let run = await runService.getRun(run_id)
    this.view.renderInputFiles(run.selected_input_files)
  }

  findAudioFiles(rootNode, predicate) {
    const isAudioNode = (x) => { return x.type == "OriginalTrackNode" || x.type == "ECCTrackNode" }
    const stopRecursion = (x) => { return x.type == "LostSamplesMaskNode" && this.model.selectedLossSimulationNode && x.name != this.model.selectedLossSimulationNode.name }
    const audioFiles = this.mapTreeToList(rootNode, predicate ? predicate : isAudioNode, x => x, stopRecursion)
    console.log("audioFiles:" + audioFiles + ", length: " + audioFiles.length)
    return audioFiles
  }

  findLossFiles(rootNode, predicate) {
    const isLossNode = (x) => { return x.type == "LostSamplesMaskNode" }
    const lossFiles = this.mapTreeToList(rootNode, predicate ? predicate : isLossNode, x => x)
    console.log("lossFiles:" + lossFiles + ", length: " + lossFiles.length)
    return lossFiles
  }

  findParent(rootNode, childNode) {
    const isParentOfNode = (x) => {
      return x.children && x.children.find(c => c.uuid = childNode.uuid)
    }
    const result = this.mapTreeToList(rootNode, isParentOfNode, x => x)
    return result instanceof Array && result.length > 0 ? result[0] : null
  }

  mapTreeToList(root, predicate = (x) => true, mapper = (x) => x, stopRecursion = (x) => false) {
    function _treeToList(root) {
      let accumulator = []
      if (predicate(root)) {
        accumulator.push(mapper(root))
      }
      if (root.children) {
        root.children.filter(x => !stopRecursion(x)).forEach((child) => {
          accumulator = accumulator.concat(_treeToList(child))
        })
      }
      return accumulator
    }

    return _treeToList(root)
  }

  clearTracks() {
    document.querySelector('#track-1').innerHTML = "";
    document.querySelector('#track-2').innerHTML = "";
    document.querySelector('#track-3').innerHTML = "";
  }

  populatePlayableFiles() {
    //let playableFiles = this.model.audioFiles.map((x) => { return { "name": x.name + "(" + this.findParent(this.model.root, x) + ")", "uuid": x.uuid }})
    this.view.populatePlayableFiles(this.model.audioFiles)
  }

  async loadTree(tracktitle) {
    this.model.filename = tracktitle
    let hierarchy = await this.runService.getRunHierarchy(this.model.run_id, this.model.filename)
    this.model.root = hierarchy;
    this.model.root.x0 = this.view.tree_height / 2;
    this.model.root.y0 = 0;

    this.view.renderRunHierarchy()
    this.view.updateRunHierarchy(this.model.root);
    this.clearTracks()
    this.model.audioFiles = this.findAudioFiles(this.model.root)
    this.model.lossFiles = this.findLossFiles(this.model.root)
    this.populatePlayableFiles()
    this.loadBuffer(this.model.audioFiles.map((x) =>  `${this.baseUrl}/analysis/runs/${this.model.run_id}/input-files/${x.uuid}/output-files/${x.uuid}`))
  }

  handleTreeClick() {
    const _controller = this
    return function handleTreeClick(d) {
      // Toggle children on click.
      if (d == _controller.model.root) {
        _controller.view.toggleWaveform(_controller.view.waveformTrack, _controller.view.layersMap, d)
      }
      if (d.type == "LostSamplesMaskNode") {
        _controller.model.loss_file = d
        _controller.model.selectedLossSimulationNode = d
        _controller.view.displayLostPacketsOnWaveForm(_controller.model.filename, _controller.model.loss_file);
        _controller.view.toggleWaveform(_controller.view.waveformTrack, _controller.view.layersMap, d)
      }
      if (d.type == "ECCTrackNode") {
        _controller.view.toggleWaveform(_controller.view.waveformTrack, _controller.view.layersMap, d)
      }
      console.log(`node.type: ${d.type}, node.file: ${d.file}, node.uuid: ${d.uuid}`)
    }
  }

  handleTreeDblclick() {
    const _controller = this
    return function handleTreeDblclick(d) {
      if (d.children) {
        d._children = d.children;
        d.children = null;
      } else {
        d.children = d._children;
        d._children = null;
      }
      if (d.type == "LostSamplesMaskNode") {
        _controller.model.loss_file = d.uuid
        _controller.model.selectedLossSimulationNode = d.uuid
        _controller.view.displayLostPacketsOnWaveForm(_controller.model.filename, _controller.model.loss_file)
      }
      _controller.view.updateRunHierarchy(d);
    }
  }

  expandAll() {
    expand(this.model.root);
    this.view.updateRunHierarchy(this.model.root);
  }

  collapseAll() {
    this.model.root.children.forEach(collapse);
    collapse(this.model.root);
    this.view.updateRunHierarchy(this.model.root);
  }

  changeTrack(selectObject) {
    var trackname = selectObject.value;
    console.log(trackname);
    this.loadTree(trackname)
  }

  loadBuffer = async (audioFiles) => {
    this.audioContext = new AudioContext()
    this.bufferLoader = new BufferLoader(
      this.audioContext,
      this.model.audioFiles.map((file) => {
        return `${this.baseUrl}/analysis/runs/${this.model.run_id}/input-files/${file.uuid}/output-files/${file.uuid}`
      }),
      this.view.renderWaveforms()
    );
    this.bufferLoader.load();
  }

  async fetchLostSamples(original_audio_node, loss_simulation_node) {
    const lostPacketsJson = await plctestbenchService.fetchLostSamples(this.model.run_id, 
      original_audio_node.uuid, loss_simulation_node.uuid, "seconds")
    return lostPacketsJson
  }

  playSound(delay, offset, duration) {
    this.model.startTime = this.audioContext.currentTime
    this.model.startOffset = 0
    if (!this.model.playing) {
      this.audioContext.resume()
      this.audioSource = this.audioContext.createBufferSource();
      this.audioSource.buffer = this.bufferLoader.bufferList[this.model.selectedTrackToPlay];
      this.audioSource.connect(this.audioContext.destination);
      this.audioSource.start(delay ? delay : 0, offset ? offset : 0, duration ? duration : this.audioSource.buffer.duration);
      this.model.playing = true
      console.log("source.buffer.duration:" + this.audioSource.buffer.duration);
    } else {
      console.log("Already playing ...")
    }
    this.view.updateCursor()()
  }

  pauseSound() {
    if (this.model.playing) {
      this.audioSource.stop()
      this.audioSource.disconnect(this.audioContext.destination)
      this.audioContext.suspend()
      this.model.startOffset = this.audioContext.currentTime
      this.model.playing = false
    } else {
      this.audioContext.resume()
      this.audioSource = this.audioContext.createBufferSource();
      this.audioSource.buffer = this.bufferLoader.bufferList[this.model.selectedTrackToPlay];
      this.audioSource.connect(this.audioContext.destination);
      this.audioSource.start(0, this.model.startOffset);
      this.model.playing = true
    }
    this.view.updateCursor()()
  }

  playInterval(start, duration) {
    this.audioContext.resume()
    this.audioSource = this.audioContext.createBufferSource();
    this.audioSource.buffer = this.bufferLoader.bufferList[this.model.selectedTrackToPlay];
    this.audioSource.connect(this.audioContext.destination);
    this.audioSource.start(0, start, duration);
    this.model.playing = true
  }

  selectSegment(segmentLayer, index) {
    var datum = segmentLayer.data[index];

    console.log("datum: (x:" + datum.x + ", width:" + datum.width + ", lossstart:" + datum.lossstart + ", losswidth:" + datum.losswidth + ")")
    if (this.model.selectedLoss) this.model.selectedLoss.color = undefined
    this.model.selectedLoss = datum
    this.model.selectedLoss.color = "red"
    this.view.segmentLayerOnWaveform.updateShapes();
    var segmentTimes = [Math.floor(this.model.selectedLoss.x), Math.ceil(this.model.selectedLoss.width)]
    this.playInterval(segmentTimes[0], segmentTimes[1])

    this.selectSamples(datum.lossstart, datum.losswidth)
  }

  async selectSamples(offset, num_samples, time_interval) {
    console.log("time_interval:" + time_interval + ", offset:" + offset + ", num_samples:" + num_samples)
    if (num_samples > 100000) {
      alert("Select a shorter range please")
      return;
    }

    //const samplesJson = await this.plctestbenchService.fetchSamplesFromFile(start, samples, this.model.filename, time_interval);
    let channel = 0;
    let unit_of_meas = "samples"

    const samplesData = await this.loadSamples(offset, num_samples, channel, unit_of_meas)
    this.view.renderSamples(samplesData)
  }

  async loadSamples(start, samples, channel, unit_of_meas) {
    let run_id = this.model.run_id
    const startat = start - samples
    const numsamples = 3 * samples

    let samplesSeries = []
    for(let index in this.model.audioFiles) {
      let file = this.model.audioFiles[index]
      let original_file_node_id = file.uuid
      let audio_file_node_id = file.uuid
      let fileSamples = await this.plctestbenchService.fetchSamplesFromFile(run_id, original_file_node_id, audio_file_node_id,
        channel, startat, numsamples, unit_of_meas)
      samplesSeries.push(fileSamples)
    }

    return samplesSeries
  }

  displaySpectrogram() {

  }

  hideSpectrogram() {

  }


}