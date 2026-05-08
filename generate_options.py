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

def readJSON(json_path):
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error: loading JSON failed: {e}")
        return None

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
    
    mcr_converter_rates_table = readJSON(mcr_converter_rates_table_path)
    if mcr_converter_rates_table is None:
        return []

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
                        "option_id": f"mcr{entry['mcr_mhz']}_fcr{fcr_ghz}_zone{zone_idx}",
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
    

def generateCompleteOptions(fc, bw, partial_options_path):
    complete_options = []
    
    # Read the partial options from the json file
    partial_options = readJSON(partial_options_path)
    if partial_options is None:
        return []
    
    # Determine the min and max frequencies of the interest BW
    f_min_target = fc - (bw / 2)
    f_max_target = fc + (bw / 2)

    # Iterate through the partial options and generate complete options by combining them if needed   
    while len(partial_options) > 0:
        # Extract the first partial option and remove it from the list to avoid using it again
        partial_option = partial_options.pop(0) 
        
        if partial_option["is_complete"]:
            # Create a complete option
            complete_option = {
                "complete_option_id": partial_option["option_id"],
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
                    if current_partial_option["f_start"] < combination["partial_options_list"][-1]["f_end"] and current_partial_option["f_end"] > combination["partial_options_list"][-1]["f_end"] and (len(combination["partial_options_list"]) == 1 or current_partial_option["f_start"] > combination["partial_options_list"][-2]["f_end"]):
                        combination["partial_options_list"].append(current_partial_option)
                        
                        # Check if the combination is complete
                        if(combination["partial_options_list"][-1]["f_end"] >= f_max_target and combination["partial_options_list"][0]["f_start"] <= f_min_target):
                            combination["is_complete"] = True
                        else:
                            total_options_checked_since_last_expansion = 0 # We reset this counter since we have expanded at least one combination   
                        
                    # If the current partial option f_max is greater than the combination.list[0] f_min and smaller than the combination.list[0] f_max but smaller than the combination.list[1] f_min(provided it exists), then we append it to the start of the combination list and check if it is complete.
                    elif current_partial_option["f_end"] > combination["partial_options_list"][0]["f_start"] and current_partial_option["f_start"] < combination["partial_options_list"][0]["f_start"] and (len(combination["partial_options_list"]) == 1 or current_partial_option["f_end"] < combination["partial_options_list"][1]["f_start"]):
                        combination["partial_options_list"].insert(0, current_partial_option)
                        
                        # Check if the combination is complete
                        if(combination["partial_options_list"][-1]["f_end"] >= f_max_target and combination["partial_options_list"][0]["f_start"] <= f_min_target):
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
            


def filter_complete_options(complete_options):
    print("Filtering complete options to find the best one...")
    
    
def sort_complete_options(complete_options):
    print("Sorting complete options by number of channels needed...")

# --- Example usage with your capture options ---
fcd = 2.1e9  # 2.1 GHz
bw = 800e6  # 800 MHz
#generatePartialOptions(fcd, bw, './assistanceJSONs/mcr_converter_rates_table.json', './assistanceJSONs/partialOptions.json')
generateCompleteOptions(fcd, bw, './assistanceJSONs/partialOptions.json')
# -------------------------------------------------