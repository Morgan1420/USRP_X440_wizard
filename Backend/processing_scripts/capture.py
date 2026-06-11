import uhd
import subprocess
import sys
import time
import json
import os
import numpy as np
import re
import threading

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
  

  # ------------------------- 3) Configurant les radios dels dispositius
  print("[CAPTURA] - Configurarnt els blocs RFNOC\n")
  

  # Creem el ...
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
  # Demanem a l'USRP que utilitzi buffers de transport interns més grans
  stream_args.args["num_recv_frames"] = "512"
  stream_args.args["recv_frame_size"] = "8000" # Ideal si tens Jumbo Frames activats
  cap_dtype = np.complex64
  
  if has_DRAM:
    # --- RUTA 1: RUTA AMB DRAM (Imatges X4_) ---
    print("[CAPTURA] Configurant la ruta passant per la memòria DRAM (Replay Block)")
      
    replay0 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#0"))
    replay1 = uhd.rfnoc.ReplayBlockControl(graph.get_block("0/Replay#1"))
      
    # Connectem la Radio al Replay
    for ch in ch_radio0:
      graph.connect(radio0.get_unique_id(), ch - 1, replay0.get_unique_id(), ch - 1)
    for ch in ch_radio1:
      graph.connect(radio1.get_unique_id(), ch - 5, replay1.get_unique_id(), ch - 5)
          
    # Connectem el Replay al Host (nosaltres)
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
      graph.connect(radio0.get_unique_id(), ch - 1, rx_streamer0, i)

    rx_streamer1 = graph.create_rx_streamer(len(ch_radio1), stream_args) if ch_radio1 else None
    for i, ch in enumerate(ch_radio1):
      graph.connect(radio1.get_unique_id(), ch - 5, rx_streamer1, i)
  
  graph.commit()
  print("[CAPTURA] Graf validat i bloquejat.")
  
  # ------------------------- 4) Execució i Descàrrega
  print("\n[CAPTURA] - INICIANT EXECUCIÓ I DESCÀRREGA")
  
  import threading

  temps_captura_json = capture_data["Sample-rate"][0].get("Temps de captura", 0)
  capture_duration = float(temps_captura_json) if temps_captura_json > 0 else 0.1 
  
  cap_delay = 0.05
  BYTES_PER_SAMP = 4
  CHUNK_SAMPS = 2_000_000  # ~8MB per canal, ideal per no col·lapsar el Host
  
  num_samps0 = int(mcrs[0] * capture_duration)
  num_samps1 = int(mcrs[1] * capture_duration)
  
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
          
          # Creem el buffer a la RAM per guardar-ho tot abans del disc
          full_data0 = np.zeros((len(ch_radio0), num_samps0), dtype=cap_dtype)
          recv_buffer0 = np.zeros((len(ch_radio0), rx_streamer0.get_max_num_samps()), dtype=cap_dtype)
          samps_received0 = 0

          while samps_received0 < num_samps0:
              samps_this_chunk = min(CHUNK_SAMPS, num_samps0 - samps_received0)
              bytes_this_chunk = samps_this_chunk * BYTES_PER_SAMP
              offset_bytes = samps_received0 * BYTES_PER_SAMP

              # Apuntem el Replay a la porció exacta per a cadascun dels canals actius
              for i, ch in enumerate(ch_radio0):
                  replay0.config_play(((ch - 1) * mem_stride0) + offset_bytes, bytes_this_chunk, ch - 1)

              # Demanem només aquest chunk a l'streamer
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
                      # Copiem exclusivament la porció rebuda al lloc corresponent de la matriu global
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
  
  '''
  # ------------------------- 4) Execució i Descàrrega
  print("\n[CAPTURA] - INICIANT EXECUCIÓ")
  
  # Calculem les mostres necessàries (Utilitzem un temps de prova d'1 segon si no ve del JSON)
  capture_duration = 0.25 
  cap_delay = 0.05
  BYTES_PER_SAMP = 4
  
  num_samps0 = int(mcrs[0] * capture_duration)
  num_samps1 = int(mcrs[1] * capture_duration)
  
  # Temps sincronitzat
  time_now = graph.get_mb_controller().get_timekeeper(0).get_time_now()
  exec_time = time_now + uhd.types.TimeSpec(cap_delay)
  
  if has_DRAM:
    # === LÒGICA DRAM (Gravar i després llegir) ===
    mem_stride0 = replay0.get_mem_size() // 4 if ch_radio0 else 0
    mem_stride1 = replay1.get_mem_size() // 4 if ch_radio1 else 0

    # 1. Armar Replays per gravar
    for ch in ch_radio0:
      replay0.record((ch - 1) * mem_stride0, num_samps0 * BYTES_PER_SAMP, ch - 1)
    for ch in ch_radio1:
      replay1.record((ch - 5) * mem_stride1, num_samps1 * BYTES_PER_SAMP, ch - 5)

    # 2. Donar l'ordre a les ràdios
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

    print("[CAPTURA] Omplint la DRAM interna...")
    time.sleep(capture_duration + cap_delay + 0.5)

    # 3. Descarregar des de la DRAM al disc
    rx_md = uhd.types.RXMetadata()
  
    if ch_radio0:
      print(f"[CAPTURA] Descarregant dades del bloc Replay 0...")
      for i, ch in enumerate(ch_radio0):
        replay0.config_play((ch - 1) * mem_stride0, num_samps0 * BYTES_PER_SAMP, ch - 1)
          
      play_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
      play_cmd0.num_samps = num_samps0
      play_cmd0.stream_now = True
      rx_streamer0.issue_stream_cmd(play_cmd0)

      full_data0 = np.zeros((len(ch_radio0), num_samps0), dtype=cap_dtype)
      recv_buffer = np.zeros((len(ch_radio0), rx_streamer0.get_max_num_samps()), dtype=cap_dtype)
      
      samps_received = 0
          
      # Per simplificar memòria al host, guardem directament a un fitxer binari brut en chunks
      files = [open(f"capture_ch{ch}.iq", "wb") for ch in ch_radio0]
          
      while samps_received < num_samps0:
        num_rx = rx_streamer0.recv(recv_buffer, rx_md, 3.0)
        
        if rx_md.error_code == uhd.types.RXMetadataErrorCode.timeout:
          print("[AVÍS] Timeout! L'USRP no envia més dades (Possible pèrdua de paquets prèvia). Sortint del bucle.")
          break # Sortim per guardar el que tenim fins ara
             
        elif rx_md.error_code == uhd.types.RXMetadataErrorCode.overflow:
          print("[AVÍS] Overflow intern detectat (S'han perdut paquets pel camí).")
          # No fem break perquè volem continuar recollint la resta de paquets que segueixin vius
          
        elif rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
          print(f"[AVÍS] Error estrany: {rx_md.strerror()}")
        
        if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
          print(f"Error de metadades: {rx_md.strerror()}")
             
        if num_rx > 0:
          mostres_a_copiar = min(num_rx, num_samps0 - samps_received)
          full_data0[:, samps_received : samps_received + mostres_a_copiar] = recv_buffer[:, :mostres_a_copiar]
          samps_received += mostres_a_copiar
                  
      for f in files: f.close()
      
      # Descàrrega Ràdio 1
      if ch_radio1:
        print(f"[CAPTURA] Descarregant dades del bloc Replay 1 ({len(ch_radio1)} canals)...")
        for i, ch in enumerate(ch_radio1):
          replay1.config_play((ch - 5) * mem_stride1, num_samps1 * BYTES_PER_SAMP, ch - 5)
          
        play_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
        play_cmd1.num_samps = num_samps1
        play_cmd1.stream_now = True
        rx_streamer1.issue_stream_cmd(play_cmd1)

        recv_buffer1 = np.zeros((len(ch_radio1), rx_streamer1.get_max_num_samps()), dtype=cap_dtype)
        files1 = [open(f"capture_ch{ch}.iq", "wb") for ch in ch_radio1]
          
        samps_received = 0
        while samps_received < num_samps1:
          num_rx = rx_streamer1.recv(recv_buffer1, rx_md, 3.0)
          if num_rx > 0:
            for i, f in enumerate(files1):
              f.write(recv_buffer1[i, :num_rx].tobytes())
            samps_received += num_rx
        
        for f in files1: f.close()
        
  else:
    # =====================================================================
    # RUTA 2: DIRECT STREAMING (Sense DRAM, captura en temps real)
    # =====================================================================
    print("[CAPTURA] Mode Streaming Directe actiu. Preparant captura multitasca...")
      
    def rx_worker(streamer, num_samps, ch_list, radio_id):
      """Funció per executar en un fil separat per rebre dades de manera concurrent"""
      rx_md = uhd.types.RXMetadata()
      recv_buffer = np.zeros((len(ch_list), streamer.get_max_num_samps()), dtype=cap_dtype)
      files = [open(f"capture_ch{ch}_direct.iq", "wb") for ch in ch_list]
          
      samps_received = 0
      while samps_received < num_samps:
        # Timeout curt perquè s'espera el flux gairebé immediatament
        num_rx = streamer.recv(recv_buffer, rx_md, 1.0)
        if rx_md.error_code == uhd.types.RXMetadataErrorCode.timeout:
          print(f"[RÀDIO {radio_id}] Avís: Timeout durant la captura.")
          break
        if num_rx > 0:
          for i, f in enumerate(files):
            f.write(recv_buffer[i, :num_rx].tobytes())
          samps_received += num_rx
                  
      for f in files: f.close()
      print(f"[RÀDIO {radio_id}] Captura finalitzada ({samps_received} mostres).")

    # Preparem els comandaments d'inici
    stream_cmd0 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd0.stream_now = False
    stream_cmd0.time_spec = exec_time
      
    stream_cmd1 = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd1.stream_now = False
    stream_cmd1.time_spec = exec_time

    threads = []

    # Llancem el fil i les ordres de la Radio 0
    if ch_radio0:
      stream_cmd0.num_samps = num_samps0
      rx_streamer0.issue_stream_cmd(stream_cmd0)
      t0 = threading.Thread(target=rx_worker, args=(rx_streamer0, num_samps0, ch_radio0, 0))
      threads.append(t0)

    # Llancem el fil i les ordres de la Radio 1
    if ch_radio1:
      stream_cmd1.num_samps = num_samps1
      rx_streamer1.issue_stream_cmd(stream_cmd1)
      t1 = threading.Thread(target=rx_worker, args=(rx_streamer1, num_samps1, ch_radio1, 1))
      threads.append(t1)

    print("[CAPTURA] Esperant l'arribada de dades (fils en paral·lel)...")
    # Iniciem els bucles de descàrrega abans no arribi el moment 'exec_time'
    for t in threads:
      t.start()
          
    # Esperem a que els fils acabin la seva feina
    for t in threads:
      t.join()
        
  print("\n[CAPTURA] Procés completat amb èxit! Fitxers guardats al disc.")
  '''
    
if __name__ == "__main__":
    sys.exit(not main())