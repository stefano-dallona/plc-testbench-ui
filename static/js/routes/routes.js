const routes = {
    "/analysis": "/static/testbench-output-analysis.html",
    "/configuration": "/static/testbench-configuration.html",
    "/runs-list": "/static/testbench-runs-list.html",

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