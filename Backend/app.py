from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, traceback
import threading

# Importem els scripts de processament que necessitem
from processing_scripts import generate_options as gen
from processing_scripts import USRP_handler as usrp_handler
from processing_scripts import capture_2 as capture_script

# Creem la app de Flask
app = Flask(__name__)
CORS(app)

# Definim els "paths" per als diferents fitxers/directoris que utilitzarem
ASSIST_DIR = os.path.join('./', 'assistanceJSONs')
FILTERS_PATH = os.path.join(ASSIST_DIR, 'filters.json')
PARTIAL_PATH = os.path.join(ASSIST_DIR, 'partialOptions.json')
COMPLETE_PATH = os.path.join(ASSIST_DIR, 'completeOptions.json')
FILTERED_PATH = os.path.join(ASSIST_DIR, 'filteredOptions.json')
MCR_TABLE_PATH = os.path.join(ASSIST_DIR, 'mcr_converter_rates_table.json')
CAPTURE_INFO_PATH = os.path.join(ASSIST_DIR, 'infoCaptura.json')
CAPTURE_DIR = os.path.join('./', 'captureFiles')

# ============================ FUNCIONS ============================ #
# Funció per llegir un JSON
def read_json(p):
  try:
    with open(p, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception:
    return None

# Funció per escriure a un fitxer JSON
def write_json(p, data):
  with open(p, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  return True



# ============================ APP ROUTES ============================ #  

# +-+-+-+-+-+-+-+-+ FILTRES i OPCIONS +-+-+-+-+-+-+-+-+ #
 
# Ruta per carregar els filtres
@app.route('/api/load_filters', methods=['GET'])
def get_filters():
  print("[API] (GET /api/load_filters) - Loading filters...")
  data = read_json(FILTERS_PATH) or {}
  return jsonify(data)

# Ruta per guardar els filtres
@app.route('/api/store_filters', methods=['POST'])
def post_filters():
  # Notifiquem a l'usuari per la terminal
  print("[API] (POST /api/store_filters) - Storing filters...")
  
  try:
    # Recuperem les dades del JSON
    obj = request.get_json() or {}
    
    # Creem un diccionari amb les dades que volem guardar
    out = {
      'min_channels': obj.get('min_channels'),
      'max_channels': obj.get('max_channels'),
      'sorting': obj.get('sorting', '')
    }
    
    # Escrivim el fitxer amb les dades
    ok = write_json(FILTERS_PATH, out)
    if not ok:
      return jsonify({'ok': False, 'message': 'Could not write filters file'}), 500
    return jsonify({'ok': True})
  
  
  except Exception as e:
    # Error d'excepició
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500

# Ruta per generar les opcions
@app.route('/api/generate', methods=['POST'])
def generate():
  # Notifiquem a l'usuari per la terminal
  print("[API] (POST /api/generate) - Generating capture options...")
  
  try:
    # Recuperem les dades del JSON
    payload = request.get_json() or {}
    
    # Recuperem els valors de f_c i bw del payload
    f_c = payload.get('f_c')
    bw = payload.get('bw')
        
    # Processem els inputs i els validem
    ok, userInputs = gen.processInputs(f_c=f_c, bw=bw)
    if not ok:
      return jsonify({'ok': False, 'message': userInputs}), 400

    # Procès per passos sobre com generar les opcions de captura basades en els inputs de l'usuari
    # PAS 1: Generem les totes les opcions parcials
    p_ok = gen.generatePartialOptions(userInputs['f_min'], userInputs['f_max'], MCR_TABLE_PATH, PARTIAL_PATH)
    if not p_ok:
      return jsonify({'ok': False, 'message': 'Failed generating partial options'}), 500

    # PAS 2: En base a les opcions parcials anteriors generem totes les combinacions d'opcions parcials que completen la banda completa
    c_ok = gen.generateCompleteOptions(userInputs['f_min'], userInputs['f_max'], PARTIAL_PATH)
    if not c_ok:
      return jsonify({'ok': False, 'message': 'Failed generating complete options'}), 500

    # PAS 3: Filtrem i ordenem les opcions
    f_ok = gen.filter_and_sort(COMPLETE_PATH, FILTERS_PATH)
    if not f_ok:
      return jsonify({'ok': False, 'message': 'Failed filtering options'}), 500

    # Finalment retornem les dades filtrades al frontend
    items = read_json(FILTERED_PATH) or []
    return jsonify({'ok': True, 'count': len(items), 'items': items})
  
  except Exception as e:
    # Excepció
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500


# Ruta per carregar les opcions filtrades
@app.route('/api/options', methods=['GET'])
def get_options():
  print("[API] (GET /api/options) - Loading options...")
  # Retornar les dades del fitxer JSON amb les opcions filtrades
  data = read_json(FILTERED_PATH) or []
  return jsonify(data)


# +-+-+-+-+-+-+-+-+ USRP I CAPTURA +-+-+-+-+-+-+-+-+ #

# Ruta per validar les connexions a l'USRP  
@app.route('/api/validate_connections', methods=['POST'])
def validate_connections(): 
  # Notifiquem a l'usuari per la terminal
  print("[API] (POST /api/validate_connections) - Validating connections to the USRP...")
  
  try:
    # Recuperem les dades del JSON
    payload = request.get_json() or {}
    
    # Recuperem les files de connexions donades per l'usuari
    rows = payload.get('rows') or []

    # Per cada fila (i.e. adreça):
    results = []
    for idx, r in enumerate(rows):
      # Recuperem les dades de la fila
      name = r.get('name')
      connected = bool(r.get('connected'))
      ipAddr = r.get('ipAddr') or None

      # Si l?usuari ens diu que no està connnectada ni ho mirem
      if not connected:
        print(f"[API] - Row {idx} ({name}): Not connected, skipping validation.")
        status = '-'
      else:
        # En cas que l'usuari es cregui que està connectada executem l'escript de validació
        v = usrp_handler.validateConnectionToTheUSRP(ipAddr)
        
        # Guardem el resultat de la validació i mostrem un missatge a la terminal
        if v is True:
          print(f"[API] - Row {idx} ({name}): Connection to {ipAddr} is valid.")
          status = 'Yes'
        elif v is False:
          print(f"[API] - Row {idx} ({name}): Connection to {ipAddr} is NOT valid.")
          status = 'No'
        else:
          status = '-'
      
      # Guardem les dades en el format correcte per retornar-les al frontend
      results.append({
        'name': name,
        'ipAddr': ipAddr,
        'status': status
      })

    # Retornem les dades al frontend
    return jsonify({'ok': True, 'results': results})
  
  except Exception as e:
    # Error d'excepció
    print("[API] Error validating connections:")
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500
    


# Ruta que inicialitza una captura 
@app.route('/api/start_capture', methods=['POST'])
def start_capture():
  # Notifiquem a l'usuari per la terminal
  print("[API] (POST /api/start_capture) - Starting capture...")
  
  try:
    # Recuperem les dades del JSON
    payload = request.get_json() or {}
    if not payload:
      return jsonify({'ok': False, 'message': 'Empty payload'}), 400
    
    # Guardem la informació a un fitxer JSON
    out_path = os.path.join(ASSIST_DIR, 'infoCaptura.json')
    ok = write_json(out_path, payload)
    if not ok:
      return jsonify({'ok': False, 'message': 'Failed writing file'}), 500
    
    # Notifiquem a l'usuari per la terminal que hem guardat la informació
    print(f"[API] Saved capture information to {out_path}")

    
    # Executem la captura (amb try/except perque caution al jugar amb els threads)
    try:
      # Creem un nou thread per no bloquejar la sol·licitud HTTP mentre s'executa l'script de captura.
      t = threading.Thread(target=capture_script.capture, daemon=True)
      t.start() # Iniciem el thread
      capture_started = True
    except Exception as e:
      print('Error starting capture:')
      traceback.print_exc()
      capture_started = False

    # Retornem la resposta al frontend amb l'estat de la captura
    return jsonify({'ok': True, 'path': out_path, 'capture_started': capture_started})
 
  except Exception as e:
    print('Error saving capture:')
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500


# ============================= APP (MAIN) ============================ #
if __name__ == '__main__':
  # Executem el backend a localhost:5000
  app.run(host='127.0.0.1', port=5000)

