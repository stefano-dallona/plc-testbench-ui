/* global use, db */
// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.

// The current database to use.
use('plc_database');

db["OriginalTrackNod"].deleteMany({})
db["LostSamplesMaskNode"].deleteMany({})
db["ReconstructedTrackNode"].deleteMany({})
db["OutputAnalysisNode"].deleteMany({})
db["Run"].deleteMany({})
db["Events"].deleteMany({})