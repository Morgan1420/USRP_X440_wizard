import uhd
import sys
import time
import numpy as np

BYTES_PER_SAMP = 4  # sc16 over the wire = 4 bytes per sample

mcrs = [1024e6, 1280e6]
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
    radio1.set_rx_frequency(radio1_frequency, 0)

    graph.connect(radio0.get_unique_id(), 0, replay0.get_unique_id(), 0)
    graph.connect(radio1.get_unique_id(), 0, replay1.get_unique_id(), 0)

    throttle = 0.2
    num_ports = 1
    cap_dtype = np.complex64

    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.args["throttle"] = str(throttle)

    # Set up streamer0
    rx_streamer0 = graph.create_rx_streamer(num_ports, stream_args)
    graph.connect(replay0.get_unique_id(), 0, rx_streamer0, 0)

    # Set up streamer1
    rx_streamer1 = graph.create_rx_streamer(num_ports, stream_args)
    graph.connect(replay1.get_unique_id(), 0, rx_streamer1, 0)

    graph.commit()

    capture_duration = 0.4
    cap_delay = 0.015
    
    ######## Data Capture Execution ########
    time_now = graph.get_mb_controller().get_timekeeper(0).get_time_now()
    
    # --- 1. RECORD CONFIGURATION & ARMING ---
    num_samps0 = int(mcrs[0] * capture_duration)
    num_bytes0 = num_samps0 * BYTES_PER_SAMP
    mem_size0 = replay0.get_mem_size()
    mem_stride0 = mem_size0 // num_ports
    
    for idx in range(num_ports):
        replay0.record(idx * mem_stride0, num_bytes0, idx)
        
    stream_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd0.num_samps = num_samps0
    stream_cmd0.stream_now = False
    stream_cmd0.time_spec = time_now + uhd.types.TimeSpec(cap_delay)
    radio0.issue_stream_cmd(stream_cmd0, 0)
   
    num_samps1 = int(mcrs[1] * capture_duration)
    num_bytes1 = num_samps1 * BYTES_PER_SAMP
    mem_size1 = replay1.get_mem_size()
    mem_stride1 = mem_size1 // num_ports

    for idx in range(num_ports):
        replay1.record(idx * mem_stride1, num_bytes1, idx)
                                                                                                 
    stream_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd1.num_samps = num_samps1
    stream_cmd1.stream_now = False
    stream_cmd1.time_spec = time_now + uhd.types.TimeSpec(cap_delay)
    radio1.issue_stream_cmd(stream_cmd1, 0)

    # --- 2. WAIT FOR DRAM TO FILL ---
    print("Recording signals into onboard DRAM...")
    timeout0 = time.monotonic() + (num_samps0 / mcrs[0]) + cap_delay + 5
    while any(replay0.get_record_fullness(port) < num_bytes0 for port in range(num_ports)):
        time.sleep(0.05)
        if time.monotonic() > timeout0:
            raise RuntimeError("Timeout while loading replay0 buffer!")

    timeout1 = time.monotonic() + (num_samps1 / mcrs[1]) + cap_delay + 5
    while any(replay1.get_record_fullness(port) < num_bytes1 for port in range(num_ports)):
        time.sleep(0.05)
        if time.monotonic() > timeout1:
            raise RuntimeError("Timeout while loading replay1 buffer!")
          
    # --- 3. DOWNLOAD RADIO 0 DATA TO HOST ---
    print(f"Downloading {num_samps0} samples from Replay0...")
    output_buf_replay0 = np.zeros(num_samps0, dtype=cap_dtype)
    rx_md = uhd.types.RXMetadata()
    
    for idx in range(num_ports):
        replay0.config_play(idx * mem_stride0, num_bytes0, idx)
        
    play_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    play_cmd0.num_samps = num_samps0
    play_cmd0.stream_now = False
    play_cmd0.time_spec = uhd.types.TimeSpec(0.0)
    rx_streamer0.issue_stream_cmd(play_cmd0)

    max_pkt_samps0 = rx_streamer0.get_max_num_samps()
    recv_buffer0 = np.zeros((num_ports, max_pkt_samps0), dtype=cap_dtype)
    
    samps_received0 = 0
    while samps_received0 < num_samps0:
        num_rx = rx_streamer0.recv(recv_buffer0, rx_md, 5.0)
        if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
            print("Error during download Replay0: " + rx_md.strerror())
            break
        if num_rx > 0:
            output_buf_replay0[samps_received0 : samps_received0 + num_rx] = recv_buffer0[0, :num_rx]
            samps_received0 += num_rx

    # --- 4. DOWNLOAD RADIO 1 DATA TO HOST ---
    print(f"Downloading {num_samps1} samples from Replay1...")
    output_buf_replay1 = np.zeros(num_samps1, dtype=cap_dtype)
    
    for idx in range(num_ports):
        replay1.config_play(idx * mem_stride1, num_bytes1, idx)
        
    play_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    play_cmd1.num_samps = num_samps1
    play_cmd1.stream_now = False
    play_cmd1.time_spec = uhd.types.TimeSpec(0.0)
    rx_streamer1.issue_stream_cmd(play_cmd1)

    max_pkt_samps1 = rx_streamer1.get_max_num_samps()
    recv_buffer1 = np.zeros((num_ports, max_pkt_samps1), dtype=cap_dtype)        
  
    samps_received1 = 0
    while samps_received1 < num_samps1:
        num_rx = rx_streamer1.recv(recv_buffer1, rx_md, 5.0)
        if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
            print("Error during download Replay1: " + rx_md.strerror())
            break
        if num_rx > 0:
            output_buf_replay1[samps_received1 : samps_received1 + num_rx] = recv_buffer1[0, :num_rx]
            samps_received1 += num_rx

    # --- 5. STORE CAPTURES TO RAW BINARY IQ FILES ---
    print("\nWriting captures to disk...")
    output_buf_replay0.tofile("capture_radio0.iq")
    output_buf_replay1.tofile("capture_radio1.iq")
    print("Success! Saved 'capture_radio0.iq' and 'capture_radio1.iq'.")

if __name__ == "__main__":
    sys.exit(not main())