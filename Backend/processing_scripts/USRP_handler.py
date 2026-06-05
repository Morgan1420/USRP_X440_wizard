import uhd


# Funció per validar una IP
def validateConnectionToTheUSRP(ip_address=None):
    '''
        Aquesta funció comprova la connexió amb la USRP a través
        de la adreça IP proporcionada.
    '''

    result = {'ipAddr': None}

    if ip_address is None:
        print("Es necessita una adreça IP.")
        return result

    # Validem el format de la IP
    octets = ip_address.split('.')
    if len(octets) != 4 or not all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
        print("Adreça IP no vàlida: {}".format(ip_address))
        result['ipAddr'] = False
        return result

    try:
        device_args = "mgmt_addr={}".format(ip_address)
        uhd.usrp.MultiUSRP(device_args)
        result['ipAddr'] = True
    except Exception:
        result['ipAddr'] = False

    return result


