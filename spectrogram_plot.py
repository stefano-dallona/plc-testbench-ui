#import the pyplot and wavfile modules 
import matplotlib.pyplot as plot
from scipy.io import wavfile
import os
 
# Read the wav file (mono)
filepath = 'C://Data//personale//Università//2022-2023//original_tracks//Musica_e.wav'
filedir = os.path.dirname(filepath)
filename = os.path.basename(filepath)
spectrogram_name = filename.replace(".wav", "-spectrogram.jpg")
samplingFrequency, signalData = wavfile.read(filepath)
channel = 0
channelData = [ sample[channel] for sample in signalData ]
 
# Plot the signal read from wav file
plot.subplot(211)
plot.title('Spectrogram of a wav file with piano music')
 
plot.plot(signalData)
plot.xlabel('Sample')
plot.ylabel('Amplitude')
 
plot.subplot(212)
plot.figure(figsize=(1500, 800))
plot.specgram(channelData,Fs=samplingFrequency)
plot.xlabel('Time')
plot.ylabel('Frequency')
 
plot.savefig(os.path.join(filedir, spectrogram_name), format="jpg")
plot.show()