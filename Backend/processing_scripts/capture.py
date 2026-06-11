import uhd
import subprocess
import sys
import time
import json
import os
import numpy as np
import re

BYTES_PER_SAMP = 4  # sc16 over the wire = 4 bytes per sample



# Funció que llegeix un fitxer JSON i retorna el contingut en un diccionari
def getArgs(file_name="infoCaptura.json"):
  base_dir = os.path.dirname(os.path.dirname(__file__))
  json_path = os.path.join(base_dir, "assistanceJSONs", file_name)
  with open(json_path, "r", encoding="utf-8") as fh:
    return json.load(fh)

# Funció per obtenir la imatge de la FPGA actual
def getImageFPGA(ip_addr: str) -> str:

  # Creem una comanda uhd_usrp_probe per descobrir la imatge a partir del text resultant
  cmd = ["uhd_usrp_probe", "--args", f"type=x4xx,addr={ip_addr}"]
    
  # Fem un try except per si passes res amb la comanda
  try:
    
    print("[FPGA] Buscant el nom de la imatge de la FPGA...")
    # Executem el probe i capturem tota la sortida de la línia de comandes
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    text_complet = result.stdout + result.stderr
        
    # Busquem el patró "fpga=NOM" o "fpga: NOM" que imprimeix l'MPM i UHD
    match = re.search(r"fpga[:=]\s*([a-zA-Z0-9_]+)", text_complet, re.IGNORECASE)
    if match:
      print(f"[FPGA] La imatge de la FPGA actual és: {match.group(1)}")
      return match.group(1)
    print("[FPGA] No s'ha pogut trobar el nom de la imatge")
  except subprocess.CalledProcessError as e:
    print(f"[ERROR - FPGA] Error en executar uhd_usrp_probe: {e.stderr}")
    # Tornem un guió en cas de no trobar la imatge
    return "-"

  # Tornem un guió en cas de no trobar la imatge
  return "-"
    
# Funció per canviar la imatge de la FPGA
def changeImageFPGA(ip_addr: str, imatge: str):
  # Construïm la comanda en base a les 
  cmd = [
    "uhd_image_loader",
    "--args",
    f"type=x4xx,addr={ip_addr},fpga={imatge}"
  ]
  
  # Notifiquem a l'usuari
  print(f"[FPGA] Iniciant la càrrega de la imatge '{imatge}' a l'USRP ({ip_addr})...")
  print("[FPGA] Això pot trigar uns minuts i la connexió es perdrà temporalment.")
    
  # Fem un try except per si hi hagués cap problema
  try:
    # Executem la comanda
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    
    # Reiniciem la USRP
    print("[FPGA] Reiniciant USRP, cal esperar 30s...")
    time.sleep(30) # Donem marge al Linux intern de l'X440 per tornar a arrencar
    
    # Notifiquem a l'usuari
    print(f"[FPGA] Imatge pujada correctament\n[FPGA] Detalls de la càrrega:\n{result.stdout}")
     
        
  except subprocess.CalledProcessError as e:
    print(f"[ERROR - FPGA] Error en carregar la imatge '{imatge}': {e.stderr}")
    raise RuntimeError("[ERROR - FPGA] No s'ha pogut actualitzar l'FPGA de l'USRP.")


# Funció main
def main():
    
  # ------------------------- 1) Extraient i preparant variables de captura
  print("[CAPTURA] - Preparant dades per a la captura...\n")
  # Llegim el JSON
  capture_data = getArgs()
    
  # Adreça IP
  ip_addrs = []
  qsfp_connected = [False, False]
  
  for inx, connection in enumerate(capture_data["Connections"]):
    if(connection["connected"] == True and connection["validated"] == "Si"):
      ip_addrs.append(connection["ipAddr"])
      qsfp_connected[inx] = True
    
  if len(ip_addrs) == 0:
    print("Error: No s'ha trobat cap connexió validada.")
    return # error
  else:
    # Agafem la primera adreça com a principal
    ip_addr = ip_addrs[0]
    
    
  # Multi capture flag
  multi_capture_f = len(capture_data["Option"]["partial_options"]) == 2
  
  
  # Master clock rates i FCRs
  mcrs = [ capture_data["Option"]["partial_options"][0]["mcr_mhz"] * 1e6]
  fcrs = [ capture_data["Option"]["partial_options"][0]["fcr_ghz"] * 1e9]
  if multi_capture_f:
    mcrs.append(capture_data["Option"]["partial_options"][1]["mcr_mhz"] * 1e6)
    fcrs.append(capture_data["Option"]["partial_options"][1]["fcr_ghz"] * 1e9)
  else:
    # Si només hi ha una opció, dupliquem els paràmetres
    mcrs.append(mcrs[0])
    fcrs.append(fcrs[0])


  # Canals i freqüències centrals
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
  user_sample_rate = capture_data["Sample-rate"][0]["Sample-rate"] * 1e6 # en Hz, potser cal canviar el multiplicador
  
  # Print dades de captura - per fer
  print(f"Adreça IP: {ip_addr}")
  print(f"Multi-capture: {multi_capture_f}")
  print(f"Master clock rates: {mcrs} Hz")
  print(f"Frequencies of conversion: {fcrs} GHz")
  print(f"Channels: {channels}")
  print(f"Frequencies per canal: {frequencies_per_channel}")
  print(f"Sample rate: {user_sample_rate} Sps\n")
  
  
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
  elif max(mcrs) <= 512e6 and qsfp_connected[0] and qsfp_connected[1]:
    if current_fpga != "CG_400":
      changeImageFPGA(ip_addr=ip_addr, imatge="CG_400")
  elif max(mcrs) <= 512e6 and qsfp_connected[0]:
    has_DRAM = True
    if current_fpga != "X4_400":
      changeImageFPGA(ip_addr=ip_addr, imatge="X4_400")
  elif min(mcrs) >= 1000e6 and qsfp_connected[0] and qsfp_connected[1]:
    if current_fpga != "CG_1600":
      changeImageFPGA(ip_addr=ip_addr, imatge="CG_1600")
  elif min(mcrs) >= 1000e6 and qsfp_connected[0]:
    has_DRAM = True
    if current_fpga != "X4_1600":
      changeImageFPGA(ip_addr=ip_addr, imatge="X4_1600")
  else:
    raise RuntimeError("[ERROR - CAPTURA] No s'ha trobat cap imatge de FPGA compatible amb els paràmetres de captura i connexions QSFP detectades.")

  print("[CAPTURA] FPGA configurada correctament\n")
  
  return
  # ------------------------- 3) Configurant les radios dels dispositius
  # Configurem les freqüències centrals de cada canal
    
  # Creem el ...
  dev_args = f"addr={ip_addr},product=x440,master_clock_rate=({mcrs[0]};{mcrs[1]})"
  graph = uhd.rfnoc.RfnocGraph(dev_args)

  # Configurem els canals 
  radio0 = uhd.rfnoc.RadioControl(graph.get_block("0/Radio#0"))
  radio1 = uhd.rfnoc.RadioControl(graph.get_block("0/Radio#1"))

  replay0 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#0"))
  replay1 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#1"))

   
  # Configurem les freqüències de conversió de dades de cada canal
  radio0_frequency = fcrs[0]
  radio1_frequency = fcrs[1]
    
   
  # Configurem cadascun dels canals
  for idx, channel in enumerate(channels):
      if channel <= 4 :
          radio0.set_rx_frequency(frequencies[idx], channel)
      else:
          radio1.set_rx_frequency(frequencies[idx], channel-4)
   
  graph.connect(radio0.get_unique_id(), 0, replay0.get_unique_id(), 0)
  graph.connect(radio1.get_unique_id(), 0, replay1.get_unique_id(), 0)

  # Configurem els streamers per descarregar les captures a host després de la captura
  throttle = 0.2
  num_ports = 1
  cap_dtype = np.complex64

  stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
  stream_args.args["throttle"] = str(throttle)
  
  return
    
  '''
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
    '''
    
if __name__ == "__main__":
    sys.exit(not main())