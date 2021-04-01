from os.path import isfile
from time import sleep
import os
from threading import Thread
from datetime import datetime
from shutil import move
import sys
from numpy import float,arange,array
from pandas import read_excel

#TODO : Hata olan durumlarda sonraki analize geçme özelliği ekle
#TODO : 3D düşey mesh boyutunu düzenle
#TODO : Hız outputunu da al

class Monitor:
    def __init__(self,dimension,model_name,frequency,ditch_number,d2s,SP_pattern,RC,acc_pattern):
        soil_excel = read_excel("SoilProfile.xlsx",sheet_name="SoilParameters",header=None)
        model_parameters = read_excel("SoilProfile.xlsx",sheet_name="ModelParameters",header=None).iloc[:,1].values
        sheet_pile_parameters = read_excel("SoilProfile.xlsx",sheet_name="SheetPileParameters",header=None).iloc[:,1].values
        rubber_chips_parameters = read_excel("SoilProfile.xlsx",sheet_name="RubberChips",header=None).iloc[:,1].values
        self.initial_path = os.getcwd()
        self.Dimension = dimension

        self.damping_ratio = str(soil_excel.iloc[0,1])
        self.layer_names = str(soil_excel.loc[2:,0].values).replace(" ",",")
        self.elastic_modulus = str(soil_excel.loc[2:,1].values).replace(" ",",")
        self.poisson_ratio = str(soil_excel.loc[2:,2].values).replace(" ",",")
        self.density = str(soil_excel.loc[2:,3].values).replace(" ",",")
        self.thickness = str(soil_excel.loc[2:,4].values).replace(" ",",")
        self.VS = str(soil_excel.loc[2:,5].values).replace(" ",",")

        self.W = str(model_parameters[1])
        self.L = str(model_parameters[2])
        #self.ditch_number = model_parameters[3]
        self.ditch_number = ditch_number
        self.DL = model_parameters[4]
        self.DW = model_parameters[5]
        self.DH = model_parameters[6]
        #self.D2S = model_parameters[7]
        self.D2S = d2s
        self.D2D = model_parameters[8]
        #self.accelometer_pattern = str(model_parameters[9])
        self.accelometer_pattern = str(acc_pattern)
        self.source_size = model_parameters[10]
        self.PGA = model_parameters[11]
        #self.frequency = model_parameters[12]
        self.frequency = frequency
        self.time_step = model_parameters[13]
        self.duration = model_parameters[14]
        self.mesh_size = model_parameters[17]
        #self.model_name = model_parameters[0]
        self.model_name = model_name

        #self.SP_pattern = str(sheet_pile_parameters[0])
        self.SP_pattern = str(SP_pattern)
        self.SP_E = str(sheet_pile_parameters[1])
        self.SP_Thickness = str(sheet_pile_parameters[2])
        self.SP_Height = str(sheet_pile_parameters[3])
        self.SP_Interaction = str(sheet_pile_parameters[4])
        self.SP_Density = str(sheet_pile_parameters[5])

        #self.fillDitch = str(rubber_chips_parameters[0])
        self.fillDitch = str(RC)
        self.RC_E = str(rubber_chips_parameters[1])
        self.RC_density = str(rubber_chips_parameters[2])
        self.RC_damping = str(rubber_chips_parameters[3])
        self.RC_VS = str(rubber_chips_parameters[4])
        
        self.file_name = self.model_name + ".sta"

    def dampingCoefficients(self):
        alphaSheet = read_excel("SoilProfile.xlsx",sheet_name="a")
        betaSheet = read_excel("SoilProfile.xlsx",sheet_name="B")
        dampings = alphaSheet.iloc[:, 0]
        filter_ = dampings == int(float(self.damping_ratio)*100)
        alpha = alphaSheet[filter_][self.frequency].values[0]
        beta = betaSheet[filter_][self.frequency].values[0]
        return alpha,beta

    def path_creater(self):
        os.chdir("..")
        self.target_path = os.getcwd()
        for d in ["ODB","Output",os.path.join("Output",self.model_name)]:
            try:
                os.mkdir(d)
            except:
                continue
        os.chdir(self.initial_path)

    def modify_model(self):
        alpha,Beta = self.dampingCoefficients()
        if self.Dimension == "3D":
            file_name = "D3.py"
            old_path = os.path.join(self.initial_path,file_name)
            new_path = os.path.join(self.target_path,file_name)
            file_old = open(old_path)

            data = file_old.read().replace("temp_model_name",str(self.model_name))
            data = data.replace("temp_layer_names",str(self.layer_names))
            data = data.replace("temp_elastic",str(self.elastic_modulus))
            data = data.replace("temp_poisson",str(self.poisson_ratio))
            data = data.replace("temp_density",str(self.density))
            data = data.replace("temp_thickness",str(self.thickness))
            data = data.replace("temp_damping_ratio",str(self.damping_ratio))
            data = data.replace("temp_VS",str(self.VS))

            data = data.replace("temp_width",str(self.W))
            data = data.replace("temp_height",str(self.L))

            data = data.replace("temp_alpha",str(alpha))
            data = data.replace("temp_beta",str(Beta))

            data = data.replace("temp_ditch_width", str(self.DW))
            data = data.replace("temp_ditch2ditch", str(self.D2D))
            data = data.replace("temp_ditch2source", str(self.D2S))
            data = data.replace("temp_ditch_depth", str(self.DH))
            data = data.replace("temp_ditchnumber", str(self.ditch_number))
            data = data.replace("temp_ditch_length", str(self.DL))


            data = data.replace("temp_fill_ditch",str(self.fillDitch))
            data = data.replace("temp_RC_E",str(self.RC_E))
            data = data.replace("temp_RC_density",str(self.RC_density))
            data = data.replace("temp_RC_damping",str(self.RC_damping))
            data = data.replace("temp_RC_VS",str(self.RC_VS))

            data = data.replace("temp_SP_pattern",str(self.SP_pattern))
            data = data.replace("temp_SP_E",str(self.SP_E))
            data = data.replace("temp_SP_thickness",str(self.SP_Thickness))
            data = data.replace("temp_SP_height",str(self.SP_Height))
            data = data.replace("temp_SP_interaction",str(self.SP_Interaction))
            data = data.replace("temp_SP_density",str(self.SP_Density))

            data = data.replace("temp_source_size",str(self.source_size))
            data = data.replace("temp_accelerometer_pattern",str(self.accelometer_pattern))
            data = data.replace("temp_PGA",str(self.PGA))
            data = data.replace("temp_duration",str(self.duration))
            data = data.replace("temp_frequency",str(self.frequency))
            data = data.replace("temp_time_step",str(self.time_step))
            data = data.replace("temp_mesh_size",str(self.mesh_size))
            file_old.close()
        else:
            old_path = os.path.join(self.initial_path, "D2.py")
            new_path = os.path.join(self.target_path, "D2.py")
            file_old = open(old_path)
            data = file_old.read().replace("temp_model_name", str(self.model_name))
            data = data.replace("temp_layer_names", str(self.layer_names))
            data = data.replace("temp_elastic", str(self.elastic_modulus))
            data = data.replace("temp_poisson", str(self.poisson_ratio))
            data = data.replace("temp_density", str(self.density))
            data = data.replace("temp_thickness", str(self.thickness))
            data = data.replace("temp_damping_ratio", str(self.damping_ratio))
            data = data.replace("temp_VS", str(self.VS))

            data = data.replace("temp_alpha",str(alpha))
            data = data.replace("temp_beta",str(Beta))

            data = data.replace("temp_width", str(self.W))
            data = data.replace("temp_height", str(self.L))

            data = data.replace("temp_source_size", str(self.source_size/2))
            data = data.replace("temp_accelerometer_pattern", str(self.accelometer_pattern))
            data = data.replace("temp_PGA", str(self.PGA))
            data = data.replace("temp_duration", str(self.duration))
            data = data.replace("temp_frequency", str(self.frequency))
            data = data.replace("temp_time_step", str(self.time_step))

            data = data.replace("temp_ditch_width", str(self.DW))
            data = data.replace("temp_ditch2ditch", str(self.D2D))
            data = data.replace("temp_ditch2source", str(self.D2S))
            data = data.replace("temp_ditch_depth", str(self.DH))
            data = data.replace("temp_ditchnumber", str(self.ditch_number))

            data = data.replace("temp_fill_ditch",str(self.fillDitch))
            data = data.replace("temp_RC_E",str(self.RC_E))
            data = data.replace("temp_RC_density",str(self.RC_density))
            data = data.replace("temp_RC_damping",str(self.RC_damping))
            data = data.replace("temp_RC_VS",str(self.RC_VS))

            data = data.replace("temp_mesh_size",str(self.mesh_size))

            data = data.replace("temp_SP_pattern",str(self.SP_pattern))
            data = data.replace("temp_SP_E",str(self.SP_E))
            data = data.replace("temp_SP_thickness",str(self.SP_Thickness))
            data = data.replace("temp_SP_height",str(self.SP_Height))
            data = data.replace("temp_SP_interaction",str(self.SP_Interaction))
            data = data.replace("temp_SP_density",str(self.SP_Density))
            file_old.close()
        new_file = open(new_path,"w")
        new_file.write(data)
        new_file.close()

    def modify_output(self):
        old_path = os.path.join(self.initial_path,"Output.py")
        new_path = os.path.join(self.target_path,"Output.py")

        file_old = open(old_path)
        data = file_old.read().replace("temp_model_name",str(self.model_name))
        data = data.replace("temp_target_path",self.target_path)
        if self.Dimension == "3D":
            data = data.replace("temp_output","A3")
        else:
            data = data.replace("temp_output","A2")

        file_old.close()

        new_file = open(new_path,"w")
        new_file.write(data)
        new_file.close()

    def check(self):
        while isfile(self.file_name)==False:
            sleep(0.1)

    def progress_bar(self,count,total):
        self.check()
        percents = int(100.0 * count / float(total))
        t = datetime.now().strftime("%H:%M:%S")
        hashes = '#' * percents
        spaces = ' ' * (100 - percents)
        sys.stdout.write("\r {time} [{h}] {p}% ".format(time = t,h = (hashes + spaces), p = percents))
        sys.stdout.flush()

    def read(self):
        self.check()
        count = 0
        c1 = 0
        total = self.duration / self.time_step
        while count<=total:
            f = open(self.file_name)
            count = len(f.readlines()) - 5
            if c1 != count:
                self.progress_bar(count, total)
            c1 = count
            f.close()

    def start_job(self,model_name):
        os.chdir(self.target_path)
        os.system("abaqus job={m} input={m} ask_delete=OFF".format(m=model_name))

    def folder(self):
        for i in os.listdir():
            ex = i.split(".")[-1]
            if ex=="odb":
                if i in os.listdir("ODB"):
                    os.remove("ODB\\{}".format(i))
                move(i,"ODB")
            elif ex=="txt":
                if i in os.listdir("Output\\{}".format(self.model_name)):
                    os.remove("Output\\{}\\{}".format(self.model_name,i))
                move(i,os.path.join("Output",self.model_name))
            else:
                try:
                    os.remove(i)
                except:
                    pass

    def output(self):
        os.system("abaqus cae noGui={}".format(os.path.join(self.target_path,"Output.py")))
        self.folder()
        os.chdir(os.path.join(self.target_path,"Output",self.model_name))
        os.chdir(self.initial_path)

    def operator(self):
        self.path_creater()
        self.modify_model()
        self.modify_output()

        start_time = datetime.now().strftime("%H:%M:%S")
        print("Başlangıç Saati : ",start_time)
        os.chdir(self.target_path)
        if self.Dimension == "3D":
            os.system("abaqus cae noGui={}".format(os.path.join(self.target_path,"D3.py")))
        else:
            os.system("abaqus cae noGui={}".format(os.path.join(self.target_path, "D2.py")))

        print("Inp Oluşturulma Saati : ", str(datetime.now().strftime("%H:%M:%S")))
        self.start_job(self.model_name)
        reading=Thread(target=self.read)
        job = Thread(target=self.start_job, args=(self.model_name,))
        reading.start()
        job.start()
        reading.join()
        job.join()

location = "Mentese"
pc_number = int(input("PC_Number:"))

layout = ["L50","L25"][int(pc_number%2)]
frequency = [10*i for i in range(1,16)][int(pc_number/2)]
patterns = {
    "L50":[1,2.5,6,8.5,11,13.5,16,18.5,21,25,29],
    "L25":[1,2,3.5,6,8.5,11,13.5,16,18.5]
}

D2S = {
    "L50":7.25,
    "L25":4.75
}

exps = {
    "A" : [0,0,[]],
    #"OT" : [1,0,[]],
    #"RC" : [1,1,[]],
    #"SP" : [0,0,[D2S[layout]+0.75]],
    #"SP-OT" : [1,0,[D2S[layout]+0.75]],
    #"SP-RC" : [1,1,[D2S[layout]+0.75]],
    #"DT" : [2,0,[]],
}

for key in exps.keys():
    model_name = f"{location}_{key}_{layout}_{frequency}Hz"
    print(model_name)
    DN,RC,SP = exps[key]
    model = Monitor("2D",model_name,frequency,DN,D2S[layout],SP,RC,patterns[layout])
    model.path_creater()
    model.modify_model()
    #model.operator()
    #model.output()

