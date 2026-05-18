import json

# Helper functions
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


