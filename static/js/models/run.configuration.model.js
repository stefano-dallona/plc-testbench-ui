
class RunConfigurationModel {
    run_hierarchy
    current_file_index = 0
    
    constructor(uuid, settings) {
        this.uuid = uuid
        this.settings = settings
    }
}