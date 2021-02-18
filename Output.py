from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset
from odbAccess import *
from os.path import isfile,join
from time import sleep


class Output:
    def __init__(self,model_name,target_path):
        self.model_name = model_name
        self.job_name = model_name
        self.target_path = target_path
    def check_file(self):
        file_name = self.job_name+".lck"
        while isfile(file_name)==True:
            sleep(0.1)

    def row2col(self,data):
        temp_time = []
        temp_acc = []

        for d in data:
            temp_time.append(round(d[0], 4))
            temp_acc.append(round(d[1], 10))

        if temp_time[-1]>temp_acc[-1]:
            return temp_time,temp_acc
        else:
            return temp_acc,temp_time

    def read_history_odb(self):
        sleep(5)
        self.check_file()
        file_name = self.job_name+".odb"
        odb=openOdb(path=join(self.target_path,file_name))
        step = odb.steps["Vibration Step"]
        self.output = {}
        accelometers = step.historyRegions.keys()
        accelometers.sort()
        for acc in accelometers:
            data = step.historyRegions[acc].historyOutputs["A2"].data
            time,accelerations = self.row2col(data)
            self.output["Time"]=time
            self.output[acc]=accelerations

    def wright_to_txt(self):
        self.read_history_odb()
        f = open(self.model_name+".txt","w")
        #first_row = ["Acc{}(m/s)           ".format(int(i)+1) for i in range(len(self.output.keys())-1)]

        keys = self.output.keys()
        del keys[keys.index("Time")]
        keys.sort()

        first_row = [i for i in keys]
        first_row.insert(0, "Time(s)             ")
        f.write("   ".join(first_row) + "\n")

        time = self.output["Time"]
        for i in range(len(time)):
            row_data = []
            row_data.append(str(time[i]) + " " * (25 - len(str(time[i]))))
            for key in keys:
                d = str(self.output[key][i])
                row_data.append(d + " "*(25-len(d)))
            f.write("".join(row_data) + "\n")
        f.close()

model_name = "temp_model_name"
target_path = "temp_target_path"
output = Output(model_name,target_path)
output.wright_to_txt()
