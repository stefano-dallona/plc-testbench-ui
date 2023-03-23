const routes = {
    "/analysis": "/testbench-output-analysis.html",
    "/configuration": "/testbench-configuration.html",

    navigateTo: (page, params) => {
        function paramsToString(params) {
            return `run_id=${params["run_id"]}`
        }

        let destination = routes[page]
        document.location = `${destination}?${paramsToString(params)}`
    }
}