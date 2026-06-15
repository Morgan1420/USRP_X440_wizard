from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, traceback
import threading

# Import files from repo
from processing_scripts import generate_options as gen
from processing_scripts import USRP_handler as usrp_handler
from processing_scripts import capture_2 as capture_script

# Create Flask app 
app = Flask(__name__)
CORS(app)

# Define paths for JSON and capture files
ASSIST_DIR = os.path.join('./', 'assistanceJSONs')
FILTERS_PATH = os.path.join(ASSIST_DIR, 'filters.json')
PARTIAL_PATH = os.path.join(ASSIST_DIR, 'partialOptions.json')
COMPLETE_PATH = os.path.join(ASSIST_DIR, 'completeOptions.json')
FILTERED_PATH = os.path.join(ASSIST_DIR, 'filteredOptions.json')
MCR_TABLE_PATH = os.path.join(ASSIST_DIR, 'mcr_converter_rates_table.json')
CAPTURE_INFO_PATH = os.path.join(ASSIST_DIR, 'infoCaptura.json')
CAPTURE_DIR = os.path.join('./', 'captureFiles')

# ============================ FUNCIONS ============================ #
# Function to read from a JSON file
def read_json(p):
  # The try is for any error that can happen
  try:
    with open(p, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception:
    return None

# Write data to a JSON file
def write_json(p, data):
  with open(p, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  return True



# ============================ APP ROUTES ============================ #  

# +-+-+-+-+-+-+-+-+ FILTERS AND OPTIONS +-+-+-+-+-+-+-+-+ #
 
# Route to get the current filters
@app.route('/api/load_filters', methods=['GET'])
def get_filters():
  print("[API] (GET /api/load_filters) - Loading filters...")
  data = read_json(FILTERS_PATH) or {}
  return jsonify(data)

# Route to update the filters
@app.route('/api/store_filters', methods=['POST'])
def post_filters():
  print("[API] (POST /api/store_filters) - Storing filters...")
  
  # The try is for any error that can happen
  try:
    # Get the JSON from the request
    obj = request.get_json() or {}
    
    # Create an output JSON like var to write on the JSON filters file
    out = {
      'min_channels': obj.get('min_channels'),
      'max_channels': obj.get('max_channels'),
      'sorting': obj.get('sorting', '')
    }
    
    # Write the filters to the JSON file and return error if it fails
    ok = write_json(FILTERS_PATH, out)
    if not ok:
      return jsonify({'ok': False, 'message': 'Could not write filters file'}), 500
    return jsonify({'ok': True})
  
  except Exception as e:
    # Error exception
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500

# Route to generate options
@app.route('/api/generate', methods=['POST'])
def generate():
  print("[API] (POST /api/generate) - Generating capture options...")
  
  # The try is for any error that can happen
  try:
    # Get the JSON from the request and extract f_c and bw
    payload = request.get_json() or {}
    f_c = payload.get('f_c')
    bw = payload.get('bw')
        
    # Validate and process inputs
    ok, userInputs = gen.processInputs(f_c=f_c, bw=bw)
    if not ok:
      # If inputs are not valid return error
      return jsonify({'ok': False, 'message': userInputs}), 400

    # STEP 1: Generate partial options
    p_ok = gen.generatePartialOptions(userInputs['f_min'], userInputs['f_max'], MCR_TABLE_PATH, PARTIAL_PATH)
    if not p_ok:
      return jsonify({'ok': False, 'message': 'Failed generating partial options'}), 500

    # STEP 2: Generate complete options based on partial options
    c_ok = gen.generateCompleteOptions(userInputs['f_min'], userInputs['f_max'], PARTIAL_PATH)
    if not c_ok:
      return jsonify({'ok': False, 'message': 'Failed generating complete options'}), 500

    # STEP 3: Filter and sort the complete options
    f_ok = gen.filter_and_sort(COMPLETE_PATH, FILTERS_PATH)
    if not f_ok:
      return jsonify({'ok': False, 'message': 'Failed filtering options'}), 500

    # Return the filtered options to the frontend
    items = read_json(FILTERED_PATH) or []
    return jsonify({'ok': True, 'count': len(items), 'items': items})
  
  except Exception as e:
    # Error exception
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500


# Route to get all the options in case of reloading the list
@app.route('/api/options', methods=['GET'])
def get_options():
  print("[API] (GET /api/options) - Loading options...")
  # Return the filtered options to the frontend
  data = read_json(FILTERED_PATH) or []
  return jsonify(data)


# +-+-+-+-+-+-+-+-+ USRP AND CAPTURE +-+-+-+-+-+-+-+-+ #

# Route to validate the connections to from the computer to the USRP
@app.route('/api/validate_connections', methods=['POST'])
def validate_connections():
  print("[API] (POST /api/validate_connections) - Validating connections to the USRP...")
  
  # The try is for any error that can happen
  try:
    # Get the JSON from the request and extract the rows with the USRP info
    payload = request.get_json() or {}
    rows = payload.get('rows') or []

    # Iterate though every connection given by the user
    results = []
    for idx, r in enumerate(rows):
      # Get the data from the row (in JSON format)
      name = r.get('name')
      connected = bool(r.get('connected'))
      ipAddr = r.get('ipAddr') or None

      # If it's not connected there is no need to check it
      if not connected:
        print(f"[API] - Row {idx} ({name}): Not connected, skipping validation.")
        status = '-'
      else:
        # Execute the validation script
        v = usrp_handler.validateConnectionToTheUSRP(ipAddr)
        
        # Store and print the result of the validation in a "human readable" way
        if v is True:
          print(f"[API] - Row {idx} ({name}): Connection to {ipAddr} is valid.")
          status = 'Yes'
        elif v is False:
          print(f"[API] - Row {idx} ({name}): Connection to {ipAddr} is NOT valid.")
          status = 'No'
        else:
          status = '-'
      
      # Store the result in the results list for the frontend
      results.append({
        'name': name,
        'ipAddr': ipAddr,
        'status': status
      })

    # Return the results to the frontend
    return jsonify({'ok': True, 'results': results})
  
  except Exception as e:
    # Error exception
    print("[API] Error validating connections:")
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500
    


# Route to save the capture info and trigger the capture script
@app.route('/api/start_capture', methods=['POST'])
def start_capture():
  print("[API] (POST /api/start_capture) - Starting capture...")
  
  # The try is for any error that can happen
  try:
    # Get the JSON from the request
    payload = request.get_json() or {}
    if not payload:
      # If no info was given return error
      return jsonify({'ok': False, 'message': 'Empty payload'}), 400
    
    # Save the capture info to a JSON file
    out_path = os.path.join(ASSIST_DIR, 'infoCaptura.json')
    
    ok = write_json(out_path, payload)
    if not ok:
      return jsonify({'ok': False, 'message': 'Failed writing file'}), 500
    
    print(f"[API] Saved capture information to {out_path}")

    # Trigger capture
    # The try except is for any error that can happen
    try:
      # We create a new thread so that the HTTP request doesn't block while the capture script is running.
      t = threading.Thread(target=capture_script.capture, daemon=True)
      t.start()
      capture_started = True
    except Exception as e:
      # Playing with threads can be tricky, that's why the try/except exists
      print('Error starting capture:')
      traceback.print_exc()
      capture_started = False

    # Return the path where the capture was saved
    return jsonify({'ok': True, 'path': out_path, 'capture_started': capture_started})
 
  except Exception as e:
    # Error exception
    print('Error saving capture:')
    traceback.print_exc()
    return jsonify({'ok': False, 'message': str(e)}), 500


# ============================= RUN APP (MAIN) ============================ #
if __name__ == '__main__':
  # Execute el backend amb Flask al localhost al port 5000
  app.run(host='127.0.0.1', port=5000)

