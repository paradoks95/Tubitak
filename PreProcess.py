from numpy import poly1d,polyfit,array,arange
from scipy.signal import butter,lfilter,cheby2,bessel

def BaselineCorrection(acceleration,dt,order):
    time = arange(0,len(acceleration)*dt,dt)
    constants = polyfit(time,acceleration,order)
    f = poly1d(constants)
    predicted = f(time)
    return array(acceleration) - predicted

def Filtering(data,dt,filter_type,filter_configuration,lowcut,highcut = 0,order=4):
    #filter_configuration : low, high, bandpass, bandstop
    nyq = 0.5 / dt
    low = lowcut / nyq
    high = highcut / nyq
    if filter_configuration == "bandpass" or filter_configuration=="bandstop":
        cutoff = [low,high]
    else:
        cutoff = low

    if filter_type == "Butterworth":
        #Tam doğru sonuç
        b,a = butter(order, cutoff, btype=filter_configuration)
    elif filter_type == "Bessel":
        #Yaklaşık sonuç
        b, a = bessel(order, cutoff, btype=filter_configuration)

    y = lfilter(b, a, data)

    return y
