import uhd


# Funció per validar IPs
def validateConnectionToTheUSRP(ip_address_1=None, ip_address_2=None):
    '''
        Aquesta funció comprova la connexió amb la USRP a través 
        de les adreces IP proporcionades. 
    '''

    # El diccionari result és el que retornarà la funció. Conté l'estat
    # de cada adreça IP i serà: None (no proporcionada), True (connexió vàlida) 
    # o False (connexió no vàlida)
    result = {'ipA': None, 'ipB': None}

    # Primer mirem que hi hagi almenys una adreça
    if ip_address_1 is None and ip_address_2 is None:
        print("Es necessita com a mínim una adreça IP.")
        return result

    # Validem que el format de les adreces IP sigui correcte
    for idx, ip in enumerate([ip_address_1, ip_address_2]):
        # Assignem la clau corresponent per a cada IP
        key = 'ipA' if idx == 0 else 'ipB'
        
        # Validem el format de la IP si l'usuari l'ha proporcionat
        if ip is not None:
            octets = ip.split('.')
            if len(octets) != 4 or not all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
                print("Adreça IP no vàlida: {}".format(ip))
                result[key] = False
                return result

    # Verifiquem la primera adreça IP
    if ip_address_1 is not None:
        # Fem servir el try-except per capturar qualsevol error que pugui sorgir en intentar connectar amb la USRP
        try:
            # Assignem els paràmetres de la USRP
            device_args = "mgmt_addr={}".format(ip_address_1)
            
            # Comprovem la connexió 
            uhd.usrp.MultiUSRP(device_args)
            #print("USRP found at IP address: {}".format(ip_address_1))
            
            # Si no hi ha excepcions, la connexió és vàlida
            result['ipA'] = True
        except Exception:
            #print("No USRP found at IP address: {}.".format(ip_address_1))ç
            
            # Si hi ha excepcions, la connexió és invàlida
            result['ipA'] = False

    # Verifiquem la segona adreça IP
    if ip_address_2 is not None:
        try:
            device_args = "mgmt_addr={}".format(ip_address_2)
            uhd.usrp.MultiUSRP(device_args)
            #print("USRP found at IP address: {}".format(ip_address_2))
            result['ipB'] = True
        except Exception:
            #print("No USRP found at IP address: {}.".format(ip_address_2))
            result['ipB'] = False

    return result


