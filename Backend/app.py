from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, traceback

# source /home/jmoran/Documents/_Docs_/UNI/TFG-GEI/USRP_X440_wizard/Backend/.venv/bin/activate

from processing_scripts import generate_options as gen
from processing_scripts import USRP_handler as usrp_handler
from processing_scripts import capture as capture_script

app = Flask(__name__)
CORS(app)

ASSIST_DIR = os.path.join('./', 'assistanceJSONs')
FILTERS_PATH = os.path.join(ASSIST_DIR, 'filters.json')
PARTIAL_PATH = os.path.join(ASSIST_DIR, 'partialOptions.json')
COMPLETE_PATH = os.path.join(ASSIST_DIR, 'completeOptions.json')
FILTERED_PATH = os.path.join(ASSIST_DIR, 'filteredOptions.json')
MCR_TABLE_PATH = os.path.join(ASSIST_DIR, 'mcr_converter_rates_table.json')

# =========================== FUNCIONS ========================== #
# Funció per llegir JSONs
def read_json(p):
  # El try except és per si intentem llegir un JSON que encara no existeix
  try:
    with open(p, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception:
    return None

# Funció per escriure a JSONs
def write_json(p, data):
  with open(p, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  return True



# ============================ APP ROUTES ======================= #  
# Ruta per obtenir els filters
@app.route('/api/load_filters', methods=['GET'])
def get_filters():
  print("GET /api/load_filters")
  data = read_json(FILTERS_PATH) or {}
  return jsonify(data)

# Ruta per actualitzar els filters
@app.route('/api/store_filters', methods=['POST'])
def post_filters():
  print("POST /api/store_filters")
  try:
    obj = request.get_json() or {}
    # Ensure keys present
    out = {
      'min_channels': obj.get('min_channels'),
      'max_channels': obj.get('max_channels'),
      'sorting': obj.get('sorting', '')
    }
    ok = write_json(FILTERS_PATH, out)
    if not ok:
      return jsonify({'ok': False, 'message': 'Could not write filters file'}), 500
    return jsonify({'ok': True})
  except Exception as e:
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500

# Ruta per generar les opcions
@app.route('/api/generate', methods=['POST'])
def generate():
  try:
    payload = request.get_json() or {}
    f_c = payload.get('f_c')
    bw = payload.get('bw')
        

    # Validate and process inputs using existing Python logic
    ok, userInputs = gen.processInputs(f_c=f_c, bw=bw)
    if not ok:
      return jsonify({'ok': False, 'message': userInputs}), 400

    # Generate partial options -> writes partialOptions.json
    p_ok = gen.generatePartialOptions(userInputs['f_min'], userInputs['f_max'], MCR_TABLE_PATH, PARTIAL_PATH)
    if not p_ok:
      return jsonify({'ok': False, 'message': 'Failed generating partial options'}), 500

    # Generate complete options -> writes completeOptions.json
    c_ok = gen.generateCompleteOptions(userInputs['f_min'], userInputs['f_max'], PARTIAL_PATH)
    if not c_ok:
      return jsonify({'ok': False, 'message': 'Failed generating complete options'}), 500

    # Apply filters and sorting (reads filters.json)
    f_ok = gen.filter_and_sort(COMPLETE_PATH, FILTERS_PATH)
    if not f_ok:
      return jsonify({'ok': False, 'message': 'Failed filtering options'}), 500

    items = read_json(FILTERED_PATH) or []
    return jsonify({'ok': True, 'count': len(items), 'items': items})
  except Exception as e:
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500


# Ruta per obtenir les opcions filtrades
@app.route('/api/options', methods=['GET'])
def get_options():
  data = read_json(FILTERED_PATH) or []
  return jsonify(data)


# Ruta per validar connexions USRP des del frontend
@app.route('/api/validate_connections', methods=['POST'])
def validate_connections():
  try:
    payload = request.get_json() or {}
    rows = payload.get('rows') or []

    results = []
    for r in rows:
      name = r.get('name')
      connected = bool(r.get('connected'))
      ipAddr = r.get('ipAddr') or None

      if not connected:
        status = '-'
      else:
        # Delegate validation to USRP handler which returns per-ip info
        res = usrp_handler.validateConnectionToTheUSRP(ipAddr)

        def _map_human(v):
          if v is True:
            return 'Si'
          if v is False:
            return 'No'
          return '-'

        status = _map_human(res.get('ipAddr'))

      results.append({
        'name': name,
        'ipAddr': ipAddr,
        'status': status
      })

    print("Validation results:", results)
    return jsonify({'ok': True, 'results': results})
  except Exception as e:
    print("Error validating connections:")
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500
    


# Ruta per desar una captura (infoCaptura.json)
@app.route('/api/save_capture', methods=['POST'])
def save_capture():
  try:
    payload = request.get_json() or {}
    if not payload:
      return jsonify({'ok': False, 'message': 'Empty payload'}), 400
    out_path = os.path.join(ASSIST_DIR, 'infoCaptura.json')
    ok = write_json(out_path, payload)
    if not ok:
      return jsonify({'ok': False, 'message': 'Failed writing file'}), 500
    print(f"Saved capture to {out_path}")

    # Trigger capture in background so the HTTP request doesn't block.
    try:
      import threading
      t = threading.Thread(target=capture_script.main, daemon=True)
      t.start()
      capture_started = True
    except Exception as e:
      print('Error starting capture:')
      traceback.print_exc()
      capture_started = False

    return jsonify({'ok': True, 'path': out_path, 'capture_started': capture_started})
  except Exception as e:
    print('Error saving capture:')
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500


if __name__ == '__main__':
  # Execute el backend amb Flask al localhost al port 5000
  app.run(host='127.0.0.1', port=5000)

