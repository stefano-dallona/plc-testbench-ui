class PlcTestbenchService {

    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async fetchLostSamples(run_id, original_file_node_id, loss_simulation_node_id, unit_of_meas) {
        const lostPacketsResponse = await fetch(`${this.baseUrl}/analysis/runs/${run_id}/input-files/${original_file_node_id}/loss-simulations/${loss_simulation_node_id}?unit_of_meas=${unit_of_meas}`);
        const lostPacketsJson = await lostPacketsResponse.json();
        return lostPacketsJson;
    }

    async fetchSamplesFromFile(run_id, original_file_node_id, audio_file_node_id, channel, offset, num_samples, unit_of_meas) {
        const samplesResponse = await fetch(`${this.baseUrl}/analysis/runs/${run_id}/input-files/${original_file_node_id}/output-files/${audio_file_node_id}/samples?channel=${channel}&offset=${offset}&num_samples=${num_samples}&unit_of_meas=${unit_of_meas}`);
        const samplesJson = await samplesResponse.json();
        return samplesJson;
    }

    async fetchMetricsFromFile(run_id, original_file_node_id, audio_file_node_id, metric_node_id, channel, offset, num_samples, unit_of_meas) {
        const metricsResponse = await fetch(`${this.baseUrl}/analysis/runs/${run_id}/input-files/${original_file_node_id}/output-files/${audio_file_node_id}/metrics/${metric_node_id}?channel=${channel}&offset=${offset}&num_samples=${num_samples}&unit_of_meas=${unit_of_meas}`)
        const metricsJson = await metricsResponse.json();
        return metricsJson;
    }
}