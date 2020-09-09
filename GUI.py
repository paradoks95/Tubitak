import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtCore import pyqtSlot,Qt
from Graphs import *
from PreProcess import *

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Tübitak'
        self.left = 0
        self.top = 0
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)
        
        self.show()
    
class MyTableWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabs.resize(1000,1000)   
        
        # Input Files Tab Layout
        self.file_tab = QWidget()
        self.tabs.addTab(self.file_tab,"Input Files")
        
        gridLayout = QGridLayout(self)
        self.pushButton = QPushButton("Records")
        self.pushButton.clicked.connect(self.openFileNameDialog)

        group = QGroupBox("Record Selection")
        vbox2 = QVBoxLayout()
        vbox2.setSpacing = 5
        vbox2.addWidget(self.pushButton)
        group.setLayout(vbox2)

        gridLayout.addWidget(group,0,0)
        self.file_tab.setLayout(gridLayout)
        # Scaling Tab Layout
        self.scale_tab = QWidget()
        self.tabs.addTab(self.scale_tab,"Scaling")
        self.scale_tab.layout = QGridLayout(self)
        self.scaleButton = QPushButton("Scale")
        self.scaleButton.clicked.connect(self.scaleFunction)
        self.scale_tab.layout.addWidget(self.scaleButton,0,0,1,8)

        #Unprocessed Data Tab Layout
        self.unprocessed_tab = QWidget()
        self.tabs.addTab(self.unprocessed_tab,"Unprocessed Data")
        self.unprocessed_tab.layout = QGridLayout(self)

        #Processed Data Tab Layout
        self.processed_tab = QWidget()
        self.tabs.addTab(self.processed_tab,"Processed Data")
        self.processed_tab.layout = QGridLayout(self)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.records = {"Acceleration":"","Velocity":""}
        self.distances = [1,3.5,6,8.5,11,13.5,16,18.5]
        self.scale_page_col= 0
        self.scale_page_inputs = {"Acceleration":{"Offsets":[],"Scales":[],"Boxes":[]},
                                    "Velocity":{"Offsets":[],"Scales":[],"Boxes":[]}}

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            modify_file(fileName)
            records = loadtxt(fileName,skiprows=8,unpack=True)
            self.records["Acceleration"]=records
            self.records["Velocity"]=records
            self.dt = read_dt(fileName)
            self.channelTable(len(records),"Acceleration")
            self.channelTable(len(records),"Velocity")
    
    def channelTable(self,channel_number,record_type):
        if record_type == "Acceleration":
            scale_factor = "0.5"
        else:
            scale_factor = "3.47"
        first_row = 1

        main_title = QLabel(record_type)
        self.scale_tab.layout.addWidget(main_title,first_row,self.scale_page_col,1,self.scale_page_col+3,alignment=Qt.AlignCenter)

        title1 = QLabel("Use Channel")
        self.scale_tab.layout.addWidget(title1,first_row+1,self.scale_page_col)

        title2 = QLabel("Offset")
        self.scale_tab.layout.addWidget(title2,first_row+1,self.scale_page_col+1)

        title3 = QLabel("Scale Factor")
        self.scale_tab.layout.addWidget(title3,first_row+1,self.scale_page_col+2)

        for i in range(channel_number):
            check_box = QCheckBox("Channel {}".format(i+1))
            self.scale_page_inputs[record_type]["Boxes"].append(check_box)
            self.scale_tab.layout.addWidget(check_box,first_row+2+i,self.scale_page_col)

            offset = QLineEdit(self)
            offset.setText("0")
            self.scale_tab.layout.addWidget(offset,first_row+2+i,self.scale_page_col+1)
            self.scale_page_inputs[record_type]["Offsets"].append(offset)

            scale = QLineEdit(self)
            scale.setText(scale_factor)
            self.scale_tab.layout.addWidget(scale,first_row+2+i,self.scale_page_col+2)
            self.scale_page_inputs[record_type]["Scales"].append(scale)

        copy_button = QPushButton("Copy Offset and Scale Factors")
        copy_button.clicked.connect(lambda:self.copyInput(record_type))
        self.scale_tab.layout.addWidget(copy_button,first_row+3+channel_number,self.scale_page_col,1,self.scale_page_col+2)

        self.scale_tab.setLayout(self.scale_tab.layout)
        self.scale_page_col = 4
    
    def copyInput(self,record_type):
        first_offset = self.scale_page_inputs[record_type]["Offsets"][0].text().replace(",",".")
        first_scale = self.scale_page_inputs[record_type]["Scales"][0].text().replace(",",".")
        for i in range(len(self.scale_page_inputs[record_type]["Offsets"])):
            self.scale_page_inputs[record_type]["Offsets"][i].setText(first_offset)
            self.scale_page_inputs[record_type]["Scales"][i].setText(first_scale)
    
    def scaleFunction(self):
        self.accelerations = []
        self.velocities = []
        for t in ["Acceleration","Velocity"]:
            inputs = self.scale_page_inputs[t]
            if t=="Acceleration":
                liste = self.accelerations
            else:
                liste = self.velocities
            for i in range(len(inputs["Offsets"])):
                checkbox = inputs["Boxes"][i]
                if checkbox.isChecked():
                    offset = float(inputs["Offsets"][i].text())
                    scale = float(inputs["Scales"][i].text())
                    f = lambda x: (x-offset)*scale
                    liste.append(f(self.records[t][i]))
        
        self.unprocessedTab()

    def addGraphTabs(self,i,process):
        graphTabs = QTabWidget()
        accTab = QWidget()
        accTab.layout = QVBoxLayout(self)
        label_image = QLabel(self)
        acc_graph = QPixmap(os.path.join("Graphs",process,"Channel {}".format(i+1),"AccelerationVsTime.png"))
        label_image.setPixmap(acc_graph)
        accTab.layout.addWidget(label_image)
        accTab.setLayout(accTab.layout)
        graphTabs.addTab(accTab,"Acceleration - Time")

        velTab = QWidget()
        velTab.layout = QGridLayout(self)
        label_image = QLabel(self)
        vel_graph = QPixmap(os.path.join("Graphs",process,"Channel {}".format(i+1),"VelocityVsTime.png"))
        label_image.setPixmap(vel_graph)
        velTab.layout.addWidget(label_image)
        velTab.setLayout(velTab.layout)
        graphTabs.addTab(velTab,"Velocity - Time")

        fourierTab = QWidget()
        fourierTab.layout = QGridLayout(self)
        label_image = QLabel(self)
        fourier_graph = QPixmap(os.path.join("Graphs",process,"Channel {}".format(i+1),"FourierSpectrum.png"))
        label_image.setPixmap(fourier_graph)
        fourierTab.layout.addWidget(label_image)
        fourierTab.setLayout(fourierTab.layout)
        graphTabs.addTab(fourierTab,"Fourier Spectrum")

        return graphTabs
    
    def processedTab(self):
        self.processedAccelerations = []
        self.processedVelocities = []
        self.processedTabs = QTabWidget()
        lowcut = float(self.lowcut_input.text().replace(",","."))
        highcut = float(self.highcut_input.text().replace(",","."))

        #Processed Graphs Tab
        processed_graphs_tab = QWidget()
        processed_graphs_tab.layout = QGridLayout(self)
        UGTab = QTabWidget()
        for i in range(len(self.accelerations)):
            acceleration = process(self.accelerations[i],self.dt,4,lowcut,highcut,True)
            velocity = process(self.velocities[i],self.dt,4,lowcut,highcut,True)
            acceleration_time(acceleration,velocity,self.dt,i+1,"Processed")
            velocity_time(acceleration,velocity,self.dt,i+1,"Processed")
            fourierSpectrum(acceleration,velocity,self.dt,i+1,"Processed")

            channel_tab = QWidget()
            channel_tab.layout = QGridLayout(self)
            graphTabs = self.addGraphTabs(i,"Processed")

            channel_tab.layout.addWidget(graphTabs)
            channel_tab.setLayout(channel_tab.layout)
            UGTab.addTab(channel_tab,"Channel {}".format(i+1))

            self.processedAccelerations.append(acceleration)
            self.processedVelocities.append(velocity)
        processed_graphs_tab.layout.addWidget(UGTab)  
        processed_graphs_tab.setLayout(processed_graphs_tab.layout)
        self.processedTabs.addTab(processed_graphs_tab,"Graphs")

        #Normalized Graph Tab
        NA_graph(self.processedAccelerations,self.processedAccelerations,self.distances)
        
        ng_page = QWidget()
        ng_page.layout = QGridLayout()
        label_image = QLabel(self)
        graph = QPixmap(os.path.join("Graphs","Processed","Normalized","Normalized.png"))
        label_image.setPixmap(graph)
        ng_page.layout.addWidget(label_image,0,0)
        ng_page.setLayout(ng_page.layout)

        self.processedTabs.addTab(ng_page,"Normalized Graph")
        self.processed_tab.layout.addWidget(self.processedTabs)
        self.processed_tab.setLayout(self.processed_tab.layout)
    
    def unprocessedTab(self):
        self.unprocessedTabs = QTabWidget()
        #Unprocessed Graphs Tab
        unprocessed_graphs_tab = QWidget()
        unprocessed_graphs_tab.layout = QGridLayout(self)
        UGTab = QTabWidget()    
        for i in range(len(self.accelerations)):
            acceleration = BaselineCorrection(self.accelerations[i],self.dt,4)
            velocity = BaselineCorrection(self.velocities[i],self.dt,4)
            acceleration_time(acceleration,velocity,self.dt,i+1,"Unprocessed")
            velocity_time(acceleration,velocity,self.dt,i+1,"Unprocessed")
            fourierSpectrum(acceleration,velocity,self.dt,i+1,"Unprocessed")
            
            channel_tab = QWidget()
            channel_tab.layout = QGridLayout(self)
            graphTabs = self.addGraphTabs(i,"Unprocessed")

            channel_tab.layout.addWidget(graphTabs)
            channel_tab.setLayout(channel_tab.layout)
            UGTab.addTab(channel_tab,"Channel {}".format(i+1))
        unprocessed_graphs_tab.layout.addWidget(UGTab)  
        unprocessed_graphs_tab.setLayout(unprocessed_graphs_tab.layout)
        self.unprocessedTabs.addTab(unprocessed_graphs_tab,"Graphs")

        #Data Process Tab
        data_process_tab = QWidget()
        data_process_tab.layout = QGridLayout(self)

        lowcut_label = QLabel("Lowcut : ")
        self.lowcut_input = QLineEdit()
        highcut_label = QLabel("Highcut : ")
        self.highcut_input = QLineEdit()
        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.processedTab)
        
        data_process_tab.layout.addWidget(lowcut_label,0,0)
        data_process_tab.layout.addWidget(highcut_label,1,0)
        data_process_tab.layout.addWidget(self.lowcut_input,0,1)
        data_process_tab.layout.addWidget(self.highcut_input,1,1)
        data_process_tab.layout.addWidget(self.filter_button,2,0,1,2)

        data_process_tab.setLayout(data_process_tab.layout)
        self.unprocessedTabs.addTab(data_process_tab,"Data Process")
        self.unprocessed_tab.layout.addWidget(self.unprocessedTabs)
        self.unprocessed_tab.setLayout(self.unprocessed_tab.layout)

        self.table = QTableWidget()
        self.table.setRowCount(8)
        self.table.setColumnCount(1)
        for i in range(8):
            self.table.setItem(i,0,QTableWidgetItem(""))

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
