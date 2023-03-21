class RunAnalysisModel {
    playing = false
    startTime = 0
    startOffset = 0
    input_path

    constructor(options) {
        this.input_path = options && options.input_path || "./"
        this.duration = options && options.duration || 750
        this.root = options && options.root || undefined
        this.selectedLossSimulationNode = options && options.selectedLossSimulationNode || undefined
        this.audioFiles = options && options.audioFiles || []
        this.lossFiles = options && options.lossFiles || []
        this.filename = options && options.filename || undefined
        this.run_id = options && options.run_id || undefined
    }
}
