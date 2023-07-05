// mongodb://root:Marmolada3343@itwn9370.biz.electrolux.com:27017

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
      workers: {
        $reduce: {
          input: '$workers',
          initialValue: [],
          in: { $concatArrays: ['$$value', '$$this'] }
        }
      },
      nodes: 1
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
