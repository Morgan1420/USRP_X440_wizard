import json
import math

# Funcions auxiliars
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

# Funcions d'entrada
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

    # Si tot és correcte
    return True, "Tots els paràmetres són vàlids."

def processInputs(f_c, bw):    
    
    # Calculem f_min i f_max a partir de f_c i bw
    f_min = f_c - bw / 2
    f_max = f_c + bw / 2
    
    # Guardem les dades si són vàlides
    if(areInputsValid(f_min=f_min, f_max=f_max, fc=f_c, bw=bw)):
        # Creem un diccionari buit amb les dades d'entrada
        userInputs = {"f_min": f_min, "f_max": f_max, "fc": f_c, "bw": bw}
        return True, userInputs
    
    
    return False, "Error: Hi ha un error amb els paràmetres d'entrada. Revisa els valors i torna-ho a intentar."
    
    
# Funcions per generar opcions
def generatePartialOptions(f_min, f_max, mcr_converter_rates_table_path, partial_options_path):
    # Creem l'array per a les partialOptions
    partial_options = []
    
    # Llegim el fitxer JSON de la taula mcr_converter_rates
    mcr_converter_rates_table = readJSON(mcr_converter_rates_table_path)
    if mcr_converter_rates_table is None:
        print("Error: No s'ha pogut carregar la taula de MCR i FCR des del fitxer JSON.")
        return False

    # Iterem per cada element (MCR) de la taula mcr_converter_rates
    for entry in mcr_converter_rates_table:
        # Extreiem la MCR (Master Clock Rate) en Hz
        mcr_hz = entry["mcr_mhz"] * 1e6
        
        # Extreiem l'ample de banda màxim permès per la MCR
        usable_bw_per_chan = 0.8 * mcr_hz   
        
        # Iterem per totes les freqüències possibles del convertidor
        for fcr_ghz in entry["rfdc_converter_rates_ghz"]:
            # Extreiem la FCR (Frequency Conversion Rate) en Hz
            fcr = fcr_ghz * 1e9
            
            # Calculem l'amplada de les zones de Nyquist
            nyquist_bw = fcr / 2
            
            # Fixem els marges de la zona de Nyquist al 80% de la zona (10% a cada costat)
            margin = 0.1 * nyquist_bw
            
            # Iterem per les zones (de la primera fins a la vuitena)
            current_f_bottom = f_min # Variable auxiliar per fer el seguiment de les freqüències
            for zone_idx in range(1, 9): 
                # Obtenim les freqüències mínima i màxima de la zona de Nyquist actual
                zone_min = (zone_idx - 1) * nyquist_bw
                zone_max = zone_idx * nyquist_bw
                
                # Definim la "zona segura" dins d'aquesta finestra de Nyquist
                safe_min = zone_min + margin
                safe_max = zone_max - margin
                
                # Comprovem si el senyal objectiu se solapa amb aquesta zona segura
                overlap_min = max(current_f_bottom, safe_min)
                overlap_max = min(f_max, safe_max)
                
                # Si hi ha solapament, creem una opció parcial per a aquesta zona
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
                    
                    # Actualitzem el progrés
                    current_f_bottom = overlap_max

    # Guardem les opcions parcials en un fitxer JSON
    storeJSON(partial_options, partial_options_path)
    
    return True
    
def generateCompleteOptions(f_min, f_max, partial_options_path):
    complete_options = []
    
    # Llegim les opcions parcials des del fitxer JSON
    partial_options = readJSON(partial_options_path)
    if partial_options is None:
        print("Error: No s'ha pogut carregar les opcions parcials des del fitxer JSON.")
        return False

    # Iterem per les opcions parcials i generem opcions completes combinant-les si cal   
    while len(partial_options) > 0:
        # Extreiem la primera opció parcial i la retirem de la llista per no reutilitzar-la
        partial_option = partial_options.pop(0) 
        
        if partial_option["is_complete"]:
            # Creem una opció completa
            complete_option = {
                "complete_option_id": len(complete_options),
                "partial_options": [partial_option],
                "f_start": partial_option["f_start"],
                "f_end": partial_option["f_end"],
                "chans_needed": partial_option["chans_needed"],
                "is_complete": True
                }

            # Afegim l'opció a la llista d'opcions completes
            complete_options.append(complete_option)
        else:
            # Creem una llista amb totes les combinacions (útils o no)
            partial_options_combinations = [{"partial_options_list": [partial_option], "is_complete": False}]
            
            # Creem una llista de les opcions parcials restants per analitzar
            partial_options_remaining = partial_options.copy()
            total_options_checked_since_last_expansion = 0
            
            # Mentre encara hi hagi opcions parcials per analitzar
            while total_options_checked_since_last_expansion < len(partial_options_remaining) and len(partial_options_remaining) > 0:
                # Actualitzem el comptador
                total_options_checked_since_last_expansion += 1
                
                # Extreiem l'opció parcial actual
                current_partial_option = partial_options_remaining.pop(0) # Remove it from the list
                
                # Comprovem si l'opció parcial actual ja és completa; si ho és, la saltem
                if current_partial_option["is_complete"]:
                    continue
                
                # Moure l'opció parcial actual al final de la llista de combinacions per analitzar
                partial_options_remaining.append(current_partial_option) 
                
                # Veiem com es pot combinar l'opció parcial actual amb les combinacions existents per crear-ne de noves
                for combination in partial_options_combinations:
                    # Comprovem si la combinació ja és completa; si ho és, la saltem
                    if combination["is_complete"]:
                        continue
                    
                    # Si el f_min de l'opció parcial actual és menor que el f_max de combination.list[-1] i més gran que el f_min de combination.list[-1] però més gran que el f_max de combination.list[-2] (si existeix), l'afegim al final de la llista i comprovem si és completa.
                    if current_partial_option["f_start"] < combination["partial_options_list"][-1]["f_end"] and current_partial_option["f_start"] > combination["partial_options_list"][-1]["f_end"] and current_partial_option["f_end"] > combination["partial_options_list"][-1]["f_end"] and (len(combination["partial_options_list"]) == 1 or current_partial_option["f_start"] > combination["partial_options_list"][-2]["f_end"]):
                        combination["partial_options_list"].append(current_partial_option)
                        
                        # Comprovem si la combinació és completa
                        if(combination["partial_options_list"][-1]["f_end"] >= f_max and combination["partial_options_list"][0]["f_start"] <= f_min):
                            combination["is_complete"] = True
                        else:
                            total_options_checked_since_last_expansion = 0 # Reiniciem aquest comptador perquè hem expandit almenys una combinació   
                        
                    # Si el f_max de l'opció parcial actual és més gran que el f_min de combination.list[0] i més petit que el f_max de combination.list[0] però més petit que el f_min de combination.list[1] (si existeix), l'afegim a l'inici de la llista i comprovem si és completa.
                    elif current_partial_option["f_end"] > combination["partial_options_list"][0]["f_start"] and current_partial_option["f_end"] < combination["partial_options_list"][0]["f_end"] and current_partial_option["f_start"] < combination["partial_options_list"][0]["f_start"] and (len(combination["partial_options_list"]) == 1 or current_partial_option["f_end"] < combination["partial_options_list"][1]["f_start"]):
                        combination["partial_options_list"].insert(0, current_partial_option)
                        
                        # Comprovem si la combinació és completa
                        if(combination["partial_options_list"][-1]["f_end"] >= f_max and combination["partial_options_list"][0]["f_start"] <= f_min):
                            combination["is_complete"] = True
                        else:
                            total_options_checked_since_last_expansion += 1 # Incrementem aquest comptador perquè no hem expandit aquesta combinació
                            
                    
            
            # Filtrarem totes les combinacions dolentes (no completes o amb menys de 8 canals)
            correct_combinations = []
            for combination in partial_options_combinations:
                total_chans_needed = sum([option["chans_needed"] for option in combination["partial_options_list"]])
                if combination["is_complete"] and total_chans_needed <= 8:
                    correct_combinations.append(combination)
                
            # Afegim les combinacions correctes a la llista d'opcions completes
            for combination in correct_combinations:
                # Creem una opció completa
                complete_option = {
                    "complete_option_id": len(complete_options),
                    "partial_options": combination["partial_options_list"],
                    "f_start": combination["partial_options_list"][0]["f_start"],
                    "f_end": combination["partial_options_list"][-1]["f_end"],
                    "chans_needed": sum([option["chans_needed"] for option in combination["partial_options_list"]]),
                    "is_complete": True
                    }

                # Afegim l'opció a la llista d'opcions completes
                complete_options.append(complete_option)
        
         
    storeJSON(complete_options, './assistanceJSONs/completeOptions.json')
    
    return True


def filter_and_sort(complete_options_path="./assistanceJSONs/completeOptions.json", filters_json_path='./assistanceJSONs/filters.json'):
    
    # Llegim els filtres des del fitxer JSON
    filters = readJSON(filters_json_path) or {}
    if filters is None:
        print("Error: No s'ha pogut carregar els filtres des del fitxer JSON.")
        return False
    
    # Extreiem els filtres del fitxer
    min_ch = filters.get('min_channels') if isinstance(filters, dict) else None
    max_ch = filters.get('max_channels') if isinstance(filters, dict) else None
    sorting = (filters.get('sorting') if isinstance(filters, dict) else None) or ''
    sorting = sorting.strip().lower()


    # Llegim les opcions completes des del fitxer JSON
    complete_options = readJSON(complete_options_path)
    if complete_options is None:
        print("Error: No s'ha pogut carregar les opcions completes des del fitxer JSON.")
        return False

    # Funcions auxiliars per extreure les claus d'ordenació, gestionant valors None
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

    # Implementació del filtratge
    filtered = []
    for item in complete_options:
        # Saltem els elements invàlids
        if not isinstance(item, dict):
            continue
        
        # Filtratge pel mínim/màxim de canals necessaris
        ch = chans_needed_of(item)
        if min_ch is not None:
            if ch is None or ch < int(min_ch):
                continue # Si no superem el filtre, passem al següent element
        if max_ch is not None:
            if ch is None or ch > int(max_ch):
                continue
        
        # Filtratge d'opcions amb més de 2 opcions parcials (l'USRP X440 només suporta 2 freqüències de mostreig diferents alhora).
        partials = item.get('partial_options', [])
        if len(partials) > 2:
            continue
        
        filtered.append(item)

    # Implementació de l'ordenació
    if sorting == 'max chan' or sorting == 'max chan(s)' or sorting == 'max chan(s)':
        filtered.sort(key=lambda i: (chans_needed_of(i) is None, -(chans_needed_of(i) or 0)))
    elif sorting == 'min chan' or sorting == 'min chan(s)':
        filtered.sort(key=lambda i: (chans_needed_of(i) is None, chans_needed_of(i) or 0))
    elif sorting == 'min overlap' or sorting == 'min overlap()' or sorting == 'min overlap':
        # Ordenem pel tram de freqüència més petit (f_end - f_start) i després pels canals necessaris
        def key_fn(i):
            ow = overlap_width(i)
            chv = chans_needed_of(i) or 0
            return ((ow is None), (ow if ow is not None else float('inf')), chv)

        filtered.sort(key=key_fn)
    else:
        # default: sort by chans_needed ascending, then by f_start
        filtered.sort(key=lambda i: (chans_needed_of(i) is None, chans_needed_of(i) or 0, i.get('f_start', 0)))

    
    # Guardem les opcions filtrades i ordenades en un fitxer JSON
    storeJSON(filtered, './assistanceJSONs/filteredOptions.json')
    
    # Retornem True si tot ha anat bé :)
    return True

