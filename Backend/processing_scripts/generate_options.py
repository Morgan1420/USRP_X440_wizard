import json
import math

# Helper functions
def readJSON(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error: loading JSON failed: {e}")
        return None

def storeJSON(data, json_path):
    try:
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, sort_keys=True, ensure_ascii=False)
        print(f"Successfully saved data to {json_path}")
    except Exception as e:
        print(f"Error: saving JSON failed: {e}")

# Input functions
def areInputsValid(f_min, f_max, fc, bw):
    # F_min
    if f_min is None or f_min <= 0:
        return False, "Error: Valor per la freqüència mínima (F_min) invàlid, aquest ha de ser un nombre positiu."
    if f_min > 4e9:
        return False, "Error: Valor per la freqüència mínima (F_min) massa alt. El màxim son 4GHz."
    
    # F_max
    if f_max is None or f_max <= 0:
        return False, "Error: Valor per la freqüència màxima (F_max) invàlid, aquest ha de ser un nombre positiu."
    if f_max > 4e9:
        return False, "Error: Valor per la freqüència màxima (F_max) massa alt. El màxim son 4GHz."
    
    # Fc
    if fc is None or fc <= 0:
        return False, "Error: Valor per la freqüència central (Fc) invàlid, aquest ha de ser un nombre positiu."
    if fc > 4e9:
        return False, "Error: Valor per la freqüència central (Fc) massa alt. El màxim son 4GHz."
    
    # BW
    if bw is None or bw <= 0:
        return False, "Error: Valor per la banda passant (BW) invàlid, aquest ha de ser un nombre positiu."
    if bw > fc:
        return False, "Error: Valor per la banda passant (BW) massa alt. Ha de ser menor o igual a la freqüència central (Fc)."

    # Else: if all is good
    return True, "Tots els paràmetres són vàlids."

def processInputs(f_c, bw):    
    
    # Calculate f_min and f_max based on f_c and bw
    f_min = f_c - bw / 2
    f_max = f_c + bw / 2
    
    # Store inputs if they are valid
    if(areInputsValid(f_min=f_min, f_max=f_max, fc=f_c, bw=bw)):
        # Create an empty dictionary of inputs
        userInputs = {"f_min": f_min, "f_max": f_max, "fc": f_c, "bw": bw}
        return True, userInputs
    
    
    return False, "Error: Hi ha un error amb els paràmetres d'entrada. Revisa els valors i torna-ho a intentar."
    
    
# Generate Options Functions
def generatePartialOptions(f_min, f_max, mcr_converter_rates_table_path, partial_options_path):
    # Create the array for the partialOptions
    partial_options = []
    
    # Read mcr_converter_rates table JSON file
    mcr_converter_rates_table = readJSON(mcr_converter_rates_table_path)
    if mcr_converter_rates_table is None:
        print("Error: No s'ha pogut carregar la taula de MCR i FCR des del fitxer JSON.")
        return False

    # Iterate through every item (MCR) in the mcr_converter_rates table
    for entry in mcr_converter_rates_table:
        # Extract the MCR (Master Clock Rate) in Hz
        mcr_hz = entry["mcr_mhz"] * 1e6
        
        # Extract the maximum BW allowed by the MCR
        usable_bw_per_chan = 0.8 * mcr_hz   
        
        # Iterate through all the possible converter rate frequencies
        for fcr_ghz in entry["rfdc_converter_rates_ghz"]:
            # Extract the FCR (Frequency Conversion Rate) in Hz
            fcr = fcr_ghz * 1e9
            
            # Calculate the width of the Nyquist zones
            nyquist_bw = fcr / 2
            
            # Set the Nyquist zone margins to 80% the Nyquist zone (10% on each side)
            margin = 0.1 * nyquist_bw
            
            # Iterate through zones (1st up to the 8th)
            current_f_bottom = f_min # Helper variable to keep track of the frequencies
            for zone_idx in range(1, 9): 
                # Get the min and max frequencies of the current Nyquist zone
                zone_min = (zone_idx - 1) * nyquist_bw
                zone_max = zone_idx * nyquist_bw
                
                # Define the "Safe Zone" within this Nyquist window
                safe_min = zone_min + margin
                safe_max = zone_max - margin
                
                # Check if our target signal overlaps with this safe zone
                overlap_min = max(current_f_bottom, safe_min)
                overlap_max = min(f_max, safe_max)
                
                # If there is an overlap, we create a partial option for this zone
                if overlap_max > overlap_min:
                    interest_bw = overlap_max - overlap_min
                    chans_needed = math.ceil(interest_bw / usable_bw_per_chan)
                    
                    option = {
                        "option_id": f"mcr{entry['mcr_mhz']}_fcr{fcr_ghz}_zone{zone_idx}",
                        "mcr_mhz": entry["mcr_mhz"],
                        "fcr_ghz": fcr_ghz,
                        "nyquist_zone": zone_idx,
                        "f_start": overlap_min,
                        "f_end": overlap_max,
                        "chans_needed": chans_needed,
                        "is_complete": (overlap_min == f_min and overlap_max == f_max)
                    }
                    partial_options.append(option)
                    
                    # Update progress
                    current_f_bottom = overlap_max

    # Store the partial options in a json file
    storeJSON(partial_options, partial_options_path)
    
    return True
    
def generateCompleteOptions(f_min, f_max, partial_options_path):
    complete_options = []
    
    # Read the partial options from the json file
    partial_options = readJSON(partial_options_path)
    if partial_options is None:
        print("Error: No s'ha pogut carregar les opcions parcials des del fitxer JSON.")
        return False

    # Iterate through the partial options and generate complete options by combining them if needed   
    while len(partial_options) > 0:
        # Extract the first partial option and remove it from the list to avoid using it again
        partial_option = partial_options.pop(0) 
        
        if partial_option["is_complete"]:
            # Create a complete option
            complete_option = {
                "complete_option_id": len(complete_options),
                "partial_options": [partial_option],
                "f_start": partial_option["f_start"],
                "f_end": partial_option["f_end"],
                "chans_needed": partial_option["chans_needed"],
                "is_complete": True
                }

            # Add to the complete options list
            complete_options.append(complete_option)
        else:
            # We create a list of all the combinations (useful or not)
            partial_options_combinations = [{"partial_options_list": [partial_option], "is_complete": False}]
            
            # We create a list of the remaining partial options to analyse
            partial_options_remaining = partial_options.copy()
            total_options_checked_since_last_expansion = 0
            
            # While there are still partial options to analyse
            while total_options_checked_since_last_expansion < len(partial_options_remaining) and len(partial_options_remaining) > 0:
                # Update flag
                total_options_checked_since_last_expansion += 1
                
                # Extract the current partial option 
                current_partial_option = partial_options_remaining.pop(0) # Remove it from the list
                
                # Check if the current partial option is already complete, if it is, we skip it
                if current_partial_option["is_complete"]:
                    continue
                
                # Move the current partial option to the end of the list of combinations to analyse
                partial_options_remaining.append(current_partial_option) 
                
                # See how the current partial option can be combined with the existing combinations to create new ones
                for combination in partial_options_combinations:
                    # Check if the combination is already complete, if it is, we skip it
                    if combination["is_complete"]:
                        continue
                    
                    # If the current partial option f_min is smaller than the combination.list[-1] f_max and greater than the combination.list[-1] f_min but greater than the combination.list[-2] f_max(provided it exists), then we append it to the end of the combination list and check if it is complete.
                    if current_partial_option["f_start"] < combination["partial_options_list"][-1]["f_end"] and current_partial_option["f_start"] > combination["partial_options_list"][-1]["f_end"] and current_partial_option["f_end"] > combination["partial_options_list"][-1]["f_end"] and (len(combination["partial_options_list"]) == 1 or current_partial_option["f_start"] > combination["partial_options_list"][-2]["f_end"]):
                        combination["partial_options_list"].append(current_partial_option)
                        
                        # Check if the combination is complete
                        if(combination["partial_options_list"][-1]["f_end"] >= f_max and combination["partial_options_list"][0]["f_start"] <= f_min):
                            combination["is_complete"] = True
                        else:
                            total_options_checked_since_last_expansion = 0 # We reset this counter since we have expanded at least one combination   
                        
                    # If the current partial option f_max is greater than the combination.list[0] f_min and smaller than the combination.list[0] f_max but smaller than the combination.list[1] f_min(provided it exists), then we append it to the start of the combination list and check if it is complete.
                    elif current_partial_option["f_end"] > combination["partial_options_list"][0]["f_start"] and current_partial_option["f_end"] < combination["partial_options_list"][0]["f_end"] and current_partial_option["f_start"] < combination["partial_options_list"][0]["f_start"] and (len(combination["partial_options_list"]) == 1 or current_partial_option["f_end"] < combination["partial_options_list"][1]["f_start"]):
                        combination["partial_options_list"].insert(0, current_partial_option)
                        
                        # Check if the combination is complete
                        if(combination["partial_options_list"][-1]["f_end"] >= f_max and combination["partial_options_list"][0]["f_start"] <= f_min):
                            combination["is_complete"] = True
                        else:
                            total_options_checked_since_last_expansion += 1 # We increment this counter since we have not expanded this combination
                            
                    
            
            # Filter all bad combinations (not complete or with less than 8 channels)
            correct_combinations = []
            for combination in partial_options_combinations:
                total_chans_needed = sum([option["chans_needed"] for option in combination["partial_options_list"]])
                if combination["is_complete"] and total_chans_needed <= 8:
                    correct_combinations.append(combination)
                
            # Append the correct combinations to the complete options list
            for combination in correct_combinations:
                # Create a complete option
                complete_option = {
                    "complete_option_id": len(complete_options),
                    "partial_options": combination["partial_options_list"],
                    "f_start": combination["partial_options_list"][0]["f_start"],
                    "f_end": combination["partial_options_list"][-1]["f_end"],
                    "chans_needed": sum([option["chans_needed"] for option in combination["partial_options_list"]]),
                    "is_complete": True
                    }

                # Add to the complete options list
                complete_options.append(complete_option)
        
         
    storeJSON(complete_options, './assistanceJSONs/completeOptions.json')
    
    return True


def filter_and_sort(complete_options_path="./assistanceJSONs/completeOptions.json", filters_json_path='./assistanceJSONs/filters.json'):
    
    # Read filters from tje JSON file
    filters = readJSON(filters_json_path) or {}
    if filters is None:
        print("Error: No s'ha pogut carregar els filtres des del fitxer JSON.")
        return False
    
    # Extract filters from the file
    min_ch = filters.get('min_channels') if isinstance(filters, dict) else None
    max_ch = filters.get('max_channels') if isinstance(filters, dict) else None
    sorting = (filters.get('sorting') if isinstance(filters, dict) else None) or ''
    sorting = sorting.strip().lower()


    # Read complete options from the JSON file
    complete_options = readJSON(complete_options_path)
    if complete_options is None:
        print("Error: No s'ha pogut carregar les opcions completes des del fitxer JSON.")
        return False

    # Helper functions to extract sorting keys, handling None values
    def chans_needed_of(item):
        try:
            return int(item.get('chans_needed'))
        except Exception:
            return None

    def overlap_width(item):
        try:
            return float(item.get('f_end', 0)) - float(item.get('f_start', 0))
        except Exception:
            return None

    # Filter implementation
    filtered = []
    for item in complete_options:
        # skip invalid items
        if not isinstance(item, dict):
            continue
        
        # Filter for min/max channels needed
        ch = chans_needed_of(item)
        if min_ch is not None:
            if ch is None or ch < int(min_ch):
                continue # If we don't pass the filter we skip to the next item
        if max_ch is not None:
            if ch is None or ch > int(max_ch):
                continue
        
        # Filter options with more than 2 partial options (USRP X440 only supports 2 different sample frequencies at the same time).
        partials = item.get('partial_options', [])
        if len(partials) > 2:
            continue
        
        filtered.append(item)

    # Sorting implementation
    if sorting == 'max chan' or sorting == 'max chan(s)' or sorting == 'max chan(s)':
        filtered.sort(key=lambda i: (chans_needed_of(i) is None, -(chans_needed_of(i) or 0)))
    elif sorting == 'min chan' or sorting == 'min chan(s)':
        filtered.sort(key=lambda i: (chans_needed_of(i) is None, chans_needed_of(i) or 0))
    elif sorting == 'min overlap' or sorting == 'min overlap()' or sorting == 'min overlap':
        # sort by smallest frequency span (f_end - f_start), then by chans needed
        def key_fn(i):
            ow = overlap_width(i)
            chv = chans_needed_of(i) or 0
            return ((ow is None), (ow if ow is not None else float('inf')), chv)

        filtered.sort(key=key_fn)
    else:
        # default: sort by chans_needed ascending, then by f_start
        filtered.sort(key=lambda i: (chans_needed_of(i) is None, chans_needed_of(i) or 0, i.get('f_start', 0)))

    
    # Store the filtered and sorted options back to a JSON file
    storeJSON(filtered, './assistanceJSONs/filteredOptions.json')
    
    # Return True if everything went ok :)
    return True

