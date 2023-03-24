class RunsListView {

    constructor(controller) {
        this.controller = controller
        this.controller.view = this
    }

    renderRuns() {
        let runSelect = document.getElementById("runs")
        runSelect.innerHTML = ""
        this.controller.model.runs.forEach((it) => {
          let myOption = document.createElement("option");
          myOption.text = it.run_id;
          myOption.value = it.run_id;
          runSelect.appendChild(myOption);
        })
    }

}