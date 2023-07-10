// mongodb://root:Marmolada3343@localhost:27017

use('plc_database');

db.getCollection("OriginalTrackNode").find({ "filename": /.*Blues_Bass.*/ }, { "_id": 1, "parent": 1 }).sort({ "_id": 1 });

db.getCollection("LostSamplesMaskNode").find({ "_id": Long("648878394406601900") })
db.getCollection("ReconstructedTrackNode").find({ "parent": Long("2180981324253297200") })
db.getCollection("OutputAnalysisNode").find({ "parent": Long("2180981324253297200") })

db.OriginalTrackNode.aggregate([
  {
    $graphLookup: {
      from: "LostSamplesMaskNode",
      startWith: "$_id",
      connectFromField: "_id",
      connectToField: "parent",
      maxDepth: 1,
      as: "lostSamplesMasks"
    }
  }
])

db.LostSamplesMaskNode.aggregate([
  {
    $graphLookup: {
      from: "ReconstructedTrackNode",
      startWith: "$_id",
      connectFromField: "_id",
      connectToField: "parent",
      maxDepth: 1,
      as: "reconstructedTracks"
    }
  }
])

db.ReconstructedTrackNode.aggregate([
  {
    $graphLookup: {
      from: "OutputAnalysisNode",
      startWith: "$_id",
      connectFromField: "_id",
      connectToField: "parent",
      maxDepth: 1,
      as: "outputAnalysis"
    }
  }
])

db.getCollection("OriginalTrack-1").drop()
db.getCollection("OriginalTrack-2").drop()
db.getCollection("OriginalTrack-3").drop()
db.getCollection("OriginalTrack-4").drop()

db.createView("OriginalTrack-1", "ReconstructedTrackNode", [{
  $graphLookup: {
    from: "OutputAnalysisNode",
    startWith: "$_id",
    connectFromField: "_id",
    connectToField: "parent",
    maxDepth: 1,
    as: "outputAnalysis"
  }
}])

db.createView("OriginalTrack-2", "LostSamplesMaskNode", [{
  $graphLookup: {
    from: "OriginalTrack-1",
    startWith: "$_id",
    connectFromField: "_id",
    connectToField: "parent",
    maxDepth: 2,
    as: "reconstructedTracks"
  }
}])

db.createView("OriginalTrack-3", "OriginalTrackNode", [{
  $graphLookup: {
    from: "OriginalTrack-2",
    startWith: "$_id",
    connectFromField: "_id",
    connectToField: "parent",
    maxDepth: 3,
    as: "lostSamplesMasks"
  }
}])

db.createView("OriginalTrack-4", "runs", [{
  $graphLookup: {
    from: "OriginalTrack-3",
    startWith: "$_id",
    connectFromField: "_id",
    connectToField: "run_id",
    maxDepth: 4,
    as: "originalTracks"
  }
}])

db.getCollection("RunView").drop()
db.createView("RunView", "runs", [
  {
    $project: {
      _id: 1,
      selected_input_files: {
        $map: {
          input: "$nodes",
          as: "node",
          in: "$$node._id"
        }
      },
      workers: 1,
      nodes: 1
    }
  },
  {
    $lookup: {
      from: "OriginalTrackNode",
      localField: "selected_input_files",
      foreignField: "_id",
      as: "selected_input_files"
    }
  },
  {
    $project: {
      _id: 1,
      selected_input_files:
      {
        $sortArray:
        {
          input: {
            $map: {
              input: "$selected_input_files",
              as: "input_file",
              in: { $last: { $split: ["$$input_file.filename", "\\"] } }
            }
          },
          sortBy: 1
        }
      },
      lostSamplesMasks: {
        $arrayElemAt: [ "$workers", 0 ]
      },
      reconstructedTracks: {
        $arrayElemAt: [ "$workers", 1 ]
      },
      outputAnalysis: {
        $arrayElemAt: [ "$workers", 2 ]
      },
      nodes: 1
    }
  }
])

db.createView("RunView", "runs", [
  {
    $addFields: { 'runId': '', 'description': '', 'status': '', 'createdBy': '', 'createdOn': '' }
  },
  {
    $project: {
      _id: 1,
      runId: 1,
      description: 1,
      status: 1,
      createdBy: 1,
      createdOn: 1,
      selected_input_files: 1,
      lostSamplesMasks: {
        $arrayElemAt: [ "$workers", 0 ]
      },
      reconstructedTracks: {
        $arrayElemAt: [ "$workers", 1 ]
      },
      outputAnalysis: {
        $arrayElemAt: [ "$workers", 2 ]
      },
      nodes: 1
    }
  },
  {
      $project: {
        _id: 1,
        runId: 1,
        description: 1,
        status: 1,
        createdBy: 1,
        createdOn: 1,
        selected_input_files: 1,
        lostSamplesMasks: {
          $map: {
              input: "$lostSamplesMasks",
              in: {
                  $mergeObjects: [
                      {
                          worker: "$$this.name"
                      },
                      "$$this",
                      "$$this.settings"
                  ]
              }
          }
        },
        reconstructedTracks: {
          $map: {
              input: "$reconstructedTracks",
              in: {
                  $mergeObjects: [
                      {
                          worker: "$$this.name"
                      },
                      "$$this",
                      "$$this.settings"
                  ]
              }
          }
        },
        outputAnalysis: {
          $map: {
              input: "$outputAnalysis",
              in: {
                  $mergeObjects: [
                      {
                          worker: "$$this.name"
                      },
                      "$$this",
                      "$$this.settings"
                  ]
              }
          }
        },
        nodes: 1
      }
    },
    {
      $project: {
          "lostSamplesMasks.name": 0,
          "lostSamplesMasks.settings": 0,
          "reconstructedTracks.name": 0,
          "reconstructedTracks.settings": 0,
          "outputAnalysis.name": 0,
          "outputAnalysis.settings": 0
      }
    }
])

db.getCollection("RunView").find({})

db.runs.aggregate([
  {
    $project: {
      _id: 1,
      input_files: {
        $map: {
          input: "$nodes",
          as: "node",
          in: "$$node._id"
        }
      }
    }
  },
  {
    $lookup: {
      from: "OriginalTrackNode",
      localField: "input_files",
      foreignField: "_id",
      as: "input_files"
    }
  },
  {
    $project: {
      _id: 1,
      input_files: {
        $map: {
          input: "$input_files",
          as: "selected_input_files",
          in: { $last: { $split: ["$$input_file.filename", "\\"] } }
        }
      }
    }
  }
])

db.getCollection("OriginalTrack-3").find(
  {
    $and: [
      {
        "filename": /.*Musica.*/,
        "lostSamplesMasks": {
          $elemMatch: {
            "filename": /.*BinomialPLS.*/
          }
        }
      }]
  },
  { "_id": 1 }
)

// Query by OriginalTrackNode's and LostSamplesMaskNode's attributes
db.getCollection("OriginalTrack-3").find(
  {
    $and: [
      {
        "filename": /.*Musica.*/,
        "lostSamplesMasks": {
          $elemMatch: {
            "filename": /.*GilbertElliotPLS.*/
          }
        }
      }]
  },
  { "_id": 1 }
)

// Query by OriginalTrackNode's and ReconstructedTrackNode's attributes
db.getCollection("OriginalTrack-3").find(
  {
    $and: [
      {
        "filename": /.*Musica.*/,
        "lostSamplesMasks.reconstructedTracks": {
          $elemMatch: {
            "filename": /.*ZerosPLC.*/
          }
        }
      }]
  },
  { "_id": 1 }
)

// Query by OriginalTrackNode's and OutputAnaliysisNode's attributes
db.getCollection("OriginalTrack-3").find(
  {
    $and: [
      {
        "filename": /.*Musica.*/,
        "lostSamplesMasks.reconstructedTracks.outputAnalysis": {
          $elemMatch: {
            "filename": /.*MSECalculator.*/
          }
        }
      }]
  },
  { "_id": 1 }
)
