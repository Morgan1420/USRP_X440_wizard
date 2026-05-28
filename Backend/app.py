from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, traceback

# source /home/jmoran/Documents/_Docs_/UNI/TFG-GEI/USRP_X440_wizard/Backend/.venv/bin/activate

from processing_scripts import generate_options as gen

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
        with open(p, 'r') as f:
            return json.load(f)
    except Exception:
        return None

# Funció per escriure a JSONs
def write_json(p, data):
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)
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


if __name__ == '__main__':
    # Execute el backend amb Flask al localhost al port 5000
    app.run(host='127.0.0.1', port=5000)

