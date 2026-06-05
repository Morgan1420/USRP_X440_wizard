import uhd
import sys
import argparse
import time
import numpy as np

BYTES_PER_SAMP = 4

mcrs = [400e6, 200e6]
fcrs = [0.9e9, 2e9]

def main():
  dev_args = f"addr=192.168.10.2,product=x440,master_clock_rate=({mcrs[0]};{mcrs[1]})"

  graph = uhd.rfnoc.RfnocGraph(dev_args)

  radio0 = uhd.rfnoc.RadioControl(graph.get_block("0/Radio#0"))
  radio1 = uhd.rfnoc.RadioControl(graph.get_block("0/Radio#1"))

  replay0 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#0"))
  replay1 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#1"))

  radio0_frequency = fcrs[0]
  radio1_frequency = fcrs[1]

  radio0.set_rx_frequency(radio0_frequency, 0)
  #radio0.set_rate(400e6)
  radio1.set_rx_frequency(radio1_frequency, 0)
  #radio1.set_rate(200e6)

  graph.connect(radio0.get_unique_id(), 0, replay0.get_unique_id(), 0)
  graph.connect(radio1.get_unique_id(), 0, replay1.get_unique_id(), 0)

  throttle = 0.2
  num_bytes0 = 10
  num_bytes1 = 10
  num_samps0 = 10
  num_samps1 = 10
  num_ports = 1

  cap_dtype = np.complex64

  stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
  stream_args.args["throttle"] = str(throttle)
  print("a")

  # Set up streamer0
  rx_streamer0 = graph.create_rx_streamer(num_ports, stream_args)
  graph.connect(replay0.get_unique_id(), 0, rx_streamer0, 0)
  print("b")

  #Set up streamer1
  rx_streamer1 = graph.create_rx_streamer(num_ports, stream_args)
  graph.connect(replay1.get_unique_id(), 0, rx_streamer1, 0)

  graph.commit()

  capture_duration = 0.4
  cap_delay = 0.015
  update_interval = 0.2


  ######## Data Capture and Display ########
  try:
    while True:
      time_now = graph.get_mb_controller().get_timekeeper(0).get_time_now()
      # Record from radio0 into DRAM using replay0
      num_samps0 = int(mcrs[0] * capture_duration)
      num_bytes0 = num_samps0 * BYTES_PER_SAMP
      mem_size = replay0.get_mem_size()
      mem_stride = mem_size // num_ports

      ## Arm replay0 block for recording
      for idx in range(num_ports):
        replay0.record(idx * mem_stride, num_bytes0, idx)
      ## Send stream command to radio0
      stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd.num_samps = num_samps0
      stream_cmd.stream_now = False
      stream_cmd.time_spec = time_now + uhd.types.TimeSpec(cap_delay)
      radio0.issue_stream_cmd(stream_cmd, 0)

      # Record from radio1 into DRAM using replay1
      num_samps1 = int(mcrs[1] * capture_duration)
      num_bytes1 = num_samps1 * BYTES_PER_SAMP
      mem_size = replay1.get_mem_size()
      mem_stride = mem_size // num_ports

      ## Arm replay1 block for recording
      for idx in range(num_ports):
        replay1.record(idx * mem_stride, num_bytes1, idx)
      ## Send stream command to radio1
      stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd.num_samps = num_samps1
      stream_cmd.stream_now = False
      stream_cmd.time_spec = time_now + uhd.types.TimeSpec(cap_delay)
      radio1.issue_stream_cmd(stream_cmd, 0)

      # Wait for record buffers to fill up
      timeout = time.monotonic() + num_samps0 / mcrs[0] + cap_delay + 10
      while any(
        (replay0.get_record_fullness(port) < num_bytes0 for port in range(num_ports))
      ):
        time.sleep(0.100)
        if time.monotonic() > timeout:
          raise RuntimeError("Timeout while loading replay0 buffer!")

      ## Wait for record buffers to fill up
      timeout = time.monotonic() + num_samps1 / mcrs[1] + cap_delay + 10
      while any(
        (replay1.get_record_fullness(port) < num_bytes1 for port in range(num_ports))
      ):
        time.sleep(0.100)
        if time.monotonic() > timeout:
          raise RuntimeError("Timeout while loading replay1 buffer!")

      # Read data from replay0 and replay1 into host buffers
      
      
      output_buf_replay0 = np.zeros(num_samps0, dtype=cap_dtype)

      rx_md = uhd.types.RXMetadata()
      num_bytes = num_samps0 * BYTES_PER_SAMP
      # pkt_size_bytes = replay0.get_max_packet_size(0)
      # max_samps_per_pkt = pkt_size_bytes // BYTES_PER_SAMP
      mem_stride = replay0.get_mem_size() // num_ports
      # Configure playback regions
      for idx in range(num_ports):
        replay0.config_play(idx * mem_stride, num_bytes, idx)
      stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd.num_samps = num_samps0
      # This is not strictly necessary, but the streamer will not allow a
      # multi-chan operation without a time spec.
      stream_cmd.stream_now = False
      stream_cmd.time_spec = uhd.types.TimeSpec(0.0)
      rx_streamer0.issue_stream_cmd(stream_cmd)

      num_rx = rx_streamer0.recv(output_buf_replay0, rx_md, 5.0)
      if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
        print("Error during download: " + rx_md.strerror())
      if num_rx != num_samps0:
        print("ERROR: Fewer samples received than expected!")

      # Get the new data
      len_buf_replay0 = len(output_buf_replay0)
      window = np.hamming(len_buf_replay0)
      fft = np.fft.fft(output_buf_replay0 * window)
      window_power = sum(window * window) / len_buf_replay0
      logfft = (
        20 * np.log10(np.abs(np.fft.fftshift(fft)))
        - 10 * np.log10(window_power)
        - 20 * np.log10(len_buf_replay0)
        + 3
      )
      xdata_replay0 = np.arange(
        -len_buf_replay0 / 2, len_buf_replay0 / 2, 1
      ) / len_buf_replay0 * mcrs[0] + radio0.get_rx_frequency(0)
      ydata_replay0 = logfft
      
      
      output_buf_replay1 = np.zeros(num_samps1, dtype=cap_dtype)

      # print("Downloading data to host from Replay1...")
      rx_md = uhd.types.RXMetadata()
      num_bytes = num_samps1 * BYTES_PER_SAMP
      # pkt_size_bytes = replay1.get_max_packet_size(0)
      # max_samps_per_pkt = pkt_size_bytes // BYTES_PER_SAMP
      mem_stride = replay1.get_mem_size() // num_ports
      # Configure playback regions
      for idx in range(num_ports):
        replay1.config_play(idx * mem_stride, num_bytes, idx)
      stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd.num_samps = num_samps1
      # This is not strictly necessary, but the streamer will not allow a
      # multi-chan operation without a time spec.
      stream_cmd.stream_now = False
      stream_cmd.time_spec = uhd.types.TimeSpec(0.0)
      rx_streamer1.issue_stream_cmd(stream_cmd)

      num_rx = rx_streamer1.recv(output_buf_replay1, rx_md, 5.0)
      if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
        print("Error during download: " + rx_md.strerror())
      if num_rx != num_samps1:
        print("ERROR: Fewer samples received than expected!")

      # Get the new data
      len_buf_replay1 = len(output_buf_replay1)
      window = np.hamming(len_buf_replay1)
      fft = np.fft.fft(output_buf_replay1 * window)
      window_power = sum(window * window) / len_buf_replay1
      logfft = (
        20 * np.log10(np.abs(np.fft.fftshift(fft)))
        - 10 * np.log10(window_power)
        - 20 * np.log10(len_buf_replay1)
        + 3
      )
      xdata_replay1 = np.arange(
        -len_buf_replay1 / 2, len_buf_replay1 / 2, 1
      ) / len_buf_replay1 * mcrs[1] + radio1.get_rx_frequency(0)
      ydata_replay1 = logfft
      
      time.sleep(update_interval)
      
  except:
    print ("An error occurred during capture.")
    return None
      
if __name__ == "__main__":
  sys.exit(not main())