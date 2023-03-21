function create_UUID() {
    var dt = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = (dt + Math.random() * 16) % 16 | 0;
        dt = Math.floor(dt / 16);
        return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

class RunService {

    constructor(baseUrl) {
        this.baseUrl = baseUrl
    }

    async saveRunConfiguration(configuration) {
        const request = {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(configuration)
        };
        let response = await fetch(this.baseUrl + "/runs", request).catch((error) => {
            console.log(error)
        })
        if (response.ok) {
            let responseBody = await response.json()
            console.log("saveRunConfiguration: run_id: " + responseBody.run_id)
            return responseBody.run_id
        } else {
            return null
        }
    }

    async launchRunExecution(run_id) {
        const request = {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            }
        };
        let response = await fetch(this.baseUrl + "/runs/" + run_id + "/executions", request)
        let run_execution = await response.json()
        return run_execution
    }

    startListeningForExecutionEvents(run_id, execution_id, callback) {
        this.sseListener = new EventSource(`${this.baseUrl}/runs/${run_id}/executions/${execution_id}/events`);
        this.sseListener.addEventListener("run_execution", callback)
    }

    stopListeningForExecutionEvents() {
        if (this.sseListener) {
            this.sseListener.close();
        }
    }

    async getRunHierarchy(run_id, audio_file) {
        //let requestUrl = this.baseUrl + "/output_hierarchy?run_id=" + run_id + "&filename=" + audio_file
        let execution_id = run_id
        let requestUrl = this.baseUrl + `/runs/${run_id}/executions/${execution_id}/hierarchy`
        let response = await fetch(requestUrl)
        let run_hierarchy = await response.json()
        return run_hierarchy.find((node) => node.file.endsWith(audio_file))
    }

    async getSettingsMetadata() {
        let response = await fetch(this.baseUrl + "/settings_metadata")
        let settings_metadata = await response.json()
        return settings_metadata
    }

    async getLossSimulators() {
        let response = await fetch(this.baseUrl + "/loss_simulators")
        let loss_simulators = await response.json()
        return loss_simulators
    }

    async getLossModels() {
        let response = await fetch(this.baseUrl + "/loss_models")
        let loss_models = await response.json()
        return loss_models
    }

    async getEccAlgorithms() {
        let response = await fetch(this.baseUrl + "/ecc_algorithms")
        let ecc_algorithms = await response.json()
        return ecc_algorithms
    }

    async getOutputAnalysers() {
        let response = await fetch(this.baseUrl + "/output_analysers")
        let output_analysers = await response.json()
        return output_analysers
    }

    async getInputFiles(path) {
        let response = await fetch(this.baseUrl + "/input_files?path=" + path)
        let input_files = await response.json()
        return input_files
    }

    async getRun(run_id) {
        let response = await fetch(`${this.baseUrl}/runs/${run_id}`)
        let run = await response.json()
        return run
    }

}