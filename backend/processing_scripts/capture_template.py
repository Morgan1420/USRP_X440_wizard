import uhd
import numpy as np
import matplotlib.pyplot as plt
import time

# 1. Connexió
usrp = uhd.usrp.MultiUSRP("addr=192.168.10.2")


# 2. Configuració de la captura
num_samps = 10000 # number of samples received
center_freq = 500e6 # Hz
sample_rate = 1e6 # Hz
gain = 0 # dB

# 2.2 Pujem la configuració a la USRP 
usrp.set_master_clock_rate(250e6, 0) # Canal 0
usrp.set_rx_rate(sample_rate, 0)
usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), 0)
usrp.set_rx_gain(gain, 0)


st_args = uhd.usrp.StreamArgs("fc32", "sc16")
st_args.channels = [0]
metadata = uhd.types.RXMetadata()
streamer = usrp.get_rx_stream(st_args)
recv_buffer = np.zeros((1, 1000), dtype=np.complex64)


stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
stream_cmd.stream_now = True
streamer.issue_stream_cmd(stream_cmd)

# Receive Samples
samples = np.zeros(num_samps, dtype=np.complex64)
for i in range(num_samps//1000):
    streamer.recv(recv_buffer, metadata)
    samples[i*1000:(i+1)*1000] = recv_buffer[0]

# Stop Stream
stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
streamer.issue_stream_cmd(stream_cmd)

print(len(samples))
print(samples[0:10])

# --- TIME DOMAIN ---
t = np.arange(len(samples)) / sample_rate

plt.figure()
plt.plot(t, samples.real, label="I")
plt.plot(t, samples.imag, label="Q")
plt.title("Signal (Time Domain)")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.legend()
plt.grid()

# --- MAGNITUDE ---
plt.figure()
plt.plot(t, np.abs(samples))
plt.title("Magnitude")
plt.xlabel("Time (s)")
plt.ylabel("|IQ|")
plt.grid()

# --- FREQUENCY DOMAIN (FFT) ---
fft_data = np.fft.fftshift(np.fft.fft(samples))
freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), d=1/sample_rate))

plt.figure()
plt.plot(freqs/1e6, 20*np.log10(np.abs(fft_data)))
plt.title("Spectrum")
plt.xlabel("Frequency (MHz)")
plt.ylabel("Power (dB)")
plt.grid()

plt.show()

