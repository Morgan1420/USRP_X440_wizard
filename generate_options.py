import json
import math

def areInputsValid(fc, bw, time, num_chan):
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
    
    # Time
    if time is None or time <= 0:
        return False, "Error: Valor per el temps (Time) invàlid, aquest ha de ser un nombre positiu."
    if time > 5:
        return True, "Warning: Valor per el temps (Time) massa alt. Consider baixar-lo per evitar fitxers de captura grans."
    
    # Num channels
    if num_chan < 1 or num_chan > 8:
        return False, "Error: Valor per el nombre de canals (Num Channels) invàlid. Ha de ser un enter entre 1 i 8."
    
    # Else: if all is good
    return True, "Tots els paràmetres són vàlids."

def storeJSON(data, json_path):
    try:
        with open(json_path, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)
        print(f"Successfully saved data to {json_path}")
    except Exception as e:
        print(f"Error: saving JSON failed: {e}")



def generatePartialOptions(fc, bw, mcr_converter_rates_table_path, partial_options_path):
    # Create the array for the partialOptions
    partial_options = []
    
    # Determine the min and max frequencies of the interest BW
    f_min_target = fc - (bw / 2)
    f_max_target = fc + (bw / 2)
    
    # Read converter_rates table (.json)
    with open(mcr_converter_rates_table_path, 'r') as file:
        mcr_converter_rates_table = json.load(file)
     
    for entry in mcr_converter_rates_table:
        mcr_hz = entry["mcr_mhz"] * 1e6
        
        # Usable BW is usually 80% of the Nyquist bandwidth (0.8 * mcr/2)
        usable_bw_per_chan = 0.8 * mcr_hz   
        
        # Iterate through all the possible converter rate frequencies
        for fcr_ghz in entry["rfdc_converter_rates_ghz"]:
            fcr = fcr_ghz * 1e9
            nyquist_bw = fcr / 2
            # 10% guard band at each edge of the Nyquist zone
            margin = 0.1 * nyquist_bw
            
            current_f_bottom = f_min_target
            
            # Iterate through zones (1st, 2nd, 3rd...)
            for zone_idx in range(1, 9): # X440 covers up to ~4GHz
                zone_min = (zone_idx - 1) * nyquist_bw
                zone_max = zone_idx * nyquist_bw
                
                # Define the "Safe Zone" within this Nyquist window
                safe_min = zone_min + margin
                safe_max = zone_max - margin
                
                # Check if our target signal overlaps with this safe zone
                overlap_min = max(current_f_bottom, safe_min)
                overlap_max = min(f_max_target, safe_max)
                
                if overlap_max > overlap_min:
                    interest_bw = overlap_max - overlap_min
                    chans_needed = math.ceil(interest_bw / usable_bw_per_chan)
                    
                    option = {
                        "mcr_mhz": entry["mcr_mhz"],
                        "fcr_ghz": fcr_ghz,
                        "nyquist_zone": zone_idx,
                        "f_start": overlap_min,
                        "f_end": overlap_max,
                        "chans_needed": chans_needed,
                        "is_complete": (overlap_min == f_min_target and overlap_max == f_max_target)
                    }
                    partial_options.append(option)
                    
                    # Update progress
                    current_f_bottom = overlap_max

    # Store the partial options in a json file
    storeJSON(partial_options, partial_options_path)
    return partial_options
    

def generateCompleteOptions(partial_options):
    complete_options = []
    
    
    
    return complete_options

# --- Example usage with your capture options ---
capture_results = generatePartialOptions(2.1e9, 100e6, './assistanceJSONs/mcr_converter_rates_table.json', './assistanceJSONs/partialOptions.json')
