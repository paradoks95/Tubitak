from numpy import loadtxt,arange

def read_file(file_name):
    force_desired,force_loadcell,acc_base,acc_ground,_,_,_,_,_ = loadtxt(file_name,dtype=str,unpack=True)
    return force_desired,force_loadcell,acc_base,acc_ground

def export(file_name,record_type,records,header_line,dt=0.0002):
    name,frequency = file_name.split("_")
    file = open("{}_{}_{}.txt".format(name,record_type,frequency),"w")
    time = arange(0,len(records[0]),dt)
    file.write(header_line)
    for i in range(len(records[0])):
        line = "{}\t{}\t{}\t{}\n".format(round(time[i],4),records[0][i],round(time[i],4),records[1][i])
        file.write(line)
    
    file.close()

force_desired,force_loadcell,acc_base,acc_ground = read_file("10HzSin_1mm")
export("10HzSin_1mm","Acc",[acc_base,acc_ground],"Time [Sec] - Base	g - Base	Time [Sec] - Ground	g - Ground\n")
