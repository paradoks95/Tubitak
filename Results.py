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
        x = i["X"]
        if i["type"] == "line":
            plt.plot(x,y,label = i["label"])
        else:
            plt.scatter(x, y, label=i["label"])
        plt.semilogy()
        plt.legend()
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.xticks(arange(2,24,2))
        plt.ylim([0.0001,3])
        if vertical_line:
            for v in vertical_line:
                plt.text(v, 1.1, "Dalga\nBariyeri", fontsize=9,
                         horizontalalignment='center')
                plt.vlines(v,0,1)
        #plt.title(title)
    plt.grid()
    plt.savefig(os.path.join("Grafikler",title))
    #plt.show()
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


field_results = {"Mentese_A_L50_30Hz": [1, 0.923374182, 0.480633789, 0.308068381, 0.219583229, 0.223512138, 0.179632603, 0.127040088, 0.172218502],
                 "Mentese_A_L50_50Hz": [1,0.427807539,0.03228388,0.014273471,0.044975451,0.038383464,0.027038681,0.027375821,0.024698215],
                 "Mentese_A_L50_90Hz": [1, 0.150339752, 0.04516516, 0.017884863, 0.009755274, 0.007204952, 0.010068533, 0.010948918, 0.010561129],
                 "Mentese_A_L50_100Hz": [1,0.256703311,0.055076282,0.034403915,0.018318843,0.021344574,0.019765446,0.019498798,0.040958334],
                 "Mentese_A_L50_120Hz": [1,0.153751211,0.018287708,0.007321187,0.002788981,0.001786312,0.002780004,0.003641743,0.003027754],
                 "Mentese_A_L50_150Hz": [1,0.199180773,0.024066032,0.010615407,0.020209248,0.012429058,0.016505453,0.013667769,0.023004984],
                 "Milas_A_L50_30Hz": [1, 0.413679618, 0.205464915, 0.160147151, 0.116372801, 0.064602853, 0.035176691, 0.048881742, 0.048817597],
                 "Milas_A_L50_50Hz": [1,0.351551705,0.09298022,0.060349454,0.023088675,0.013079248,0.012517651,0.004125119,0.0139518],
                 "Milas_A_L50_60Hz": [1, 0.415158018, 0.213785318, 0.074861852, 0.022982681, 0.014427372, 0.006941767, 0.006300525, 0.004203442],
                 "Milas_A_L50_90Hz": [1, 0.162095767, 0.087821468, 0.042962695, 0.015386815, 0.009627105, 0.010522475, 0.010635336, 0.047319158],
                 "Milas_A_L50_100Hz": [1,0.250147092,0.035244991,0.030104926,0.011260746,0.016564247,0.022766646,0.03551466,0.236344916],
                 "Milas_A_L50_120Hz": [1,0.352666119,0.20950289,0.090622431,0.017558517,0.019431605,0.03513051,0.045317953,0.042110795],
                 "Milas_A_L50_150Hz": [1,0.707134107,0.060149125,0.067378514,0.01734751,0.025302863,0.037855987,0.108183729,0.146190959]}

d = [1,2.5,6,8.5,11,13.5,16,18.5,21]
d2 = arange(1,21.5,0.5)
for c in ["Milas"]:
    for f in [30,50,100,150]:
        generate_graph("{}_A_L50_{}Hz_Damping".format(c,f),[],"Normalize İvme","Mesafe(m)",d,
                    {"Acc": read_file("{}_A_{}Hz_D5".format(c, f)),"X": d2, "type": "line", "label": "Abaqus"},
                    {"Acc": field_results["{}_A_L50_{}Hz".format(c, f)],"X":d, "type": "scatter", "label": "Saha Verileri"})
