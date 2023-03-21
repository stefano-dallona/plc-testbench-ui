var appConfig = function(options) {
    function extractRunIdFromLocation() {
        const queryString = window.location.search
        const params = new URLSearchParams(queryString);
        return params.get("run_id");
    }
    return {
        backendBaseUrl: options.backendBaseUrl || "http://localhost:5000",
        rootFolder: options.rootFolder || "./original_tracks",
        run_id: options.run_id || extractRunIdFromLocation()
    }
}