from numpy import loadtxt,arange,insert,diff
from pandas import DataFrame,ExcelWriter
from Graphs import process
from scipy.integrate import cumtrapz

def acc2vel(acceleration,dt=0.0005):
    vel = cumtrapz(acceleration*981,dx=dt)
    vel = insert(vel,0,0)
    return vel

def vel2acc(velocity,dt=0.0005):
    time = arange(0, len(velocity) * dt, dt)
    return insert(diff(velocity)/diff(time),0,0)/981

def read_file(file_name,channels,factors):
    datas = [loadtxt(file_name,skiprows=8,unpack=True)][0]
    scaled_datas = []
    for i in range(len(channels)):
        channel = channels[i]
        offset = factors[i-1][0]
        scale = factors[i-1][1]
        f = lambda x: x*scale - offset
        scaled_datas.append(f(datas[channel-1]))

    return scaled_datas

def export2excel(fileName):
    accelerations = read_file(fileName,[1,2,3,4,5,6,7,8],[[0,0.5],[0,0.5],[0,0.5],[0,0.5],[0,0.5],[0,0.5],[0,0.5],[0,0.5]])
    velocities = read_file(fileName,[9,10,11,12,13,14,15,16],[[0,3.47],[0,3.47],[0,3.47],[0,3.47],[0,3.47],[0,3.47],[0,3.47],[0,3.47]])
    AccSheet = {}
    VelSheet = {}
    for i in range(len(accelerations)):
        acc = process(accelerations[i],0.0005,4,0,0)
        vel = process(velocities[i],0.0005,4,0,0)
        AccSheet["Accelerometer {}(g)".format(i+1)] = acc
        AccSheet["Jeofon {}(cm/s)".format(i+1)] = vel2acc(vel)
        VelSheet["Accelerometer {}(g)".format(i+1)] = acc2vel(acc)
        VelSheet["Jeofon {}(cm/s)".format(i+1)] =vel
    
    writer = ExcelWriter('{}.xlsx'.format(fileName.split(".")[0]), engine='xlsxwriter')
    DF1 = DataFrame(AccSheet)
    DF2 = DataFrame(VelSheet)
    DF1.to_excel(writer,sheet_name="Accelerations",index=False)
    DF2.to_excel(writer,sheet_name="Velocities",index=False)
    writer.save()

export2excel("SP-70-L50.txt")