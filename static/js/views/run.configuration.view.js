//import '../controllers/run.configuration.controller'


class RunConfigurationView {

    constructor(controller) {
        this.controller = controller
        this.controller.view = this
        this.nodeIds = []
        this.pbsMap = {}
    }

    notifyRunCompletion(run_id) {
        alert("Elaboration of run '" + run_id + "' completed successfully!")
    }

    getRunConfigurationData() {
        const form = document.getElementById("run-configuration-form");
        return new FormData(form);
    }

    renderFileUploader() {
        let _this = this
        Dropzone.options.dropper = {
            paramName: 'file',
            addRemoveLinks: true,
            chunking: true,
            forceChunking: true,
            url: this.controller.runService.baseUrl + "/upload",
            maxFiles: 20,
            maxFilesize: 1025,
            chunkSize: 1000000,
            acceptedFiles: '.wav',
            init: function () {
                let _this = this
                var clearButton = document.getElementById("clear-dropzone")
                clearButton.addEventListener("click", function () {
                    _this.removeAllFiles();
                });
            },
            success: (function () {
                return function (file, response) {
                    this.removeFile(file);
                    _this.controller.loadInputFiles(_this.controller.inputFilePath)
                }
            })()
        }
    }

    async renderSettingsForm() {
        const settingsMetadata = await this.controller.getSettingsMetadata()

        let settingsForm = document.getElementById('settings');
        settingsForm.innerHTML = ""

        settingsMetadata.forEach((it) => {
            let aDiv = document.createElement("div");
            let aLabel = document.createElement("span");
            let aControl = document.createElement("input");
            aLabel.innerHTML = it.name + " (" + it.type + ")"
            aLabel.className = "label"
            aControl.id = it.name
            aControl.name = it.name
            aControl.value = it.value
            aControl.className = "setting"

            settingsForm.appendChild(aDiv);
            aDiv.appendChild(aLabel);
            aDiv.appendChild(aControl);
        })
    }

    addLossSimulatorControls(loss_simulators, loss_models) {
        let lossSimulators = document.getElementById('lossSimulators');
        let lossModels = document.getElementById('lossModels');

        let index = lossSimulators.getElementsByClassName("lossSimulator").length

        let lossSimulatorDiv = document.createElement("div");
        lossSimulatorDiv.id = "lossSimulatorDiv-" + index;
        lossSimulatorDiv.className = "lossSimulator"
        lossSimulators.appendChild(lossSimulatorDiv)
        let lossSimulatorSelect = document.createElement("select");
        lossSimulatorDiv.appendChild(lossSimulatorSelect)
        let lossSimulatorId = "lossSimulator-" + index;
        lossSimulatorSelect.id = lossSimulatorId;
        lossSimulatorSelect.name = lossSimulatorId;
        lossSimulatorSelect.className = "lossSimulator"

        this.renderLossSimulators(lossSimulatorId, loss_simulators)

        let lossModelDiv = document.createElement("div");
        lossModelDiv.id = "lossModelDiv-" + index;
        lossModelDiv.className = "lossModel"
        lossModels.appendChild(lossModelDiv)
        let lossModelSelect = document.createElement("select");
        lossModelDiv.appendChild(lossModelSelect)
        let lossModelId = "lossModel-" + index;
        lossModelSelect.id = lossModelId;
        lossModelSelect.name = lossModelId;
        lossModelSelect.className = "lossModel"

        this.renderLossModels(lossModelId, loss_models)

        let deleteButton = document.createElement("button");
        deleteButton.id = "deleteSimulator-" + index;
        deleteButton.innerHTML = "&nbsp; - &nbsp;"
        deleteButton.addEventListener("click", (event) => {
            let index = (event.srcElement.id + "").replaceAll("deleteSimulator-", "")
            console.log("deleteButton on index: " + index)
            document.getElementById('lossSimulatorDiv-' + index).remove()
            document.getElementById('lossModelDiv-' + index).remove()
        });
        lossModelDiv.appendChild(deleteButton)
    }

    renderLossSimulators(selectId, loss_simulators) {
        let mySelect = document.getElementById(selectId);

        loss_simulators.forEach((it) => {
            let myOption = document.createElement("option");
            myOption.text = it;
            myOption.value = it;
            mySelect.appendChild(myOption);
        })
    }

    renderLossModels(selectId, loss_models) {
        let mySelect = document.getElementById(selectId);

        loss_models.forEach((it) => {
            let myOption = document.createElement("option");
            myOption.text = it;
            myOption.value = it;
            mySelect.appendChild(myOption);
        })
    }

    renderEccAlgorithms(ecc_algorithms) {
        let mySelect = document.getElementById('eccAlgorithms');

        ecc_algorithms.forEach((it) => {
            let myOption = document.createElement("option");
            myOption.text = it;
            myOption.value = it;
            mySelect.appendChild(myOption);
        })
    }

    renderOutputAnalysers(output_analysers) {
        let mySelect = document.getElementById('outputAnalysers');

        output_analysers.forEach((it) => {
            let myOption = document.createElement("option");
            myOption.text = it;
            myOption.value = it;
            mySelect.appendChild(myOption);
        })
    }

    renderInputFiles(input_files) {
        let mySelect = document.getElementById('selectedInputFiles');

        mySelect.innerHTML = ""
        input_files.forEach((it) => {
            let myOption = document.createElement("option");
            myOption.text = it;
            myOption.value = it;
            mySelect.appendChild(myOption);
        })
    }

    renderRunHierarachy(data) {
        d3.select("#hierarchy").html(null)

        // Set the dimensions and margins of the diagram
        let margin = { top: 20, right: 90, bottom: 30, left: 90 },
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        // append the svg object to the body of the page
        // appends a 'group' element to 'svg'
        // moves the 'group' element to the top left margin
        let svg = d3.select("#hierarchy").append("svg")
            .attr("width", width + margin.right + margin.left)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate("
                + margin.left + "," + margin.top + ")");

        let i = 0,
            duration = 750,
            root;

        // declares a tree layout and assigns the size
        let treemap = d3.tree().size([height, width]);

        // Assigns parent, children, height, depth
        root = d3.hierarchy(data, function (d) {
            d.id = d.uuid
            return d.children
        });
        root.x0 = height / 2;
        root.y0 = 0;

        // Assigns the x and y position for the nodes
        let treeData = treemap(root);

        // Compute the new tree layout.
        let nodes = treeData.descendants(),
            links = treeData.descendants().slice(1);

        // Normalize for fixed-depth.
        nodes.forEach(function (d) { d.y = d.depth * 180 });

        // ****************** Nodes section ***************************

        // Update the nodes...
        let node = svg.selectAll('g.node')
            .data(nodes, function (d) {
                return d.id || (d.id = d.data.uuid);
            });

        // Enter any new modes at the parent's previous position.
        let nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr("transform", function (d) {
                return "translate(" + root.y0 + "," + root.x0 + ")";
            })
            .on('click', click);

        // Add Circle for the nodes
        nodeEnter.append('circle')
            .attr('class', 'node')
            .attr('r', 1e-6)
            .style("fill", function (d) {
                return d._children ? "lightsteelblue" : "#fff";
            });

        // Add labels for the nodes
        nodeEnter.append('text')
            .attr("dy", ".35em")
            .attr("x", function (d) {
                return d.children || d._children ? -25 : 25;
            })
            .attr("text-anchor", function (d) {
                return d.children || d._children ? "end" : "start";
            })
            .text(function (d) { return d.data.name; });

        // UPDATE
        let nodeUpdate = nodeEnter.merge(node);

        // Transition to the proper position for the node
        nodeUpdate.transition()
            .duration(duration)
            .attr("transform", function (d) {
                return "translate(" + d.y + "," + d.x + ")";
            });

        // Update the node attributes and style
        nodeUpdate.select('circle.node')
            .attr('r', 10)
            .style("fill", function (d) {
                return d._children ? "lightsteelblue" : "#fff";
            })
            .attr('cursor', 'pointer');

        // Remove any exiting nodes
        let nodeExit = node.exit().transition()
            .duration(duration)
            .attr("transform", function (d) {
                return "translate(" + root.y + "," + root.x + ")";
            })
            .remove();

        // On exit reduce the node circles size to 0
        nodeExit.select('circle')
            .attr('r', 1e-6);

        // On exit reduce the opacity of text labels
        nodeExit.select('text')
            .style('fill-opacity', 1e-6);

        // ****************** links section ***************************

        // Update the links...
        let link = svg.selectAll('path.link')
            .data(links, function (d) { return d.id; });

        // Enter any new links at the parent's previous position.
        let linkEnter = link.enter().insert('path', "g")
            .attr("class", "link")
            .attr('d', function (d) {
                var o = { x: root.x0, y: root.y0 }
                return diagonal(o, o)
            });

        // UPDATE
        let linkUpdate = linkEnter.merge(link);

        // Transition back to the parent element position
        linkUpdate.transition()
            .duration(duration)
            .attr('d', function (d) { return diagonal(d, d.parent) });

        // Remove any exiting links
        let linkExit = link.exit().transition()
            .duration(duration)
            .attr('d', function (d) {
                var o = { x: source.x, y: source.y }
                return diagonal(o, o)
            })
            .remove();

        // Store the old positions for transition.
        nodes.forEach(function (d) {
            d.x0 = d.x;
            d.y0 = d.y;
        });

        let _this = this

        // Creates a curved (diagonal) path from parent to the child nodes
        function diagonal(s, d) {

            let path = `M ${s.y} ${s.x}
        C ${(s.y + d.y) / 2} ${s.x},
          ${(s.y + d.y) / 2} ${d.x},
          ${d.y} ${d.x}`

            return path
        }

        // Toggle children on click.
        function click(d) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else {
                d.children = d._children;
                d._children = null;
            }
            update(d);
        }

        function expandAll() {
            expand(root);
            update(root);
        }
    
        function collapseAll() {
            root.children.forEach(collapse);
            collapse(root);
            update(root);
        }

        function createElaborationProgressBar(svg, run_id) {
            let group = svg.append("g")
                .attr("class", "elaboration")
                .attr("id", "pb-" + run_id)
    
            let circle = group.append("circle")
                .attr("cx", 50)
                .attr("cy", 50)
                .attr("r", 30)
    
            return group
        }

        function radialProgress(selector) {
            const parent = d3.select(selector)
    
            if (!parent._groups[0][0]) return

            var x = parent._groups[0][0].childNodes[0].cx.baseVal.value
            var y = parent._groups[0][0].childNodes[0].cy.baseVal.value
            var r = parent._groups[0][0].childNodes[0].r.baseVal.value
    
            const size = { "x": x, "y": y, "width": r * 2, "height": r * 2 }
            console.log(`x:${size.x},y:${size.y}`)
    
            const outerRadius = size.height;
            const thickness = size.height / 5;
            let value = 0;
    
            const mainArc = d3.arc()
                .startAngle(0)
                .endAngle(Math.PI * 2)
                .innerRadius(outerRadius - thickness)
                .outerRadius(outerRadius)
    
            parent.append("path")
                .attr('class', 'progress-bar-bg')
                .attr('transform', `translate(${size.x},${size.y})`)
                .attr('d', mainArc())
    
            const mainArcPath = parent.append("path")
                .attr('class', 'progress-bar')
                .attr('transform', `translate(${size.x},${size.y})`)
    
            let percentLabel = parent.append("text")
                .attr('class', 'progress-label')
                .attr('transform', `translate(${size.x},${size.y})`)
                .text('0')
    
            return {
                update: function (progressPercent) {
                    const startValue = value
                    const startAngle = Math.PI * startValue / 50
                    const angleDiff = Math.PI * progressPercent / 50 - startAngle;
                    const startAngleDeg = startAngle / Math.PI * 180
                    const angleDiffDeg = angleDiff / Math.PI * 180
                    const transitionDuration = 1500
    
                    mainArcPath.transition().duration(transitionDuration).attrTween('d', function () {
                        return function (t) {
                            mainArc.endAngle(startAngle + angleDiff * t)
                            return mainArc();
                        }
                    })
    
                    percentLabel.transition().duration(transitionDuration).tween('bla', function () {
                        return function (t) {
                            percentLabel.text(Math.round(startValue + (progressPercent - startValue) * t));
                        }
                    })
    
                    value = progressPercent
                }
            }
        }

        this.nodeIds = []
        this.pbsMap = {}

        let elaborationPb = createElaborationProgressBar(svg, this.controller.model.run_id);
        let elaborationPbId = "pb-" + this.controller.model.run_id
        this.nodeIds.push(elaborationPbId)
        this.pbsMap[elaborationPbId] = elaborationPb

        d3.selectAll('g.node').each(function (d, i) {
            const node = d3.select(this).node()
            console.log("g.node.id:" + node.id)
            node.id = "pb-" + d.data.uuid
            node.classList.add(d.data.type)
            _this.nodeIds.push(node.id)
        })

        let progressBars = this.nodeIds.map((id) => {
            let progressBar = null
            let pb = d3.select('#' + id).select('.progress-bar').node()
            if (!pb) {
                progressBar = radialProgress(`#${id}`)
                this.pbsMap[id] = progressBar
                let savedPercentage = localStorage.getItem(id)
                if (savedPercentage) {
                    _this.updateProgressBar(id, parseInt(savedPercentage))
                }
            }
            return progressBar
        })

        if (_this.sseListener) {
            function addProgressBarListener(evtSource, progressBarId) {
                _this.sseListener.addEventListener(progressBarId, (event) => {
                    _this.updateProgressBar(event.type, data.currentPercentage)
                });
            }
            this.nodeIds.forEach((id) => {
                addProgressBarListener(this.controller.sseListener, id)
            })
        }
    }

    resetProgressBars(progressPercent = 0, includeOverallProgressbar = true, run_id = "") {
        let _this = this
        this.nodeIds.forEach((id) => {
            if (!includeOverallProgressbar || id != run_id) {
                _this.updateProgressBar(id, progressPercent)
            }
        })
    }

    updateProgressBar(id, progressPercent) {
        let progressBar = this.pbsMap[id]
        if (progressBar) {
            progressBar.update(progressPercent)
            localStorage.setItem(id, progressPercent)
        }
    }
}