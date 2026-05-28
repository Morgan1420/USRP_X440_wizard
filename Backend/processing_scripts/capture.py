
import numpy as np
import uhd
import matplotlib.pyplot as plt
import time


def captureViability():
    # Check all the necessary conditions needed to capture
    
    # Is USRP connected?
    usrp = uhd.usrp.MultiUSRP("addr=192.168.10.2")
    print(usrp)
    
    if usrp is None:
        print("No USRP found. Please check the connection.")
        return 0
    else:
        print("USRP connected successfully.")
    
    
    
    return 1



def capture():
    # Placeholder for the moment
    return 1



uhd.usrp.MultiUSRP("addr=192.168.10.2")

captureViability()