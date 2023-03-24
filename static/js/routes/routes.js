const routes = {
    "/analysis": "/static/testbench-output-analysis.html",
    "/configuration": "/static/testbench-configuration.html",

    navigateTo: (page, params) => {
        function paramsToString(params) {
            return `run_id=${params["run_id"]}`
        }

        let destination = routes[page]
        document.location = `${destination}?${paramsToString(params)}`
    }
}