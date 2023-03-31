const routes = {
    "/analysis": "./testbench-output-analysis.html",
    "/configuration": "./testbench-configuration.html",
    "/runs-list": "./testbench-runs-list.html",

    navigateTo: (page, params) => {
        function paramsToString(params) {
            let queryString = ""
            for (const [key, value] of Object.entries(params)) {
                queryString += (queryString != "") ? "&" : ""
                queryString += `${key}=${value}`
            }
            return `run_id=${params["run_id"]}`
        }

        let destination = routes[page]
        document.location = `${destination}?${paramsToString(params)}`
    }
}