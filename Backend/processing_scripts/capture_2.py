import uhd
import sys
import time
import json
import os
import numpy as np
import threading

# Import files from other files
from processing_scripts.USRP_handler import getImageFPGA, changeImageFPGA

# GLobal vars
BYTES_PER_SAMP = 4  # sc16 over the wire = 4 bytes per sample

# Function to get arguments from infoCaptura.json
def getArgs(file_name="infoCaptura.json"):
  base_dir = os.path.dirname(os.path.dirname(__file__))
  json_path = os.path.join(base_dir, "assistanceJSONs", file_name)
  with open(json_path, "r", encoding="utf-8") as fh:
    return json.load(fh)


# Capture function
def capture():
    
  # ------------------------- 1) EXTRACT AND PREPARE CAPTURE DATA
  print("  [CAPTURA] - Preparant dades per a la captura...\n")
  
  # Read the JSON
  capture_data = getArgs()
    
  # IP addresses i connexions QSFP
  ip_addrs = []
  qsfp_connected = [False, False]
  
  # Extract all the valid IP addresses and identify the QSFP prots
  for inx, connection in enumerate(capture_data["Connections"]):
    if(connection["connected"] == True and connection["validated"] == "Yes"):
      ip_addrs.append(connection["ipAddr"])
      qsfp_connected[inx] = True
  
  # Throw error if there are no valid connections (this should be checked before but just in case)
  if len(ip_addrs) == 0:
    print("Error: No s'ha trobat cap connexió validada.")
    return # error
  else:
    # Assign the firts address as the main address
    ip_addr = ip_addrs[0]
    
    
  # Create a flag to indicate if the capture uses >1 partial option (i.e. 2 partial options)
  multi_capture_f = len(capture_data["Option"]["partial_options"]) == 2
  
  
  # Extract and prepare the MCRs and FCRs
  mcrs = [ capture_data["Option"]["partial_options"][0]["mcr_mhz"] * 1e6]
  fcrs = [ capture_data["Option"]["partial_options"][0]["fcr_ghz"] * 1e9]
  if multi_capture_f:
    mcrs.append(capture_data["Option"]["partial_options"][1]["mcr_mhz"] * 1e6)
    fcrs.append(capture_data["Option"]["partial_options"][1]["fcr_ghz"] * 1e9)
  else:
    # If there is only one option we write the same MCR and FRC to both canells, later on this'll be useful
    mcrs.append(mcrs[0])
    fcrs.append(fcrs[0])


  # Extract channels and frequencies per channel 
  channels = []
  frequencies_per_channel = {} 
  
  for idx, channel in enumerate(capture_data["Ports"]["Partial-option-1"]):
    channels.append(channel[f"Channel-{idx+1}"][0])
    frequencies_per_channel[int(channel[f'Channel-{idx+1}'][0])] = float(f"{channel['f_center']}")
    
  if(multi_capture_f):
    # En cas de tindre més d'un canal capturem les dades dels dos
    for idx, channel in enumerate(capture_data["Ports"]["Partial-option-2"]):
      channels.append(channel[f"Channel-{idx+1}"][0])
      frequencies_per_channel[int(channel[f'Channel-{idx+1}'][0])] = float(f"{channel['f_center']}")
  
  # Separem quins canals van a cada ràdio física per facilitar la lògica posterior
  ch_radio0 = [ch for ch in channels if ch <= 4]  # Canals del 1 al 4 (Indexats a nivell de placa)
  ch_radio1 = [ch for ch in channels if ch > 4]   # Canals del 5 al 8
  
  
  # Sample rate
  user_sample_rate_f = capture_data["Sample-rate"][0]["Automàtic"]
  user_sample_rate = capture_data["Sample-rate"][0]["Sample-rate"] * 1e6 # en Hz
  
  # Print dades de captura 
  print(f"Adreça IP: {ip_addr}")
  print(f"Multi-capture: {multi_capture_f}")
  print(f"Master clock rates: {mcrs} Hz")
  print(f"Frequencies of conversion: {fcrs} GHz")
  print(f"Channels: {channels}")
  print(f"Frequencies per canal: {frequencies_per_channel}")
  print(f"Sample rate desitjat: {'Automàtic (Igual a MCR)' if user_sample_rate_f else f'{user_sample_rate} Sps'}\n")
  
  
  # ------------------------- 2) Configurant la FPGA
  print("[CAPTURA] - CONFIGURANT LA FPGA")
  
  # Mirem quina és la imatge de la FPGA actual
  current_fpga = getImageFPGA(ip_addr=ip_addr)
  has_DRAM = False # Amb DRAM només cal un port, sense mínim hi han d'haver 2
  
  # Triem la imatge de la FPGA més convenient
  if max(mcrs) <= 200e6 and not user_sample_rate_f and qsfp_connected[0]:
    has_DRAM = True
    if current_fpga != "X4_200":
      changeImageFPGA(ip_addr=ip_addr, imatge="X4_200")
      current_fpga = "X4_200"
  elif max(mcrs) <= 512e6 and qsfp_connected[0] and qsfp_connected[1]:
    if current_fpga != "CG_400":
      changeImageFPGA(ip_addr=ip_addr, imatge="CG_400")
      current_fpga = "CG_400"
  elif max(mcrs) <= 512e6 and qsfp_connected[0]:
    has_DRAM = True
    if current_fpga != "X4_400":
      changeImageFPGA(ip_addr=ip_addr, imatge="X4_400")
      current_fpga = "X4_400"
  elif min(mcrs) >= 1000e6 and qsfp_connected[0] and qsfp_connected[1]:
    if current_fpga != "CG_1600":
      changeImageFPGA(ip_addr=ip_addr, imatge="CG_1600")
      current_fpga = "CG_1600"
  elif min(mcrs) >= 1000e6 and qsfp_connected[0]:
    has_DRAM = True
    if current_fpga != "X4_1600":
      changeImageFPGA(ip_addr=ip_addr, imatge="X4_1600")
      current_fpga = "X4_1600"
  else:
    raise RuntimeError("[ERROR - CAPTURA] No s'ha trobat cap imatge de FPGA compatible amb els paràmetres de captura i connexions QSFP detectades.")

  print("[CAPTURA] FPGA configurada correctament\n")
  

  # ------------------------- 3) Configurant les radios dels dispositius
  print("[CAPTURA] - Configurant els blocs RFNOC\n")

  # Creem l'arbre RFNoC
  dev_args = f"addr={ip_addr},product=x440,master_clock_rate=({mcrs[0]};{mcrs[1]}),converter_rate=({fcrs[0]};{fcrs[1]})"
  graph = uhd.rfnoc.RfnocGraph(dev_args)

  # Configurem els blocs de radio 
  radio0 = uhd.rfnoc.RadioControl(graph.get_block("0/Radio#0"))
  radio1 = uhd.rfnoc.RadioControl(graph.get_block("0/Radio#1"))

  # Sintonitzem les freqüències RF segons la distribució
  for ch in ch_radio0:
      radio0.set_rx_frequency(frequencies_per_channel[ch], ch - 1)
  for ch in ch_radio1:
      radio1.set_rx_frequency(frequencies_per_channel[ch], ch - 5) 
   
  # Variables comunes d'streaming
  stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
  stream_args.args["num_recv_frames"] = "512"
  stream_args.args["recv_frame_size"] = "8000" 
  cap_dtype = np.complex64

  # Avaluem si hem d'inserir el bloc DDC a l'arbre
  use_ddc = (current_fpga == "X4_200") and (not user_sample_rate_f) and (user_sample_rate > 0)

  if use_ddc:
      print(f"[CAPTURA] MCR detectat: {mcrs[0]} Hz. Decimant per maquinari a {user_sample_rate} Sps mitjançant blocs DDC.")
  
  if has_DRAM:
    # --- RUTA 1: RUTA AMB DRAM (Imatges X4_) ---
    print("[CAPTURA] Configurant la ruta passant per la memòria DRAM (Replay Block)")
      
    replay0 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#0"))
    replay1 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#1"))
      
    # Connectem la Radio al Replay (Intercalant el DDC si escau)
    for ch in ch_radio0:
      if use_ddc:
        ddc0 = uhd.rfnoc.DdcBlockControl(graph.get_block(f"0/DDC#{ch-1}"))
        ddc0.set_output_rate(user_sample_rate, 0)
        graph.connect(radio0.get_unique_id(), ch - 1, ddc0.get_unique_id(), 0)
        graph.connect(ddc0.get_unique_id(), 0, replay0.get_unique_id(), ch - 1)
      else:
        graph.connect(radio0.get_unique_id(), ch - 1, replay0.get_unique_id(), ch - 1)
        
    for ch in ch_radio1:
      if use_ddc:
        ddc1 = uhd.rfnoc.DdcBlockControl(graph.get_block(f"0/DDC#{ch-1}")) # 0 a 7 global
        ddc1.set_output_rate(user_sample_rate, 0)
        graph.connect(radio1.get_unique_id(), ch - 5, ddc1.get_unique_id(), 0)
        graph.connect(ddc1.get_unique_id(), 0, replay1.get_unique_id(), ch - 5)
      else:
        graph.connect(radio1.get_unique_id(), ch - 5, replay1.get_unique_id(), ch - 5)
          
    # Connectem el Replay al Host
    rx_streamer0 = graph.create_rx_streamer(len(ch_radio0), stream_args) if ch_radio0 else None
    for i, ch in enumerate(ch_radio0):
      graph.connect(replay0.get_unique_id(), ch - 1, rx_streamer0, i)
      
    rx_streamer1 = graph.create_rx_streamer(len(ch_radio1), stream_args) if ch_radio1 else None
    for i, ch in enumerate(ch_radio1):
      graph.connect(replay1.get_unique_id(), ch - 5, rx_streamer1, i)
  
  else:
    # --- RUTA 2: RUTA STREAMING DIRECTE (Imatges CG_) ---
    print("[CAPTURA] Configurant la ruta d'streaming directe al host (Sense DRAM)")
      
    rx_streamer0 = graph.create_rx_streamer(len(ch_radio0), stream_args) if ch_radio0 else None
    for i, ch in enumerate(ch_radio0):
      if use_ddc:
        ddc0 = uhd.rfnoc.DdcBlockControl(graph.get_block(f"0/DDC#{ch-1}"))
        ddc0.set_output_rate(user_sample_rate, 0)
        graph.connect(radio0.get_unique_id(), ch - 1, ddc0.get_unique_id(), 0)
        graph.connect(ddc0.get_unique_id(), 0, rx_streamer0, i)
      else:
        graph.connect(radio0.get_unique_id(), ch - 1, rx_streamer0, i)

    rx_streamer1 = graph.create_rx_streamer(len(ch_radio1), stream_args) if ch_radio1 else None
    for i, ch in enumerate(ch_radio1):
      if use_ddc:
        ddc1 = uhd.rfnoc.DdcBlockControl(graph.get_block(f"0/DDC#{ch-1}"))
        ddc1.set_output_rate(user_sample_rate, 0)
        graph.connect(radio1.get_unique_id(), ch - 5, ddc1.get_unique_id(), 0)
        graph.connect(ddc1.get_unique_id(), 0, rx_streamer1, i)
      else:
        graph.connect(radio1.get_unique_id(), ch - 5, rx_streamer1, i)
  
  graph.commit()
  print("[CAPTURA] Graf validat i bloquejat.")
  
  
  # ------------------------- 4) Execució i Descàrrega
  print("\n[CAPTURA] - INICIANT EXECUCIÓ I DESCÀRREGA")

  temps_captura_json = capture_data["Sample-rate"][0].get("Temps de captura", 0)
  capture_duration = float(temps_captura_json) if temps_captura_json > 0 else 0.1 
  
  cap_delay = 0.05
  BYTES_PER_SAMP = 4
  CHUNK_SAMPS = 2_000_000  # ~8MB per canal
  
  # Calculem les mostres exactes depenent de si hem passat per DDC o no
  actual_rate0 = user_sample_rate if use_ddc else mcrs[0]
  actual_rate1 = user_sample_rate if use_ddc else mcrs[1]

  num_samps0 = int(actual_rate0 * capture_duration)
  num_samps1 = int(actual_rate1 * capture_duration)
  
  time_now = graph.get_mb_controller().get_timekeeper(0).get_time_now()
  exec_time = time_now + uhd.types.TimeSpec(cap_delay)

  if has_DRAM:
      # =====================================================================
      # RUTA 1: CAPTURA MITJANÇANT DRAM (Amb descàrrega Chunked)
      # =====================================================================
      mem_stride0 = replay0.get_mem_size() // 4 if ch_radio0 else 0
      mem_stride1 = replay1.get_mem_size() // 4 if ch_radio1 else 0

      # --- 1. Armar els Replays per gravar ---
      for ch in ch_radio0:
          replay0.record((ch - 1) * mem_stride0, num_samps0 * BYTES_PER_SAMP, ch - 1)
      for ch in ch_radio1:
          replay1.record((ch - 5) * mem_stride1, num_samps1 * BYTES_PER_SAMP, ch - 5)

      # --- 2. Programar les Ràdios perquè disparin al moment exacte ---
      stream_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd0.num_samps = num_samps0
      stream_cmd0.stream_now = False
      stream_cmd0.time_spec = exec_time
      
      stream_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd1.num_samps = num_samps1
      stream_cmd1.stream_now = False
      stream_cmd1.time_spec = exec_time

      for ch in ch_radio0: radio0.issue_stream_cmd(stream_cmd0, ch - 1)
      for ch in ch_radio1: radio1.issue_stream_cmd(stream_cmd1, ch - 5)

      print("[CAPTURA] Enregistrant senyals a la DRAM interna de l'USRP...")
      time.sleep(capture_duration + cap_delay + 0.5)

      # --- 3. Descarregar des de la DRAM al disc dur en Chunks ---
      rx_md = uhd.types.RXMetadata()
      
      # ---------------- DESCÀRREGA RÀDIO 0 ----------------
      if ch_radio0:
          print(f"[CAPTURA] Descarregant dades del bloc Replay 0 ({len(ch_radio0)} canals) en chunks...")
          
          full_data0 = np.zeros((len(ch_radio0), num_samps0), dtype=cap_dtype)
          recv_buffer0 = np.zeros((len(ch_radio0), rx_streamer0.get_max_num_samps()), dtype=cap_dtype)
          samps_received0 = 0

          while samps_received0 < num_samps0:
              samps_this_chunk = min(CHUNK_SAMPS, num_samps0 - samps_received0)
              bytes_this_chunk = samps_this_chunk * BYTES_PER_SAMP
              offset_bytes = samps_received0 * BYTES_PER_SAMP

              for i, ch in enumerate(ch_radio0):
                  replay0.config_play(((ch - 1) * mem_stride0) + offset_bytes, bytes_this_chunk, ch - 1)

              play_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
              play_cmd0.num_samps = samps_this_chunk
              play_cmd0.stream_now = True
              rx_streamer0.issue_stream_cmd(play_cmd0)

              chunk_received = 0
              while chunk_received < samps_this_chunk:
                  num_rx = rx_streamer0.recv(recv_buffer0, rx_md, 3.0)
                  
                  if rx_md.error_code == uhd.types.RXMetadataErrorCode.timeout:
                      print(f"[AVÍS R0] Timeout al chunk! {rx_md.strerror()}")
                      break
                      
                  if num_rx > 0:
                      full_data0[:, samps_received0 : samps_received0 + num_rx] = recv_buffer0[:, :num_rx]
                      samps_received0 += num_rx
                      chunk_received += num_rx

          print("[CAPTURA] Descàrrega per xarxa de Ràdio 0 completada. Guardant a disc...")
          for i, ch in enumerate(ch_radio0):
              full_data0[i, :].tofile(f"capture_ch{ch}.iq")

      # ---------------- DESCÀRREGA RÀDIO 1 ----------------
      if ch_radio1:
          print(f"[CAPTURA] Descarregant dades del bloc Replay 1 ({len(ch_radio1)} canals) en chunks...")
          
          full_data1 = np.zeros((len(ch_radio1), num_samps1), dtype=cap_dtype)
          recv_buffer1 = np.zeros((len(ch_radio1), rx_streamer1.get_max_num_samps()), dtype=cap_dtype)
          samps_received1 = 0

          while samps_received1 < num_samps1:
              samps_this_chunk = min(CHUNK_SAMPS, num_samps1 - samps_received1)
              bytes_this_chunk = samps_this_chunk * BYTES_PER_SAMP
              offset_bytes = samps_received1 * BYTES_PER_SAMP

              for i, ch in enumerate(ch_radio1):
                  replay1.config_play(((ch - 5) * mem_stride1) + offset_bytes, bytes_this_chunk, ch - 5)

              play_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
              play_cmd1.num_samps = samps_this_chunk
              play_cmd1.stream_now = True
              rx_streamer1.issue_stream_cmd(play_cmd1)

              chunk_received = 0
              while chunk_received < samps_this_chunk:
                  num_rx = rx_streamer1.recv(recv_buffer1, rx_md, 3.0)
                  
                  if rx_md.error_code == uhd.types.RXMetadataErrorCode.timeout:
                      print(f"[AVÍS R1] Timeout al chunk! {rx_md.strerror()}")
                      break
                      
                  if num_rx > 0:
                      full_data1[:, samps_received1 : samps_received1 + num_rx] = recv_buffer1[:, :num_rx]
                      samps_received1 += num_rx
                      chunk_received += num_rx

          print("[CAPTURA] Descàrrega per xarxa de Ràdio 1 completada. Guardant a disc...")
          for i, ch in enumerate(ch_radio1):
              full_data1[i, :].tofile(f"capture_ch{ch}.iq")

  else:
      # =====================================================================
      # RUTA 2: DIRECT STREAMING (Captura en temps real multitasca)
      # =====================================================================
      print("[CAPTURA] Mode Streaming Directe actiu. Preparant captura multitasca...")
      
      def rx_worker(streamer, num_samps, ch_list, radio_id):
          rx_md = uhd.types.RXMetadata()
          full_data = np.zeros((len(ch_list), num_samps), dtype=cap_dtype)
          recv_buffer = np.zeros((len(ch_list), streamer.get_max_num_samps()), dtype=cap_dtype)
          
          samps_received = 0
          while samps_received < num_samps:
              num_rx = streamer.recv(recv_buffer, rx_md, 2.0)
              if rx_md.error_code == uhd.types.RXMetadataErrorCode.timeout:
                  print(f"[RÀDIO {radio_id}] Avís: Timeout durant la captura directa.")
                  break
              if num_rx > 0:
                  mostres_a_copiar = min(num_rx, num_samps - samps_received)
                  full_data[:, samps_received : samps_received + mostres_a_copiar] = recv_buffer[:, :mostres_a_copiar]
                  samps_received += mostres_a_copiar
                  
          print(f"[RÀDIO {radio_id}] Streaming finalitzat. Guardant a disc...")
          for i, ch in enumerate(ch_list):
              full_data[i, :samps_received].tofile(f"capture_ch{ch}_direct.iq")

      stream_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd0.stream_now = False
      stream_cmd0.time_spec = exec_time
      
      stream_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      stream_cmd1.stream_now = False
      stream_cmd1.time_spec = exec_time

      threads = []

      if ch_radio0:
          stream_cmd0.num_samps = num_samps0
          rx_streamer0.issue_stream_cmd(stream_cmd0)
          t0 = threading.Thread(target=rx_worker, args=(rx_streamer0, num_samps0, ch_radio0, 0))
          threads.append(t0)

      if ch_radio1:
          stream_cmd1.num_samps = num_samps1
          rx_streamer1.issue_stream_cmd(stream_cmd1)
          t1 = threading.Thread(target=rx_worker, args=(rx_streamer1, num_samps1, ch_radio1, 1))
          threads.append(t1)

      print("[CAPTURA] Esperant l'arribada de dades en temps real...")
      for t in threads: t.start()
      for t in threads: t.join()

  print("\n[CAPTURA] Procés completat amb èxit! Fitxers guardats al disc.")

if __name__ == "__main__":
  capture()