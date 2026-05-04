def prepare():
    print("ready")


# CHECKERS
def checkInputFields():
    # Mira si els inputs de l'usuari són tots correctes
    # - num_chan entre 1 i 8 (inclosos) 
    print("Tot OK!")


# CALCULATORS



# USRP RELATED
def chooseFPGAImage(num_chan, bw, sample_rate):
    # Calculate the data rate
    #  - The 4 means there are 4 Bytes per sample
    #  - The 8 is to change from B to b
    data_rate = num_chan * sample_rate * 4 * 8

    # Choose the FPGA image
    if (num_chan <= 2):
        if(bw < 400e6):
            if (data_rate < 39e9): # we leave 1GB/s of margin
                return "X4_400"
            elif (data_rate < 199e9):
                return "CG_400"
            else:
                return f"Error: El ratio de dades (data_rate) és massa elevat. Tens: {data_rate}; quan el màxim és: 199GB"
        else:
            if (data_rate < 39e9): # we leave 1GB/s of margin
                return "X4_1600"
            elif (data_rate < 199e9):
                return "CG_1600"
            else:
                return f"Error: El ratio de dades (data_rate) és massa elevat. Tens: {data_rate}; quan el màxim és: 199GB"
            
    else:
        if (data_rate < 39e9): # we leave 1GB/s of margin
            return "X4_400"
        elif (data_rate < 199e9):
            return "CG_400"
        else:
            return f"Error: El ratio de dades (data_rate) és massa elevat. Tens: {data_rate}; quan el màxim és: 199GB"
        
        
        # Load the image into the USRP
    # ....