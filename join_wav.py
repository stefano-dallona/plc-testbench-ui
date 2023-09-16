import wave
import sys
import os
import io


def print_usage(command_name):
    print("Usage: python %s <path-to-wav-file> <start-time> <end-time> [output-filename]" % (command_name))

if len(sys.argv) < 3:
    print_usage(os.path.basename(sys.argv[0]))
    sys.exit(1)

infiles = sys.argv[1:]
outfile = "joined.wav"

data= []
for infile in infiles:
    w = wave.open(infile, 'rb')
    data.append( [w.getparams(), w.readframes(w.getnframes())] )
    w.close()
    
output = wave.open(outfile, 'wb')
output.setparams(data[0][0])
for i in range(len(data)):
    output.writeframes(data[i][1])
output.close()