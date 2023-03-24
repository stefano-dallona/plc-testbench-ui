

class RunConfigurationController {

    constructor(model, runService, routes) {
        this.model = model
        this.runService = runService
        this.view = null
        this.sseListener = null
        this.routes = routes
    }

    init(inputFilePath) {
        this.inputFilePath = inputFilePath

        let _this = this

        let addLossSimulatorButton = document.getElementById("btn_add_loss_simulator");
        addLossSimulatorButton.addEventListener("click", (event) => {
            _this.addLossSimulatorControls()
        });

        let saveButton = document.getElementById("btn_save");
        saveButton.addEventListener("click", async function (event) {
            _this.model.settings = _this.buildModelFromView()
            await _this.saveRunConfiguration()
            _this.model.current_file_index = 0
            _this.model.run_hierarchy = await _this.getRunHierarchy()
            _this.view.renderRunHierarachy(_this.model.run_hierarchy)
            _this.view.resetProgressBars(0)
        });

        let executeRunButton = document.getElementById("btn_run");
        executeRunButton.addEventListener("click", async function (event) {
            _this.model.current_file_index = 0
            _this.model.run_hierarchy = await _this.getRunHierarchy()
            _this.view.renderRunHierarachy(_this.model.run_hierarchy)
            _this.view.resetProgressBars(0)
            if (_this.model.run_id) {
                await _this.launchRunExecution(_this.model.run_id)
                _this.startListeningForExecutionEvents(_this.model.run_id, _this.model.execution_id)
            }
        });

        let runListButton = document.getElementById("btn_run_list");
        runListButton.addEventListener("click", async function (event) {
            _this.routes.navigateTo("/runs-list", {})
        });

        this.view.renderSettingsForm()
        this.loadLossSimulators('lossSimulator-0')
        this.loadLossModels('lossModel-0')
        this.loadEccAlgorithms()
        this.loadOutputAnalysers()
        this.loadInputFiles(inputFilePath)

        this.view.renderFileUploader()
        this.view.renderSettingsForm()
    }

    startListeningForExecutionEvents(sseBaseUrl) {
        let _this = this
        let progressBarIdPrefix = "pb-"

        let progressCallback = async function (e) {
            let message = JSON.parse(e.data)
            let progressBar = _this.view.pbsMap[progressBarIdPrefix + message.nodeid]
            if (progressBar) {
                progressBar.update(message.currentPercentage)
            }
            if (message.nodetype == "RunExecution" && message.nodeid == _this.model.run_id) {
                _this.view.resetProgressBars(100)
                _this.runService.stopListeningForExecutionEvents();
                _this.view.notifyRunCompletion(_this.model.run_id)
                routes.navigateTo("/analysis", { "run_id": _this.model.run_id })
            }
            if (message.nodetype == "ECCTestbench") {
                let runExecutionProgressBarId = progressBarIdPrefix + _this.model.run_id
                let input_files = _this.getSelectedFiles()
                let new_file_index = Math.min(input_files.length - 1, Math.ceil(input_files.length * (message.currentPercentage / 100.0)))
                if (new_file_index == _this.model.current_file_index) return
                _this.model.current_file_index = new_file_index
                _this.model.run_hierarchy = await _this.getRunHierarchy()
                _this.view.renderRunHierarachy(_this.model.run_hierarchy)
                _this.view.resetProgressBars(0)
                _this.view.updateProgressBar(runExecutionProgressBarId, message.currentPercentage)
            }
        }
        runService.startListeningForExecutionEvents(this.model.run_id, this.model.run_id, progressCallback)
    }

    getSelectedFiles() {
        let _this = this
        return (() => Array.isArray(_this.model.settings.selectedInputFiles) ? _this.model.settings.selectedInputFiles : [_this.model.settings.selectedInputFiles])()
    }

    async saveRunConfiguration() {
        this.model.run_id = await runService.saveRunConfiguration(this.model.settings)
    }

    async loadRunConfiguration() {
        //this.model.settings = runService.loadRunConfiguration(this.model.run_id)
        runService.loadRunConfiguration(this.model.run_id)
    }

    async launchRunExecution(run_id) {
        this.model.run_id = run_id
        this.model.current_file_index = 0
        this.model.execution_id = runService.launchRunExecution(this.model.run_id)
    }

    async getSettingsMetadata() {
        let settings_metadata = await runService.getSettingsMetadata()
        return settings_metadata
    }

    async getRunHierarchy() {
        let run_hierarchy = await runService.getRunHierarchy(this.model.run_id, this.getSelectedFiles()[this.model.current_file_index])
        return run_hierarchy
    }

    buildModelFromView() {
        let runSettingsData = this.view.getRunConfigurationData()
        let runSettings = {}
        runSettingsData.forEach((value, key) => {
            if (!Reflect.has(runSettings, key)) {
                runSettings[key] = value
                return;
            }
            if (!Array.isArray(runSettings[key])) {
                runSettings[key] = [runSettings[key]]
            }
            runSettings[key].push(value)
        })
        console.log("run settings: " + runSettings)
        return runSettings
    }

    async addLossSimulatorControls() {
        let loss_simulators = await runService.getLossSimulators()
        let loss_models = await runService.getLossModels()
        this.view.addLossSimulatorControls(loss_simulators, loss_models)
    }

    async loadLossSimulators(selectId) {
        let loss_simulators = await runService.getLossSimulators()
        this.view.renderLossSimulators(selectId, loss_simulators)
    }

    async loadLossModels(selectId) {
        let loss_models = await runService.getLossModels()
        this.view.renderLossModels(selectId, loss_models)
    }

    async loadEccAlgorithms() {
        let ecc_algorithms = await runService.getEccAlgorithms()
        this.view.renderEccAlgorithms(ecc_algorithms)
    }

    async loadOutputAnalysers() {
        let output_analysers = await runService.getOutputAnalysers()
        this.view.renderOutputAnalysers(output_analysers)
    }

    async loadInputFiles(path) {
        let input_files = await runService.getInputFiles(path)
        this.view.renderInputFiles(input_files)
    }

}