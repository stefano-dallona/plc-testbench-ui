class RunsListModel {

    constructor(options) {
        this.runs = options && options.run || []
        this.input_path = options && options.input_path || []
    }

}