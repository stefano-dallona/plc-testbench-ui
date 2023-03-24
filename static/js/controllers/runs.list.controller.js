
class RunsListController {

    constructor(model, runService, routes) {
        this.model = model
        this.runService = runService
        this.routes = routes
    }

    init() {
        this.findAllRuns()

        let analyseButton = document.getElementById("Analyse")
        let _this = this
        analyseButton.addEventListener("click", (event) => {
            _this.routes.navigateTo("/analysis", { "run_id": document.getElementById("runs").value})
        });
    }

    async findAllRuns() {
        this.model.runs = await runService.findAllRuns()
        this.view.renderRuns()
    }

}