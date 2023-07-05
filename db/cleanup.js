/* global use, db */
// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.

// The current database to use.
use('plc_database');

use('luca_dot_vignati_at_vignati_dot_net');
use('stefano_dot_dallona_at_gmail_dot_com');

db["OriginalTrackNode"].deleteMany({})
db["LostSamplesMaskNode"].deleteMany({})
db["ReconstructedTrackNode"].deleteMany({})
db["OutputAnalysisNode"].deleteMany({})
db["runs"].deleteMany({})
db["Run"].deleteMany({})
db["Events"].deleteMany({})

use('global');
db["users"].deleteMany({})