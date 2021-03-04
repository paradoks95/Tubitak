# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2020 replay file
# Internal Version: 2019_09_13-20.49.31 163176
# Run by NBF on Sat Feb 20 16:09:05 2021
#

# from driverUtils import executeOnCaeGraphicsStartup
# executeOnCaeGraphicsStartup()
#: Executing "onCaeGraphicsStartup()" in the site directory ...
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(1.11979, 1.12269), width=164.833, 
    height=111.37)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile('D:/Projeler/Tubitak/Kodlar/D3Inf.py', __main__.__dict__)
#* NameError: global name 'temp_layer_names' is not defined
#* File "D:/Projeler/Tubitak/Kodlar/D3Inf.py", line 486, in <module>
#*     model = Create_Model()
#* File "D:/Projeler/Tubitak/Kodlar/D3Inf.py", line 16, in __init__
#*     self.parameter = {"Name": temp_layer_names,
