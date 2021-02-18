from numpy import loadtxt,array,arange,insert,abs,diff,where
from scipy.integrate import cumtrapz
import os
from PreProcess import *
from Spectra import FourierAmplitude
import matplotlib.pyplot as plt
from math import ceil,floor

def modify_file(file_name):
    old_file = open(file_name)
    old_text = old_file.read()
    old_file.close()
    os.remove(file_name)
    new_text = old_text.replace(",",".")
    new_file = open(file_name,"w")
    new_file.write(new_text)
    new_file.close()

def time_series(acceleration,dt):
    vel = cumtrapz(acceleration*981,dx=dt)
    vel = insert(vel,0,0)
    disp = cumtrapz(vel,dx=dt)
    disp = insert(disp, 0, 0)
    return vel,disp

def vel2acc(velocity,dt):
    time = arange(0, len(velocity) * dt, dt)
    return insert(diff(velocity)/diff(time),0,0)/981

def read_file(file_name,channels,f=lambda x:x):
    data = [loadtxt(file_name,skiprows=8,unpack=True)]
    data = f(data[0])
    return data[channels]

def read_dt(file_name):
    f = open(file_name)
    r = f.readlines()
    row = r[4]
    return float(row.split(":")[1])

def process(accelerations,dt,bc_order,lowcut,highcut,filtering=False):
    time = arange(0,len(accelerations)*dt,dt)
    pa = BaselineCorrection(accelerations,dt,bc_order)
    if filtering:
        pa = Filtering(pa,dt,"Butterworth","bandpass",lowcut,highcut)
    
    
    return pa


def amplitude_reduction(free_field,trench):
    #Normalized accelerations
    return trench/free_field

def normalized_depth(frequencies,trench_depth,Vs):
    return array(frequencies)*trench_depth/Vs

def channel_graph2(processed_acceleration,acceleration,dt,name):
    velocity,displacement = time_series(acceleration,dt)
    pro_velocity,pro_displacement = time_series(processed_acceleration,dt)
    times = arange(0, len(acceleration) * dt, dt)

    fig = plt.figure(figsize=(10, 7))
    spec = fig.add_gridspec(ncols=2, nrows=4)
    #UNPROCESSED
    #Acceleration - Time
    ax11 = fig.add_subplot(spec[0, 0])
    ax11.plot(times, acceleration, label="{} g".format(round(max(abs(acceleration)),4)))
    ax11.legend()
    ax11.set_title("Unprocessed")
    ax11.set_xlabel("Time(s)")
    ax11.set_ylabel("Acceleration(g)")
    ax11.grid()

    #Velocity - Time
    ax21 = fig.add_subplot(spec[1, 0])
    ax21.plot(times, velocity)
    ax21.set_xlabel("Time(s)")
    ax21.set_ylabel("Velocity(cm/s)")
    ax21.grid()

    #Displacement - Time
    ax31 = fig.add_subplot(spec[2, 0])
    ax31.plot(times, displacement)
    ax31.set_xlabel("Time(s)")
    ax31.set_ylabel("Displacement(cm)")
    ax31.grid()

    #Fourier
    f,fa,pa = FourierAmplitude(acceleration,dt)
    ax41 = fig.add_subplot(spec[3, 0])
    ax41.plot(f, fa)
    ax41.semilogx()
    ax41.set_xlabel("Frequency(Hz)")
    ax41.set_ylabel("Amplitude")
    ax41.grid()

    # PROCESSED
    # Acceleration - Time
    ax12 = fig.add_subplot(spec[0, 1])
    ax12.plot(times, processed_acceleration, label="{} g".format(round(max(abs(processed_acceleration)), 4)))
    ax12.legend()
    ax12.set_title("Processed")
    ax12.set_xlabel("Time(s)")
    ax12.set_ylabel("Acceleration(g)")
    ax12.grid()

    # Velocity - Time
    ax22 = fig.add_subplot(spec[1, 1])
    ax22.plot(times, pro_velocity)
    ax22.set_xlabel("Time(s)")
    ax22.set_ylabel("Velocity(cm/s)")
    ax22.grid()

    # Displacement - Time
    ax32 = fig.add_subplot(spec[2, 1])
    ax32.plot(times, pro_displacement)
    ax32.set_xlabel("Time(s)")
    ax32.set_ylabel("Displacement(cm)")
    ax32.grid()

    # Fourier
    pro_f, pro_fa, pro_pa = FourierAmplitude(processed_acceleration, dt)
    ax42 = fig.add_subplot(spec[3, 1])
    ax42.plot(pro_f, pro_fa)
    ax42.semilogx()
    ax42.set_xlabel("Frequency(Hz)")
    ax42.set_ylabel("Amplitude")
    ax42.grid()

    #fig.show()
    fig.savefig(os.path.join("Graphs","Processed Data",name))

def NA_graph(accelerations,velocities,distances):
    path = os.path.join("Graphs","Processed","Normalized")
    path_creator(path)
    max_acc = array([max(abs(i)) for i in accelerations])
    NA = max_acc / max(max_acc)
    max_vel = array([max(abs(i)) for i in velocities])
    NV = max_vel / max(max_vel)
    distances = distances[:len(NA)]
    plt.plot(distances,NA,label = "Acceleration")
    plt.plot(distances,NV,label = "Velocity")
    plt.xlabel = "Distance(m)"
    plt.ylabel = "Normalized Values"
    plt.legend()
    plt.semilogy()
    plt.grid()
    plt.savefig(os.path.join(path,"Normalized"),bbox_inches='tight')
    plt.close()

def velocity_graph(accelerations,velocities,dt):
    fig = plt.figure(constrained_layout = False,figsize=(10,10))
    spec = fig.add_gridspec(ncols=2, nrows=len(accelerations))
    times = arange(0, len(accelerations[0]) * dt, dt)
    for i in range(len(accelerations)):
        acc = accelerations[i]
        vel = velocities[i]
        acctovel,disp = time_series(acc,dt)
        veltoacc = vel2acc(vel,times)
        ax1 = fig.add_subplot(spec[i,0])
        ax1.plot(times,vel,label="Calculated",linewidth=1)
        ax1.plot(times,acctovel,label="Measured",linewidth = 1)
        ax1.legend()
        ax1.set_title("Velocity")
        ax1.grid()

        ax2 = fig.add_subplot(spec[i,1])
        ax2.plot(times,acc,label="Calculated",linewidth=1)
        ax2.plot(times,veltoacc,label="Measured",linewidth = 1)
        ax2.legend()
        ax2.set_title("Acceleration")
        ax2.grid()
    fig.savefig(os.path.join("Graphs","Velocity Comparisons","Channel {}".format(i+1)))

def path_creator(path):
    if not os.path.exists(path):
        os.makedirs(path)

def acceleration_time(acceleration,velocity,dt,channel_no,process):
    path = os.path.join("Graphs",process,"Channel {}".format(channel_no))
    path_creator(path)
    time = arange(0,len(acceleration)*dt,dt)
    acceleration2 = vel2acc(velocity,dt)
    plt.plot(time,acceleration,label="Accelerometer({} g)".format(round(max(abs(acceleration)),4)),linewidth = 0.5)
    plt.plot(time,acceleration2,label="Jeofon({} g)".format(round(max(abs(acceleration2)),4)),linewidth = 0.5)
    plt.grid()
    plt.legend()
    plt.xlabel("Time (s)")
    plt.ylabel("Acceleration (g)")
    plt.savefig(os.path.join(path,"AccelerationVsTime"),bbox_inches='tight')
    plt.close()

def velocity_time(acceleration,velocity,dt,channel_no,process):
    path = os.path.join("Graphs",process,"Channel {}".format(channel_no))
    path_creator(path)
    time = arange(0,len(velocity)*dt,dt)
    velocity2,_ = time_series(acceleration,dt)
    plt.plot(time,velocity,label="Jeofon({} m/s)".format(round(max(abs(velocity)),4)),linewidth=0.5)
    plt.plot(time,velocity2,label="Accelerometer({} m/s)".format(round(max(abs(velocity2)),4)),linewidth=0.5)
    plt.grid()
    plt.legend()
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (cm/s)")
    plt.savefig(os.path.join(path,"VelocityVsTime"),bbox_inches='tight')
    plt.close()

def fourierSpectrum(acceleration,velocity,dt,channel_no,process,startFrom=10,endAt=100):
    path = os.path.join("Graphs",process,"Channel {}".format(channel_no))
    path_creator(path)
    vel,_ = time_series(acceleration,dt)
    f,fa,_ = FourierAmplitude(velocity,dt)
    f2,fa2,_ = FourierAmplitude(vel,dt)
    first_index =(abs(f-startFrom)).argmin()
    last_index =(abs(f-endAt)).argmin()
    plt.plot(f[first_index:last_index],fa[first_index:last_index],label="Jeofon({})".format(round(max(abs(fa[first_index:])),4)))
    plt.plot(f2[first_index:last_index],fa2[first_index:last_index],label="Accelerometer({})".format(round(max(abs(fa2[first_index:])),4)))
    plt.grid()
    plt.legend()
    plt.xticks(arange(startFrom,endAt+10,10))
    #plt.semilogx()
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Fourier Amplitude")
    plt.savefig(os.path.join(path,"FourierSpectrum"),bbox_inches='tight')
    plt.close()


