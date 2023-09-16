import wave
import sys
import os
import io


def print_usage(command_name):
    print("Usage: python %s <path-to-wav-file> <start-time> <end-time> [output-filename]" % (command_name))

if len(sys.argv) < 4:
    print_usage(os.path.basename(sys.argv[0]))
    sys.exit(1)

input_file = sys.argv[1]
start_time = float(sys.argv[2])
end_time = float(sys.argv[3])
output_file = sys.argv[4] if len(sys.argv) >= 5 else input_file.replace(".wav", "-cut.wav")

# file to extract the snippet from
with wave.open(input_file, "rb") as infile:
    # get file data
    nchannels = infile.getnchannels()
    sampwidth = infile.getsampwidth()
    frames = infile.getnframes()
    framerate = infile.getframerate()
    duration = frames / float(framerate)
    # times between which to extract the wave from
    start = start_time if start_time >= 0 else 0 # seconds
    end = end_time if end_time <= duration else duration # seconds

    # set position in wave to start of segment
    infile.setpos(int(start * framerate))
    # extract data
    data = infile.readframes(int((end - start) * framerate))

# write the extracted data to a new file
output_file = io.BytesIO()
with wave.open(output_file, 'w') as outfile:
    outfile.setnchannels(nchannels)
    outfile.setsampwidth(sampwidth)
    outfile.setframerate(framerate)
    outfile.setnframes(int(len(data) / sampwidth))
    outfile.writeframes(data)