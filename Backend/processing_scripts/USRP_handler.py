import uhd
import subprocess
import re
import time

# Funció per validar la connexió IP amb l'USRP
def validateConnectionToTheUSRP(ip_address=None):
  # Variable de retorn
    isValid = None

  # Si no hi ha IP, no és ni vàlida ni invàlida
    if ip_address is None:
        print("  [USRP HANDLER] - No IP address provided.")
        return isValid

  # Validem el format de l'adreça IP: "x.x.x.x", on x és entre 0 i 255
    octets = ip_address.split('.')
    if len(octets) != 4 or not all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
        print("  [USRP HANDLER] - IP address invalid: {}".format(ip_address))
        isValid = False
        return isValid

  # Intentem connectar amb l'USRP fent servir la llibreria UHD. Si funciona és vàlida, si llença una excepció no ho és :)
    try:
        device_args = "mgmt_addr={}".format(ip_address)
        uhd.usrp.MultiUSRP(device_args)
        isValid = True
    except Exception:
        isValid = False

    return isValid

  # Funció per obtenir la imatge actual de la FPGA
def getImageFPGA(ip_addr: str) -> str:

  # Creem una comanda uhd_usrp_probe per descobrir la imatge a partir del text resultant
  cmd = ["uhd_usrp_probe", "--args", f"type=x4xx,addr={ip_addr}"]
    
  # Fem un try except per si passes res amb la comanda
  try:
    
    print("    [FPGA] Buscant el nom de la imatge de la FPGA...")
    # Executem el probe i capturem tota la sortida de la línia d'ordres
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    text_complet = result.stdout + result.stderr
        
    # Busquem el patró "fpga=NOM" o "fpga: NOM" que imprimeix l'MPM i UHD
    match = re.search(r"fpga[:=]\s*([a-zA-Z0-9_]+)", text_complet, re.IGNORECASE)
    if match:
      print(f"    [FPGA] La imatge de la FPGA actual és: {match.group(1)}")
      return match.group(1)
    print("    [FPGA] No s'ha pogut trobar el nom de la imatge")
  except subprocess.CalledProcessError as e:
    print(f"    [ERROR - FPGA] Error en executar uhd_usrp_probe: {e.stderr}")
    # Tornem un guionet en cas de no trobar la imatge
    return "-"

  # Tornem un guionet en cas de no trobar la imatge
  return "-"
    
# Funció per canviar la imatge de la FPGA
def changeImageFPGA(ip_addr: str, imatge: str):
  # Construïm la comanda en base als paràmetres
  cmd = [
    "uhd_image_loader",
    "--args",
    f"type=x4xx,addr={ip_addr},fpga={imatge}"
  ]
  
  # Notifiquem l'usuari
  print(f"    [FPGA] Iniciant la càrrega de la imatge '{imatge}' a l'USRP ({ip_addr})...")
  print("    [FPGA] Això pot trigar uns minuts i la connexió es perdrà temporalment.")
    
  # Fem un try/except per si hi hagués cap problema
  try:
    # Executem la comanda
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    
    # Reiniciem l'USRP
    print("    [FPGA] Reiniciant USRP, cal esperar 30s...")
    time.sleep(30) # Donem marge al Linux intern de l'X440 per tornar a arrencar
    
    # Notifiquem l'usuari
    print(f"    [FPGA] Imatge pujada correctament\n[FPGA] Detalls de la càrrega:\n{result.stdout}")
     
        
  except subprocess.CalledProcessError as e:
    print(f"    [ERROR - FPGA] Error en carregar la imatge '{imatge}': {e.stderr}")
    raise RuntimeError("    [ERROR - FPGA] No s'ha pogut actualitzar l'FPGA de l'USRP.")

