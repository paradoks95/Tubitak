from numpy import loadtxt,array,where,mean,arange,append,flipud
import matplotlib.pyplot as plt
import os

os.chdir("..")
os.chdir("Output")
def read_file(file_name):
    os.chdir(file_name)
    data = [loadtxt("{}.txt".format(file_name),skiprows=1,unpack=True)]
    os.chdir("..")
    acc_list = []
    for i in data[0][1:]:
        acc_list.append(max(abs(i)))

    return array(sorted(acc_list,reverse=True))/max(acc_list)
    #return flipud(array(acc_list)/max(acc_list))

def NA_generator(file_name,frequency_list):
    data = {}
    for f in frequency_list:
        f_name = file_name + "_Hz{}".format(f)
        data[f] = read_file(f_name)

    return data

def trench_depth_NA(frequency_list,depth_list):
    data = {}
    for f in frequency_list:
        for d in depth_list:
            f_name = "O2_Hz{}_D{}".format(f,int(d*10))
            data[f_name] = read_file(f_name)

    return data
def trench_depth_AR(frequency_list,depth_list,double_trench,free_field):
    data = {}
    for f in frequency_list:
        F_NA = free_field[f]
        for d in depth_list:
            f_name = "O2_Hz{}_D{}".format(f,int(d*10))
            O2_NA = double_trench[f_name]

            data[f_name] = O2_NA/F_NA

    return data

def Ar_generator(depth, frequency_list,free_field,open_trench):
    data = {}
    for f in frequency_list:
        f_NA = free_field[f]
        O_NA = open_trench[f]
        D = depth*f/212.85
        data[round(D,2)] = O_NA/f_NA

    return data

def generate_graph(title,vertical_line,ylabel,xlabel,x,*accelerations):
    for i in accelerations:
        y = i["Acc"]
        plt.scatter(x,y,label = i["label"])
        plt.semilogy()
        plt.legend()
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.xticks(arange(1,20,1))
        if vertical_line:
            for v in vertical_line:
                plt.vlines(v,0,max(y))
        plt.title(title)
    plt.grid()
    plt.savefig(title)
    plt.show()
    plt.close()

def channel_graph(title,ylabel,xlabel,accelerations,x):
    for i in range(len(accelerations[x[0]])):
        acc_list = []
        for n in x:
            acc_list.append(accelerations[n][i])
        plt.plot(x,array(acc_list)/max(acc_list),label="Channel {}".format(i+1))
        plt.semilogy()
    plt.legend()
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.grid()
    plt.savefig(title)
    plt.show()
    plt.close()
def Ar_NormalizedDepth(title,field,abaqus,acc_num,vline=False):
    abaqus_x = list(abaqus.keys())
    abaqus_y = []
    for k in abaqus_x:
        acc = abaqus[k][acc_num]
        abaqus_y.append(acc)

    field_x = list(field.keys())
    field_y = []
    for k in field_x:
        acc = field[k][acc_num]
        field_y.append(acc)

    plt.plot(abaqus_x,abaqus_y,label="Abaqus")
    plt.scatter(field_x,field_y,label="Field")
    plt.semilogy()
    plt.grid()
    plt.legend()
    plt.title(title)
    if vline:
        for i in vline:
            plt.vlines(i,0,max(list(abaqus_y) + list(field_y)))
    plt.ylabel("Amplitude Reduction Ratio")
    plt.xlabel("Normalized Depth")
    plt.savefig(title)
    plt.close()

def AR_Depth(title,abaqus,acc_num):
    abaqus_x = arange(2,6.5,0.5)
    for f in [50,75,100]:
        abaqus_y = []
        for d in abaqus_x:
            key = "O2_Hz{}_D{}".format(f,int(d*10))
            acc = abaqus[key][acc_num]
            abaqus_y.append(acc)

        plt.plot(abaqus_x,abaqus_y,label="{} Hz".format(f))
    plt.semilogy()
    plt.legend()
    plt.grid()
    plt.title(title)
    plt.ylabel("Amplitude Reduction Ratio")
    plt.xlabel("Trench Depth")
    plt.savefig(title)
    plt.close()


d = [1,3.5,6,8.5,11,13.5,16,18.5]
generate_graph("Comparison",[4],"Normalized Acceleration","Distance",d,
               {"Acc":read_file("FreeField100Hz_Planar2"),"type":"scatter","label":"Material"},
               {"Acc":read_file("Rough"),"type":"scatter","label":"Part(Rough)"},
               {"Acc":read_file("FreeField"),"type":"scatter","label":"Free Field"}
               )
