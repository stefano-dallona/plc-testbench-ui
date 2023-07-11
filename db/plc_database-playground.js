// mongodb://root:Marmolada3343@localhost:27017

use('plc_database');
use('stefano_dot_dallona_at_gmail_dot_com');

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

db.getCollection("RunView").drop()
db.createView("RunView", "runs", [
  {
    $addFields: { 'run_id': '', 'description': '', 'classname': "Run" }
  },
  {
    $project: {
      _id: 1,
      classname: 1,
      run_id: "$_id",
      description: 1,
      status: 1,
      creator: "$creator",
      created_on: { "$dateToString":{"format":"%Y-%m-%dT%H:%M:%S", "date":"$created_on"}},
      selected_input_files: {
        $arrayElemAt: [ "$workers", 0 ]
      },
      lost_samples_masks: {
        $arrayElemAt: [ "$workers", 1 ]
      },
      reconstructed_tracks: {
        $arrayElemAt: [ "$workers", 2 ]
      },
      output_analysis: {
        $arrayElemAt: [ "$workers", 3 ]
      },
      nodes: 1
    }
  },
  {
      $project: {
        _id: 1,
        classname: 1,
        run_id: 1,
        description: 1,
        status: 1,
        creator: 1,
        created_on: 1,
        selected_input_files: {
          $map: {
              input: "$selected_input_files",
              in: "$$this.settings.filename"
          }
        },
        lost_samples_masks: {
          $map: {
              input: "$lost_samples_masks",
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
        reconstructed_tracks: {
          $map: {
              input: "$reconstructed_tracks",
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
        output_analysis: {
          $map: {
              input: "$output_analysis",
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
          "nodes": 0,
          "selected_input_files.name": 0,
          "selected_input_files.settings": 0,        
          "lost_samples_masks.name": 0,
          "lost_samples_masks.settings": 0,
          "reconstructed_tracks.name": 0,
          "reconstructed_tracks.settings": 0,
          "output_analysis.name": 0,
          "output_analysis.settings": 0
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
