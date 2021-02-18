from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset
import material
import sketch
import part
import section
import mesh
from odbAccess import *
from numpy import float,cumsum,array,abs,where,cos,arange,pi,zeros,unique,append,sin

class Create_Model:
    def __init__(self):
        self.parameter = {"Name": temp_layer_names,
                          "Elastic": temp_elastic,
                          "Poisson": temp_poisson,
                          "Density": temp_density,
                          "Permeability": temp_permeability,
                          "Void": temp_void_ratio,
                          "Thicknesses": temp_thickness,
                          "Damping Ratio": temp_damping_ratio,
                          "Vs": temp_VS}

        self.inf_size_x = 10
        self.inf_size_y = 10
        self.Width = 2*(float(temp_width)+self.inf_size_x)
        self.Height = float(sum(self.parameter["Thicknesses"]))+self.inf_size_y
        self.source_size = float(temp_source_size)*2
        self.accelometer_pattern = temp_accelerometer_pattern
        self.PGA = temp_PGA
        self.duration = temp_duration
        self.frequency = temp_frequency
        self.time_step = temp_time_step

        self.ditch_width = temp_ditch_width
        self.ditch_depth = temp_ditch_depth
        self.ditch2source = temp_ditch2source
        self.ditchnumber = temp_ditchnumber
        self.ditch2ditch = temp_ditch2ditch

        self.fillDitch = int(temp_fill_ditch)
        self.RC_E = temp_RC_E
        self.RC_density = temp_RC_density

        self.SP_pattern = array(temp_SP_pattern)+self.Width/2 + self.source_size/2
        self.SP_E = temp_SP_E
        self.SP_density = temp_SP_density
        self.SP_thickness = temp_SP_thickness
        self.SP_height = temp_SP_height
        self.SP_interaction = temp_SP_interaction

        self.Thicknesses = self.parameter["Thicknesses"]
        self.layer_heights = append([self.Height], self.Height - cumsum(self.parameter["Thicknesses"]))
        self.sorted_heights = array(sorted(self.layer_heights)[1:])

        self.model_size = sum(self.accelometer_pattern) + self.source_size
        self.model_name = "temp_model_name"

        self.mesh_size = temp_mesh_size
        self.f = lambda L, x: [L[i:i + 1] for i in x]
        session.viewports["Viewport: 1"].setValues(displayedObject=None)
        mdb.models.changeKey(fromName="Model-1", toName=self.model_name)
        self.soilModel = mdb.models[self.model_name]

        self.finite_mesh_type = "CPE4R"
        self.infinite_mesh_type = "CINPE4"
        self.temp_inf_type = "CPE4I"

    def create_part(self):
        soilProfileSketch = self.soilModel.ConstrainedSketch(name="__profile__", sheetSize=self.Width * 2)
        soilProfileSketch.rectangle(point1=(0, 0), point2=(self.Width, self.Height))
        self.soilPart = self.soilModel.Part(name="Soil Part", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
        self.soilPart.BaseShell(sketch=soilProfileSketch)
        self.soilPart.Set(faces=self.f(self.soilPart.faces,[0]),name="All Face")

        lelf_edge = self.soilPart.edges.findAt((0,1,0)).index
        right_edge = self.soilPart.edges.findAt((self.Width,1,0)).index
        bottom_edge = self.soilPart.edges.findAt((self.Width/2,0,0)).index
        self.soilPart.Set(edges=self.f(self.soilPart.edges,[lelf_edge,right_edge]),name="Vertical Boundary Edges")
        self.soilPart.Set(edges=self.f(self.soilPart.edges,[bottom_edge]),name="Bottom Edge")
        del self.soilModel.sketches['__profile__']

        self.soilModel.ConstrainedSketch(gridSpacing=3.53, name='__profile__', sheetSize=self.Width * 2,
                                         transform=self.soilPart.MakeSketchTransform(
                                             sketchPlane=self.soilPart.faces[0],
                                             sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0, 0, 0.0)))

        self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,
                                                  sketch=self.soilModel.sketches['__profile__'])
        self.soilModel.sketches['__profile__'].rectangle(point1=(self.inf_size_x, self.Height),
                                                         point2=(self.Width - self.inf_size_x, self.inf_size_y))
        self.soilModel.sketches['__profile__'].Line(point1=(self.inf_size_x, self.inf_size_y),
                                                    point2=(0, 0))
        self.soilModel.sketches['__profile__'].Line(point1=(self.Width - self.inf_size_x, self.inf_size_y),
                                                    point2=(self.Width, 0))
        self.soilModel.sketches['__profile__'].Line(
            point1=(self.Width - self.inf_size_x - self.mesh_size, self.inf_size_y),
            point2=(self.Width - self.inf_size_x - self.mesh_size, 0))
        self.soilModel.sketches['__profile__'].Line(
            point1=(self.inf_size_x + self.mesh_size, self.inf_size_y),
            point2=(self.inf_size_x + self.mesh_size, 0))
        self.soilModel.sketches['__profile__'].Line(
            point1=(self.Width - self.inf_size_x, self.inf_size_y + self.mesh_size),
            point2=(self.Width, self.inf_size_y + self.mesh_size))
        self.soilModel.sketches['__profile__'].Line(
            point1=(0, self.inf_size_y + self.mesh_size),
            point2=(self.inf_size_x, self.inf_size_y + self.mesh_size))
        self.soilPart.PartitionFaceBySketch(faces=self.soilPart.faces[0],
                                            sketch=self.soilModel.sketches['__profile__'])
        del self.soilModel.sketches['__profile__']

    def create_sheet_pile(self):
        self.soilMaterial = self.soilModel.Material("Steel")
        self.soilMaterial.Density(table=((self.SP_density,),))
        self.soilMaterial.Elastic(table=((self.SP_E,0.33),))
        self.soilModel.HomogeneousSolidSection(name="Sheet Pile Section", material="Steel")

        for i in range(len(self.SP_pattern)):
            #Draw Sheet Pile
            SPProfileSketch = self.soilModel.ConstrainedSketch(name="__profile__", sheetSize=self.Width * 2)
            SPProfileSketch.rectangle(point1=(0, 0), point2=(self.SP_thickness, self.SP_height))
            SPPart = self.soilModel.Part(name="Sheet Pile_{}".format(i+1), dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
            SPPart.BaseShell(sketch=SPProfileSketch)
            SPPart.Set(faces=self.f(SPPart.faces, [0]), name="Sheet Pile_{}".format(i+1))
            SPPart.SectionAssignment(region=(SPPart.faces,),sectionName="Sheet Pile Section")
            del self.soilModel.sketches['__profile__']

            #Cut Soil
            face = self.soilPart.faces.findAt((self.Width/2, self.Height - 0.01, 0))
            self.soilModel.ConstrainedSketch(gridSpacing=3.53, name='__profile__', sheetSize=self.Width,
                                             transform=self.soilPart.MakeSketchTransform(sketchPlane=face,
                                                                                         sketchPlaneSide=SIDE1,
                                                                                         sketchOrientation=RIGHT,
                                                                                         origin=(0, 0, 0.0)))

            self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,
                                                      sketch=self.soilModel.sketches['__profile__'])
            self.soilModel.sketches['__profile__'].rectangle(point1=(self.SP_pattern[i], self.Height),
                                                             point2=(self.SP_pattern[i] + self.SP_thickness,
                                                                     self.Height - self.SP_height))
            self.soilPart.Cut(sketch=self.soilModel.sketches['__profile__'])
            del self.soilModel.sketches['__profile__']

            #Create Soil Surface
            edge1 = self.soilPart.edges.findAt((self.SP_pattern[i],self.Height-0.01,0)).index
            edge2 = self.soilPart.edges.findAt((self.SP_pattern[i]+self.SP_thickness,self.Height-0.01,0)).index
            edge3 = self.soilPart.edges.findAt((self.SP_pattern[i]+self.SP_thickness/2,self.Height-self.SP_height,0)).index
            self.soilPart.Surface(name='Soil Surface_{}'.format(i+1),side1Edges=self.f(self.soilPart.edges,[edge1,edge2,edge3]))

            #Create Instance
            self.create_instance("Sheet Pile-{}".format(i+1),SPPart)

            # Translate Pile
            self.soilModel.rootAssembly.translate(instanceList=('Sheet Pile-{}'.format(i + 1),),
                                                  vector=(self.SP_pattern[i], self.Height - self.SP_height, 0.0))
            # Create Sheet Pile Surface
            edge1 = SPPart.edges.findAt((0, self.SP_height/2, 0)).index
            edge2 = SPPart.edges.findAt((self.SP_thickness, self.SP_height/2, 0)).index
            edge3 = SPPart.edges.findAt((self.SP_thickness / 2, 0, 0)).index
            SPPart.Surface(name='Pile Surface_{}'.format(i + 1), side1Edges=self.f(SPPart.edges, [edge1, edge2, edge3]))

            #Interaction
            self.soilModel.ContactProperty('IntProp-1')
            self.soilModel.interactionProperties['IntProp-1'].TangentialBehavior(formulation=ROUGH)
            self.soilModel.SurfaceToSurfaceContactStd(adjustMethod=NONE,
                clearanceRegion=None, createStepName='Initial', datumAxis=None,
                initialClearance=OMIT, interactionProperty='IntProp-1', master=
                self.soilModel.rootAssembly.instances['Soil Part-1'].surfaces['Soil Surface_{}'.format(i+1)], name='Int-1',
              slave=self.soilModel.rootAssembly.instances['Sheet Pile-{}'.format(i+1)].surfaces['Pile Surface_{}'.format(i+1)]
                , sliding=FINITE, thickness=ON)

    def create_ditch(self):
        if self.ditchnumber > 0:
            top_face = self.soilPart.faces.findAt((self.Width/2, self.Height - 0.01, 0))
            for i in range(self.ditchnumber):
                x = self.Width/2 +self.source_size/2 + self.ditch2source + i*(self.ditch_width + self.ditch2ditch)
                self.soilModel.ConstrainedSketch(gridSpacing=3.53, name='__profile__', sheetSize=self.Width,
                                                 transform=self.soilPart.MakeSketchTransform(sketchPlane=top_face,
                                                                                             sketchPlaneSide=SIDE1,
                                                                                             sketchOrientation=RIGHT,
                                                                                             origin=(0, 0, 0.0)))

                self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,sketch=self.soilModel.sketches['__profile__'])
                self.soilModel.sketches['__profile__'].rectangle(point1=(x, self.Height),
                                                            point2=(x + self.ditch_width, self.Height - self.ditch_depth))
                self.soilPart.Cut(sketch=self.soilModel.sketches['__profile__'])
                del self.soilModel.sketches['__profile__']

            try:
                for x in [self.inf_size_x+0.01]+list(self.SP_pattern+self.SP_thickness+0.01):
                    face = self.soilPart.faces.findAt((x, self.Height - self.ditch_depth, 0))
                    self.soilModel.ConstrainedSketch(gridSpacing=3.53, name='__profile__', sheetSize=self.Width,
                                                     transform=self.soilPart.MakeSketchTransform(sketchPlane=face,
                                                                                                 sketchPlaneSide=SIDE1,
                                                                                                 sketchOrientation=RIGHT,
                                                                                                 origin=(0, 0, 0.0)))
                    self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,sketch=self.soilModel.sketches['__profile__'])
                    self.soilModel.sketches['__profile__'].Line(point1=(0, self.Height - self.ditch_depth),
                                                                     point2=(self.Width,self.Height - self.ditch_depth))
                    self.soilPart.PartitionFaceBySketch(faces=face, sketch=self.soilModel.sketches['__profile__'])
                    del self.soilModel.sketches['__profile__']
            except:
                pass

    def create_rubber_barrier(self):
        if self.fillDitch and self.ditchnumber:   
            self.soilMaterial = self.soilModel.Material("Rubber")
            self.soilMaterial.Density(table=((self.RC_density,),))
            self.soilMaterial.Elastic(table=((self.RC_E,0.33),))
            self.soilModel.HomogeneousSolidSection(name="Rubber Chips Section", material="Rubber")

            for i in range(self.ditchnumber):
                x = self.Width/2 +self.source_size/2 + self.ditch2source + i*(self.ditch_width + self.ditch2ditch)
                print(x)
                #Draw Rubber Chip
                RCProfileSketch = self.soilModel.ConstrainedSketch(name="__profile__", sheetSize=self.Width * 2)
                RCProfileSketch.rectangle(point1=(0, 0), point2=(self.ditch_width, self.ditch_depth))
                RCPart = self.soilModel.Part(name="Rubber Chips_{}".format(i+1), dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
                RCPart.BaseShell(sketch=RCProfileSketch)
                RCPart.Set(faces=self.f(RCPart.faces, [0]), name="Rubber Chips_{}".format(i+1))
                RCPart.SectionAssignment(region=(RCPart.faces,),sectionName="Rubber Chips Section")
                del self.soilModel.sketches['__profile__']

                #Create Soil Surface
                edge1 = self.soilPart.edges.findAt((x,self.Height-0.01,0)).index
                edge2 = self.soilPart.edges.findAt((x+self.ditch_width,self.Height-0.01,0)).index
                edge3 = self.soilPart.edges.findAt((x+self.ditch_width/2,self.Height-self.ditch_depth,0)).index
                self.soilPart.Surface(name='Trench Surface_{}'.format(i+1),side1Edges=self.f(self.soilPart.edges,[edge1,edge2,edge3]))

                #Create Instance
                self.create_instance("Rubber Chips-{}".format(i+1),RCPart)

                # Translate Pile
                self.soilModel.rootAssembly.translate(instanceList=('Rubber Chips-{}'.format(i + 1),),
                                                    vector=(x, self.Height - self.ditch_depth, 0.0))
                # Create Rubber Chips Surface
                edge1 = RCPart.edges.findAt((0, self.ditch_depth/2, 0)).index
                edge2 = RCPart.edges.findAt((x, self.ditch_depth/2, 0)).index
                edge3 = RCPart.edges.findAt((x / 2, 0, 0)).index
                RCPart.Surface(name='RC Surface_{}'.format(i + 1), side1Edges=self.f(SPPart.edges, [edge1, edge2, edge3]))

                #Interaction
                self.soilModel.ContactProperty('IntProp-2')
                self.soilModel.interactionProperties['IntProp-2'].TangentialBehavior(formulation=ROUGH)
                self.soilModel.SurfaceToSurfaceContactStd(adjustMethod=NONE,
                    clearanceRegion=None, createStepName='Initial', datumAxis=None,
                    initialClearance=OMIT, interactionProperty='IntProp-2', master=
                    self.soilModel.rootAssembly.instances['Soil Part-1'].surfaces['Trench Surface_{}'.format(i+1)], name='Int-1',
                     slave=self.soilModel.rootAssembly.instances['Rubber Chips-{}'.format(i+1)].surfaces['RC Surface_{}'.format(i+1)]
                    , sliding=FINITE, thickness=ON)
            
    
    def sketch_face(self, y, left_x):
        face = self.soilPart.faces.findAt((0.01 + left_x, y - 0.01, 0))
        self.soilModel.ConstrainedSketch(gridSpacing=3.53, name='__profile__', sheetSize=self.Width,
                                         transform=self.soilPart.MakeSketchTransform(sketchPlane=face,
                                                                                     sketchPlaneSide=SIDE1,
                                                                                     sketchOrientation=RIGHT,
                                                                                     origin=(0, 0, 0.0)))

        self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,
                                                  sketch=self.soilModel.sketches['__profile__'])
        self.soilModel.sketches['__profile__'].Line(point1=(0 + left_x, y),
                                                    point2=(self.Width - self.inf_size_x + left_x, y))
        self.soilPart.PartitionFaceBySketch(faces=face, sketch=self.soilModel.sketches['__profile__'])
        del self.soilModel.sketches['__profile__']

    def partition_part(self, thickness):
        offset = self.Height - thickness
        if offset > self.inf_size_y:
            self.sketch_face(offset, 0)
            self.sketch_face(offset, self.Width - self.inf_size_x)
            self.sketch_face(offset, self.inf_size_x)

    def create_material(self, name, properties):
        elastic = properties["E"]
        density = properties["D"]

        damping = properties.get("Damping", 0)
        H = properties.get("H", 0.005)
        Vs = properties.get("Vs", 0)
        alpha, beta = self.rayleigh_damping([1, 4], Vs, H, damping)
        self.soilMaterial = self.soilModel.Material(name)
        self.soilMaterial.Density(table=((density,),))
        self.soilMaterial.Elastic(table=(elastic,))
        self.soilMaterial.Damping(alpha=alpha, beta=beta)

    def create_section(self):
        bottom_face = self.soilPart.faces[self.soilPart.faces.findAt((self.Width/2, 0.01, 0)).index]
        bottom_right_face = self.soilPart.faces[self.soilPart.faces.findAt((self.Width - 0.01, 0, 0)).index]
        bottom_left_face = self.soilPart.faces[self.soilPart.faces.findAt((0.01, 0, 0)).index]

        right_bottom_face = self.soilPart.faces[self.soilPart.faces.findAt((self.Width - 0.01, self.inf_size_y - 0.01, 0)).index]
        left_bottom_face = self.soilPart.faces[self.soilPart.faces.findAt((0.01, self.inf_size_y - 0.01, 0)).index]
        last_inf_face_left = self.soilPart.faces[self.soilPart.faces.findAt((0.01, self.inf_size_y+0.01, 0)).index]
        last_inf_face_middle = self.soilPart.faces[self.soilPart.faces.findAt((self.Width/2, self.inf_size_y+0.01, 0)).index]
        last_inf_face_right = self.soilPart.faces[self.soilPart.faces.findAt((self.Width - 0.01, self.inf_size_y+self.mesh_size+0.01, 0)).index]

        self.soilModel.HomogeneousSolidSection(name="Infinite_Section", material=self.parameter["Name"][-1])
        self.soilPart.SectionAssignment(region=(bottom_face, bottom_right_face,bottom_left_face,left_bottom_face,last_inf_face_middle, right_bottom_face,last_inf_face_left,last_inf_face_right),sectionName="Infinite_Section")

        for i in range(len(self.layer_heights) - 1):
            y = float(self.layer_heights[i]) - 0.01
            name = self.parameter["Name"][i]

            index1 = self.soilPart.faces.findAt((0.01, y, 0)).index
            index2 = self.soilPart.faces.findAt((self.Width - 0.01, y, 0)).index
            index3 = self.soilPart.faces.findAt((self.inf_size_x+0.01, y, 0)).index
            section_name = name + "_Section"

            self.soilModel.HomogeneousSolidSection(name=section_name, material=name)
            self.soilPart.SectionAssignment(region=(self.soilPart.faces[index1], self.soilPart.faces[index2],self.soilPart.faces[index3]),
                                            sectionName=section_name)
            index_list = [index1]
            for x in self.SP_pattern:
                index = self.soilPart.faces.findAt((x+self.SP_thickness+0.01,y,0)).index
                self.soilPart.SectionAssignment(region=(self.soilPart.faces[index], ),sectionName=section_name)
                index_list.append(index)
            self.soilPart.Set(faces=self.f(self.soilPart.faces, index_list), name=name + "_Face")

        if len(self.SP_pattern)>0:
            try:
                face = self.soilPart.faces.findAt((self.Width/2, self.Height - self.SP_height, 0))
                self.soilModel.ConstrainedSketch(gridSpacing=3.53, name='__profile__', sheetSize=self.Width,
                                                 transform=self.soilPart.MakeSketchTransform(sketchPlane=face,
                                                                                             sketchPlaneSide=SIDE1,
                                                                                             sketchOrientation=RIGHT,
                                                                                             origin=(0, 0, 0.0)))
                self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,
                                                          sketch=self.soilModel.sketches['__profile__'])
                self.soilModel.sketches['__profile__'].Line(point1=(0, self.Height - self.SP_height),
                                                            point2=(self.Width, self.Height - self.SP_height))
                self.soilPart.PartitionFaceBySketch(faces=face, sketch=self.soilModel.sketches['__profile__'])
                del self.soilModel.sketches['__profile__']
            except:
                pass

    def create_face_sets(self):
        finite_faces = self.soilPart.faces.getByBoundingBox(self.inf_size_x, self.inf_size_y, 0, self.Width - self.inf_size_x,
                                                            self.Height, 0)
        self.soilPart.Set(faces=finite_faces, name="Finite_Faces")

        inf_face1 = self.soilPart.faces.findAt((self.inf_size_x/2, 0.01, 0)).index
        inf_face2 = self.soilPart.faces.findAt((0.01, self.inf_size_y/2, 0)).index
        inf_face3 = self.soilPart.faces.findAt((self.Width - self.inf_size_x + 0.01, 0.01, 0)).index
        inf_face4 = self.soilPart.faces.findAt((self.Width - 0.01, self.inf_size_y / 2, 0)).index
        inf_face5 = self.soilPart.faces.findAt((self.Width/2, self.inf_size_y / 2, 0)).index
        infinite_faces = [inf_face1, inf_face2, inf_face3,inf_face4,inf_face5]
        for i in range(len(self.layer_heights)):
            y = float(self.layer_heights[i] - 0.01)
            infinite_faces.append(self.soilPart.faces.findAt((self.Width - 0.01, y, 0)).index)
            infinite_faces.append(self.soilPart.faces.findAt((0.01, y, 0)).index)
        self.soilPart.Set(faces=self.f(self.soilPart.faces, infinite_faces), name="Infinite_Faces")

    def create_edge_set(self):
        left_finite_edges = []
        finite_horizontal_edges = []
        vertical_edges = []
        single_seed_edges = []
        single_seed_coordinates = [(0, 0.01, 0),(self.inf_size_x/2,self.Height,0),(0.01,self.inf_size_y+self.mesh_size,0),
                                   (self.inf_size_x+self.mesh_size,0.01,0),(0.01,0,0),(self.inf_size_x/2,self.inf_size_y/2,0),
                                   (self.Width - self.inf_size_x - self.mesh_size, 0.01, 0),
                                   (self.Width - 0.01, self.Height, 0),
                                   (self.Width - 0.01, self.inf_size_y + self.mesh_size, 0),
                                   (self.Width - 0.01, 0, 0), (self.Width, 0.01, 0),
                                   ((self.Width - self.inf_size_x / 2), self.inf_size_y / 2, 0)]
        for i in single_seed_coordinates:
            single_seed_edges.append(self.soilPart.edges.findAt(i).index)

        y_coordinates = list(self.layer_heights)+[0]
        try:
            edge = self.soilPart.edges.findAt((self.inf_size_x + 0.01,self.Height-self.SP_height,0)).index
            finite_horizontal_edges.append(edge)
            for x in self.SP_pattern:
                edge = self.soilPart.edges.findAt((x+self.SP_thickness+0.01,self.Height-self.SP_height,0)).index
                finite_horizontal_edges.append(edge)
        except:
            pass
        for i in range(len(y_coordinates)):
            y = y_coordinates[i]
            finite_edge_id = self.soilPart.edges.findAt((self.Width/2, y, 0)).index
            finite_horizontal_edges.append(finite_edge_id)
            for x in self.SP_pattern:
                finite_edge_id = self.soilPart.edges.findAt((x + self.SP_thickness + 0.001, y, 0)).index
                finite_horizontal_edges.append(finite_edge_id)

        for y in arange(self.Height-0.01,self.inf_size_y + self.mesh_size,-0.1):
            # Vertical Edges
            N1 = (0, y, 0)
            N2 = (self.Width - self.inf_size_x, y, 0)
            N3 = (self.Width, y, 0)
            N4 = (self.inf_size_x, y, 0)
            try:
                id1 = self.soilPart.edges.findAt(N1).index
                id2 = self.soilPart.edges.findAt(N2).index
                id3 = self.soilPart.edges.findAt(N3).index
                id4 = self.soilPart.edges.findAt(N4).index

                left_finite_edges.append(id1)
                vertical_edges.append(id1)
                vertical_edges.append(id2)
                vertical_edges.append(id3)
                vertical_edges.append(id4)
            except:
                pass

        self.soilPart.Set(edges=self.f(self.soilPart.edges, vertical_edges), name="All_Vertical_Edges")
        self.soilPart.Set(edges=self.f(self.soilPart.edges, finite_horizontal_edges),
                          name="Finite_Horizontal_Edges")
        self.soilPart.Set(edges=self.f(self.soilPart.edges, single_seed_edges), name="Single_Seed_Edges")

    def draw_source(self):
        N1 = (self.Width/2 - self.source_size/2, self.Height, 0)
        N2 = (self.Width/2 + self.source_size/2, self.Height, 0)

        self.soilPart.DatumPointByCoordinate(N1)
        self.soilPart.DatumPointByCoordinate(N2)

        top_part = self.soilPart.faces.findAt((self.inf_size_x + 0.01, self.Height, 0))
        self.soilPart.PartitionFaceByShortestPath(faces=top_part, point1=N1, point2=N2)
        id1 = self.soilPart.edges.findAt((self.Width/2, self.Height, 0)).index
        self.soilPart.Set(edges=self.f(self.soilPart.edges, [id1]), name="Source")

    def create_instance(self,name,part):
        self.soilModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
        self.soilModel.rootAssembly.Instance(dependent=ON, name=name, part=part)
        self.soilModel.rootAssembly.regenerate()

    def rayleigh_damping(self, modes, Vs, H, damping_ratio):
        wn = lambda mode, Vs, H: (2 * mode - 1) * Vs / (4 * H)
        try:
            wi = wn(modes[0], Vs, H)
            wj = wn(modes[1], Vs, H)
            alpha = damping_ratio * 2 * wi * wj / (wi + wj)
            beta = damping_ratio * 2 / (wi + wj)
        except:
            alpha, beta = 0, 0

        return alpha, beta

    def create_vibration(self):
        time = arange(0, self.duration + self.time_step, self.time_step)
        accelerations = self.PGA * sin(2 * pi * self.frequency * time)
        self.data = [[time[i], accelerations[i]] for i in range(len(time))]

    def create_step(self):
        self.create_vibration()
        self.soilModel.ImplicitDynamicsStep(initialInc=self.time_step, timePeriod=self.duration,
                                            maxNumInc=int(2 * (self.duration / self.time_step)),
                                            name='Vibration Step',
                                            previous='Initial', maxInc=self.time_step)
        self.soilModel.TabularAmplitude(name="Vibration", timeSpan=STEP, smooth=SOLVER_DEFAULT, data=self.data)

    def create_boundary_conditions(self):
        Sets = self.soilModel.rootAssembly.instances["Soil Part-1"].sets
        self.soilModel.DisplacementBC(amplitude="Vibration", createStepName='Vibration Step', name='Vibration',region=Sets['Source'], u2=-0.01)
        self.soilModel.DisplacementBC(createStepName='Initial', name='BC-X',region=Sets['Vertical Boundary Edges'], u1=0)
        self.soilModel.DisplacementBC(createStepName='Initial', name='BC-Y',region=Sets['Bottom Edge'], u2=0,u1=0)

    def bisection(self, Vs, u):
        x1 = float(Vs / 2)
        x2 = float(Vs)
        c = float((x1 + x2) / 2)
        a = float(((1 - 2 * u) / (2 - 2 * u)) ** 0.5)
        f = lambda VR: (VR / Vs) ** 6 - 8 * (VR / Vs) ** 4 - (16 * a ** 2 - 24) * (VR / Vs) ** 2 - 16 * (1 - a ** 2)

        while abs(f(c)) > 0.01:
            if f(c) > 0:
                x2 = c
            else:
                x1 = c
            c = (x1 + x2) / 2

        return c

    def constrained_sketch(self,name,face):
        self.soilModel.ConstrainedSketch(gridSpacing=3.53, name=name, sheetSize=self.Width,
                                         transform=self.soilPart.MakeSketchTransform(sketchPlane=face,
                                                                                     sketchPlaneSide=SIDE1,
                                                                                     sketchOrientation=RIGHT,
                                                                                     origin=(0, 0, 0.0)))

        self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES, sketch=self.soilModel.sketches[name])
    
    def divide_model(self):
        for y in list(self.layer_heights) + [self.Height - self.SP_height,self.Height - self.ditch_depth]:
            face = self.soilPart.faces.findAt((self.Width/2,y-0.1,0))

            if len(self.SP_pattern) > 0:
                self.constrained_sketch("__profile1__", face)
                self.soilModel.sketches['__profile1__'].Line(point1=(self.Width / 2, y), point2=(self.Width / 2, 0))
                for i in self.SP_pattern:
                    diff = self.mesh_size - self.SP_thickness
                    x1 = i - diff / 2
                    self.soilModel.sketches['__profile1__'].Line(point1=(x1, y), point2=(x1, 0))
                    self.soilPart.PartitionFaceBySketch(faces=face, sketch=self.soilModel.sketches['__profile1__'])
                del self.soilModel.sketches['__profile1__']

            if len(self.SP_pattern) > 0:
                self.constrained_sketch("__profile1__", face)
                self.soilModel.sketches['__profile1__'].Line(point1=(self.Width / 2, y), point2=(self.Width / 2, 0))
                for i in self.SP_pattern:
                    face2 = self.soilPart.faces.findAt((i+self.SP_thickness+0.1, y - 0.1, 0))
                    self.constrained_sketch("__profile2__", face2)
                    diff = self.mesh_size - self.SP_thickness
                    x2 = i + self.SP_thickness + diff / 2
                    self.soilModel.sketches['__profile2__'].Line(point1=(x2, y), point2=(x2, 0))
                    self.soilPart.PartitionFaceBySketch(faces=face2, sketch=self.soilModel.sketches['__profile2__'])
                del self.soilModel.sketches['__profile2__']

    def set_mesh_control(self):
        face1 = self.soilPart.faces.findAt((self.Width - 1, 0.01,0))
        face2 = self.soilPart.faces.findAt((self.Width - 1, self.inf_size_y/2,0))
        face3 = self.soilPart.faces.findAt((0.01, self.inf_size_y/2,0))
        face4 = self.soilPart.faces.findAt((self.inf_size_x/2, 0.01,0))
        face5 = self.soilPart.faces.findAt((self.Width/2-0.1, 0.01,0))
        face6 = self.soilPart.faces.findAt((self.Width/2+0.1, 0.01,0))
        edge = self.soilPart.edges.findAt((self.Width/2,self.inf_size_y/2,0))
        diagonal_edge1 = self.soilPart.edges.findAt((self.Width - self.inf_size_x/2,self.inf_size_y/2,0))
        diagonal_edge2 = self.soilPart.edges.findAt((self.inf_size_x/2,self.inf_size_y/2,0))
        self.soilPart.setSweepPath(edge=diagonal_edge1, region=face1, sense=FORWARD)
        self.soilPart.setSweepPath(edge=diagonal_edge2, region=face3, sense=FORWARD)
        self.soilPart.setSweepPath(edge=diagonal_edge1, region=face2, sense=FORWARD)
        self.soilPart.setSweepPath(edge=diagonal_edge2, region=face4, sense=FORWARD)
        self.soilPart.setSweepPath(edge=edge, region=face5, sense=FORWARD)
        self.soilPart.setSweepPath(edge=edge, region=face6, sense=FORWARD)
        self.soilPart.setMeshControls(regions=self.soilPart.sets["Infinite_Faces"].faces, technique=SWEEP)
        self.soilPart.setMeshControls(regions=self.soilPart.sets["Finite_Faces"].faces, technique=SWEEP)

        for y in self.layer_heights[:-1]:
            face1 = self.soilPart.faces.findAt((self.Width - 0.01,y-0.01,0))
            face2 = self.soilPart.faces.findAt((0.01,y-0.01,0))
            face3 = self.soilPart.faces.findAt((self.Width/2-0.1,y-0.01,0))
            face4 = self.soilPart.faces.findAt((self.Width/2+0.1,y-0.01,0))

            edge1 = self.soilPart.edges.findAt((self.Width-0.01,y,0))
            edge2 = self.soilPart.edges.findAt((0.01,y,0))
            edge3 = self.soilPart.edges.findAt((self.Width/2-1,y,0))
            edge4 = self.soilPart.edges.findAt((self.Width/2+1,y,0))

            self.soilPart.setSweepPath(edge=edge1, region=face1, sense=FORWARD)
            self.soilPart.setSweepPath(edge=edge2, region=face2, sense=REVERSE)
            self.soilPart.setSweepPath(edge=edge3, region=face3, sense=REVERSE)
            self.soilPart.setSweepPath(edge=edge4, region=face4, sense=FORWARD)

    def create_mesh(self):
        self.set_mesh_control()
        self.soilPart.setElementType(regions=(self.soilPart.sets["Infinite_Faces"]),elemTypes=(
        mesh.ElemType(elemCode=CPE4I, elemLibrary=STANDARD), mesh.ElemType(elemCode=CPE4I, elemLibrary=STANDARD)))
        self.soilPart.setElementType(regions=(self.soilPart.sets["Finite_Faces"]), elemTypes=(
            mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD), mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD)))
        self.soilPart.seedEdgeBySize(edges=self.soilPart.sets["All_Vertical_Edges"].edges, size=self.mesh_size,
                                     constraint=FIXED)
        self.soilPart.seedEdgeBySize(edges=self.soilPart.sets["Finite_Horizontal_Edges"].edges, size=self.mesh_size,
                                     )
        self.soilPart.seedEdgeBySize(edges=(self.soilPart.edges.findAt((0.01, 0, 0)),), size=self.mesh_size)
        self.soilPart.seedEdgeByNumber(edges=self.soilPart.sets["Single_Seed_Edges"].edges, number=1,
                                       constraint=FIXED)
        for i in range(len(self.SP_pattern)):
            part = self.soilModel.parts["Sheet Pile_{}".format(i+1)]
            part.setElementType(regions=(part.sets["Sheet Pile_{}".format(i+1)]),
                                         elemTypes=(mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD),
                                         mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD)))
            part.seedPart(size = self.mesh_size)
            part.generateMesh()

            self.soilPart.seedEdgeBySize(edges=(self.soilPart.edges.findAt((self.SP_pattern[i]+self.SP_thickness/2, 0, 0)),), size=self.SP_thickness*2)

        self.soilPart.generateMesh()

    def create_nodes(self):
        self.node_list = []
        x2 = self.Width/2+ 0.5*self.source_size + cumsum(array(self.accelometer_pattern))
        for i in x2:
            self.node_list.append(self.soilPart.nodes.getClosest((i, self.Height, 0)))
            self.node_list.append(self.soilPart.nodes.getClosest((i, self.Height, 0)))

        self.soilPart.Set(nodes=mesh.MeshNodeArray(self.node_list), name="Accelometers")

    def create_history_output(self):
        self.soilModel.fieldOutputRequests["F-Output-1"].deactivate("Vibration Step")
        self.soilModel.HistoryOutputRequest(createStepName="Vibration Step", frequency=1, name="H-Output-2",
                                            variables=('A2',),
                                            region=self.soilModel.rootAssembly.allInstances['Soil Part-1'].sets[
                                                'Accelometers'])

        del self.soilModel.historyOutputRequests['H-Output-1']
        del self.soilModel.fieldOutputRequests['F-Output-1']

    def create_job(self):
        self.job_name = self.model_name
        mdb.Job(model=self.model_name, name=self.job_name, type=ANALYSIS, memory=90, memoryUnits=PERCENTAGE,
                numCpus=6, numDomains=6, numGPUs=1)
        mdb.jobs[self.model_name].writeInput(consistencyChecking=OFF)

    def change_element_type(self):
        inp = open(self.model_name + ".inp")
        data = inp.read().replace(self.temp_inf_type, self.infinite_mesh_type)
        new_inp = open(self.model_name + ".inp", "w")
        new_inp.write(data)
        new_inp.close()
        inp.close()

    def operator(self):
        self.create_part()
        self.create_instance("Soil Part-1",self.soilPart)
        self.create_sheet_pile()

        for i in range(len(self.parameter["Name"])):
            name = self.parameter["Name"][i]
            height = sum(self.parameter["Thicknesses"][:i + 1])
            density = self.parameter["Density"][i]
            thickness = self.parameter["Thicknesses"][i]
            Vs = self.parameter["Vs"][i]
            elasticity = (self.parameter["Elastic"][i], self.parameter["Poisson"][i])
            damping_ratio = self.parameter["Damping Ratio"]

            self.partition_part(height)
            self.create_material(name, {"E": elasticity, "D": density, "Damping": damping_ratio, "Vs": Vs,
                                        "H": thickness})

        self.create_section()
        self.create_edge_set()
        self.draw_source()
        self.create_step()
        self.create_face_sets()
        self.create_ditch()
        #self.create_rubber_barrier()
        self.divide_model()
        self.create_mesh()
        self.create_nodes()
        self.create_boundary_conditions()
        self.create_history_output()
        self.create_job()
        self.change_element_type()

model = Create_Model()
model.operator()
