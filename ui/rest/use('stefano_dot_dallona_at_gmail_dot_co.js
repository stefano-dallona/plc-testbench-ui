use('stefano_dot_dallona_at_gmail_dot_com');

db["OriginalTrackNode"].deleteMany({})
db["LostSamplesMaskNode"].deleteMany({})
db["ReconstructedTrackNode"].deleteMany({})
db["OutputAnalysisNode"].deleteMany({})
//db["runs"].deleteMany({})
db["Run"].deleteMany({})
db["Events"].deleteMany({})