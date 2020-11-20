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
from numpy import float, cumsum, array, sin, arange, pi, flipud, append


class Create_Model:
    def __init__(self):
        self.parameter = {"Name": temp_layer_names,
                          "Elastic": temp_elastic,
                          "Poisson": temp_poisson,
                          "Density": temp_density,
                          "Thicknesses": temp_thickness,
                          "Damping Ratio": temp_damping_ratio,
                          "Vs": temp_VS}

        self.inf_size_x = 10
        self.inf_size_y = 10
        self.inf_size_z = 10
        self.Width = float(temp_width)+self.inf_size_x
        self.Depth = float(sum(self.parameter["Thicknesses"]))+self.inf_size_z
        self.layer_heights = append([self.Depth], self.Depth - cumsum(self.parameter["Thicknesses"]))
        self.sorted_heights = array(sorted(self.layer_heights)[1:])
        self.Length = self.Width
        self.source_size = float(temp_source_size)
        self.accelometer_pattern = temp_accelerometer_pattern
        self.PGA = temp_PGA
        self.duration = temp_duration
        self.frequency = temp_frequency
        self.time_step = temp_time_step

        self.ditch_width = temp_ditch_width
        self.ditch_depth = temp_ditch_depth
        self.ditch_length = temp_ditch_length
        self.ditch2source = temp_ditch2source
        self.ditch_number = temp_ditchnumber
        self.ditch2ditch = temp_ditch2ditch

        self.fillDitch = int(temp_fill_ditch)
        self.RC_E = temp_RC_E
        self.RC_density = temp_RC_density

        self.free_space_X = float((self.Width - self.source_size))/2
        self.free_space_Y = float(self.inf_size_y + 1)

        self.Thicknesses = self.parameter["Thicknesses"]

        self.model_size = sum(self.accelometer_pattern) + self.source_size
        self.model_name = "temp_model_name"

        self.mesh_size = temp_mesh_size
        self.f = lambda L, x: [L[i:i + 1] for i in x]
        session.viewports["Viewport: 1"].setValues(displayedObject=None)
        mdb.models.changeKey(fromName="Model-1", toName=self.model_name)
        self.soilModel = mdb.models[self.model_name]

    def layer_centers(self):
        self.centers = []
        layer_heights = cumsum(flipud(self.parameter["Thicknesses"]))
        for i in range(len(layer_heights)):
            if i == 0:
                center = layer_heights[i] / 2
            else:
                center = layer_heights[i - 1] + \
                    (layer_heights[i] - layer_heights[i - 1]) / 2
            self.centers.append(center+self.inf_size_z)

    def create_part(self):
        soilProfileSketch = self.soilModel.ConstrainedSketch(
            name="__profile__", sheetSize=self.Width * 2)
        soilProfileSketch.rectangle(
            point1=(0, 0), point2=(self.Width, self.Length))

        self.soilPart = self.soilModel.Part(
            name="Soil Part", dimensionality=THREE_D, type=DEFORMABLE_BODY)
        self.soilPart.BaseSolidExtrude(
            sketch=soilProfileSketch, depth=self.Depth)

        del self.soilModel.sketches['__profile__']

        self.create_face_sets()
        """self.soilModel.ConstrainedSketch(gridSpacing=2.37, name='__profile__',
                                        sheetSize=self.Width, transform=self.soilPart.MakeSketchTransform(
                                         sketchPlane=self.soilPart.faces.findAt((0.1,0.1,self.Depth)),
                                         sketchPlaneSide=SIDE1,sketchOrientation=RIGHT, origin=(0, 0, self.Depth),
                                         sketchUpEdge=self.soilPart.edges.findAt((self.Width,self.Length/2,self.Depth))))

        self.soilPart.projectReferencesOntoSketch(filter=COPLANAR_EDGES,sketch=self.soilModel.sketches['__profile__'])
        self.soilModel.sketches['__profile__'].rectangle(point1=(self.inf_size_x, self.inf_size_y),point2=(self.Width-self.inf_size_x, self.Length - self.inf_size_y))
        self.soilModel.sketches['__profile__'].Line(point1=(0,0),point2=(self.inf_size_x,self.inf_size_y))
        self.soilModel.sketches['__profile__'].Line(point1=(self.Width,0),point2=(self.Width-self.inf_size_x,self.inf_size_y))
        self.soilModel.sketches['__profile__'].Line(point1=(self.Width,self.Length),point2=(self.Width-self.inf_size_x, self.Length - self.inf_size_y))
        self.soilModel.sketches['__profile__'].Line(point1=(0,self.Length),point2=(self.inf_size_x,self.Length - self.inf_size_y))
        self.soilPart.PartitionFaceBySketch(faces=self.soilPart.faces.findAt((self.Width/2,self.Length/2,self.Depth)),
                                            sketch=self.soilModel.sketches['__profile__'],
                                            sketchUpEdge=self.soilPart.edges.findAt((self.Width,self.Length/2,self.Depth)))
        self.soilPart.PartitionCellBySweepEdge(cells=self.soilPart.cells[0],edges=(
                                               self.soilPart.edges.findAt((self.inf_size_x,self.Length/2,self.Depth)),
                                               self.soilPart.edges.findAt((self.Width - self.inf_size_x,self.Length/2,self.Depth)),
                                               self.soilPart.edges.findAt((self.Width/2,self.inf_size_y,self.Depth)),
                                               self.soilPart.edges.findAt((self.Width/2,self.Length - self.inf_size_y,self.Depth))),
                                               sweepPath=self.soilPart.edges.findAt((0,0,self.Depth/2)))

        diagonals = [(self.inf_size_x/2,self.inf_size_y/2,self.Depth),
                     (self.Width-self.inf_size_x/2,self.inf_size_y/2,self.Depth),
                     (self.inf_size_x/2,self.Length - self.inf_size_y/2,self.Depth),
                     (self.Width-self.inf_size_x/2,self.Length - self.inf_size_y/2,self.Depth)]

        for i in diagonals:
            self.soilPart.PartitionCellBySweepEdge(cells=self.soilPart.cells, edges=(self.soilPart.edges.findAt(i),),
            sweepPath = self.soilPart.edges.findAt((0, 0, self.Depth / 2)))


        del self.soilModel.sketches['__profile__']
        self.partition_cell(self.inf_size_z)"""

    def partition_cell(self, z):

        face = self.soilPart.faces.findAt((0.1, 0, z))
        N1 = (0, 0, z)
        N2 = (self.Width, 0, z)

        self.soilPart.DatumPointByCoordinate(N1)
        self.soilPart.DatumPointByCoordinate(N2)
        try:
            self.soilPart.PartitionFaceByShortestPath(face, N1, N2)
            self.soilPart.PartitionCellBySweepEdge(cells=self.soilPart.cells, edges=(self.soilPart.edges.findAt((self.Width/2, 0, z)),),
                                                   sweepPath=self.soilPart.edges.findAt((0, 0.1, 0)))
        except:
            pass

    def natural_frequency(self, mode, Vs, H):
        f = (2 * mode - 1) * Vs / (4 * H)
        return f

    def rayleigh_damping(self, modes, Vs, H, damping_ratio):
        if Vs == 0:
            return 0, 0
        else:
            wi = self.natural_frequency(modes[0], Vs, H)
            wj = self.natural_frequency(modes[1], Vs, H)
            alpha = damping_ratio * 2 * wi * wj / (wi + wj)
            beta = damping_ratio * 2 / (wi + wj)

            return alpha, beta

    def create_material(self, name, properties):
        elastic = properties["E"]
        density = properties["D"]
        damping = properties["Damping"]
        H = properties.get("H", 0.005)
        Vs = properties.get("Vs", 0)
        alpha, beta = self.rayleigh_damping([1, 4], Vs, H, damping)
        self.soilMaterial = self.soilModel.Material(name)
        self.soilMaterial.Density(table=((density,),))
        self.soilMaterial.Elastic(table=(elastic,))
        self.soilMaterial.Damping(alpha=alpha, beta=beta)

    def create_section(self):
        for i in range(len(self.layer_heights)):
            z = float(self.layer_heights[i]) - 0.01
            if i == len(self.layer_heights)-1:
                i = len(self.layer_heights)-2

            name = self.parameter["Name"][i]

            index1 = self.soilPart.cells.findAt(
                (self.Width/2, self.Length/2, z)).index
            index2 = self.soilPart.cells.findAt((self.Width/2, 0.1, z)).index
            index3 = self.soilPart.cells.findAt(
                (self.Width - 0.1, self.Length/2, z)).index
            index4 = self.soilPart.cells.findAt(
                (self.Width/2, self.Length - 0.1, z)).index
            index5 = self.soilPart.cells.findAt((0.1, self.Length/2, z)).index
            section_name = name + "_Section"

            self.soilModel.HomogeneousSolidSection(
                name=section_name, material=name)
            self.soilPart.SectionAssignment(region=(self.soilPart.cells[index1], self.soilPart.cells[index2], self.soilPart.cells[index3],
                                                    self.soilPart.cells[index4], self.soilPart.cells[index5]), sectionName=section_name)
            self.soilPart.Set(cells=self.f(self.soilPart.cells, [
                              index1, index2, index3, index4, index5]), name=name + "_Cell")

    def create_edge_set(self):
        #Horizontal Edges
        horizontal_finite_edges = []
        horizontal_infinite_edges = []
        single_seed_edges = []
        heights = list(self.layer_heights) + [0]
        for z in heights:
            F1 = (self.Width/2, self.inf_size_y, z)
            F2 = (self.Width - self.inf_size_x, self.Length/2, z)
            F3 = (self.Width/2, self.Length - self.inf_size_y, z)
            F4 = (self.inf_size_x, self.Length/2, z)
            for node in [F1, F2, F3, F4]:
                horizontal_finite_edges.append(
                    self.soilPart.edges.findAt(node).index)

            INF1 = (self.Width / 2, 0, z)
            INF2 = (self.Width, self.Length / 2, z)
            INF3 = (self.Width / 2, self.Length, z)
            INF4 = (0, self.Length / 2, z)
            for node in [INF1, INF2, INF3, INF4]:
                horizontal_infinite_edges.append(
                    self.soilPart.edges.findAt(node).index)

            diagonals = [(self.inf_size_x / 2, self.inf_size_y / 2, z),
                         (self.Width - self.inf_size_x / 2, self.inf_size_y / 2, z),
                         (self.inf_size_x / 2, self.Length - self.inf_size_y / 2, z),
                         (self.Width - self.inf_size_x / 2, self.Length - self.inf_size_y / 2, z)]
            for node in diagonals:
                single_seed_edges.append(
                    self.soilPart.edges.findAt(node).index)

        self.soilPart.Set(edges=self.f(self.soilPart.edges,
                                       horizontal_finite_edges), name="H_F_Edges")
        self.soilPart.Set(edges=self.f(self.soilPart.edges,
                                       horizontal_infinite_edges), name="H_INF_Edges")

        #Vertical Edges
        vertical_edges = []
        heights = self.centers + [0.1]
        for z in heights:
            F1 = (self.Width-self.inf_size_x, self.inf_size_y, z)
            F2 = (self.Width-self.inf_size_x, self.Length - self.inf_size_y, z)
            F3 = (self.inf_size_x, self.Length - self.inf_size_y, z)
            F4 = (self.inf_size_x, self.inf_size_y, z)
            INF1 = (self.Width, 0, z)
            INF2 = (self.Width, self.Length, z)
            INF3 = (0, self.Length, z)
            INF4 = (0, 0, z)
            for node in [F1, F2, F3, F4, INF1, INF2, INF3, INF4]:
                if z == 0.1:
                    single_seed_edges.append(
                        self.soilPart.edges.findAt(node).index)
                else:
                    vertical_edges.append(
                        self.soilPart.edges.findAt(node).index)

        self.soilPart.Set(edges=self.f(self.soilPart.edges,
                                       vertical_edges), name="V_Edges")
        self.soilPart.Set(edges=self.f(self.soilPart.edges,
                                       single_seed_edges), name="Single_Seed_Edges")

    def create_face_sets(self):
        NX1 = (0, self.Length / 2, self.Depth / 2)
        NX2 = (self.Width, self.Length / 2, self.Depth / 2)
        NY1 = (self.Width / 2, 0, self.Depth / 2)
        NY2 = (self.Width / 2, self.Length, self.Depth / 2)
        NZ = (self.Width / 2, self.Length/2, 0)

        X1 = self.soilPart.faces.findAt(NX1).index
        X2 = self.soilPart.faces.findAt(NX2).index
        Y1 = self.soilPart.faces.findAt(NY1).index
        Y2 = self.soilPart.faces.findAt(NY2).index
        Z = self.soilPart.faces.findAt(NZ).index

        self.soilPart.Set(faces=self.f(
            self.soilPart.faces, [X1, X2]), name="X_Faces")
        self.soilPart.Set(faces=self.f(
            self.soilPart.faces, [Y1, Y2]), name="Y_Faces")
        self.soilPart.Set(faces=self.f(
            self.soilPart.faces, [Z]), name="Z_Face")

    def create_datum_planes(self):
        """cell1 = self.soilPart.cells.getByBoundingBox(0, 0, self.Depth - self.parameter["Thicknesses"][0], self.Width,
                                                     self.Length, self.Depth)
        d1 = self.soilPart.DatumPlaneByPrincipalPlane(XZPLANE, self.free_space_Y).id
        self.soilPart.PartitionCellByDatumPlane(cell1, self.soilPart.datums[d1])

        cell2 = self.soilPart.cells.getByBoundingBox(0, 0, self.Depth - self.parameter["Thicknesses"][0], self.Width,
                                                     self.Length, self.Depth)
        d2 = self.soilPart.DatumPlaneByPrincipalPlane(XZPLANE, self.free_space_Y + self.source_size).id
        self.soilPart.PartitionCellByDatumPlane(cell2, self.soilPart.datums[d2])

        cell3 = self.soilPart.cells.getByBoundingBox(0, 0, self.Depth - self.parameter["Thicknesses"][0], self.Width,
                                                     self.Length, self.Depth)
        d3 = self.soilPart.DatumPlaneByPrincipalPlane(YZPLANE, self.Width / 2).id
        self.soilPart.PartitionCellByDatumPlane(cell3, self.soilPart.datums[d3])"""
        edge = self.soilPart.edges.findAt(
            (self.Width, self.Length / 2, self.Depth))
        self.soilModel.ConstrainedSketch(gridSpacing=2.37, name='__profile__',
                                         sheetSize=self.Width, transform=self.soilPart.MakeSketchTransform(
                                             sketchPlane=self.soilPart.faces.findAt(
                                                 (self.Width/2, self.Length/2, self.Depth)),
                                             sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0, 0, self.Depth), sketchUpEdge=edge))

        self.soilPart.projectReferencesOntoSketch(
            filter=COPLANAR_EDGES, sketch=self.soilModel.sketches['__profile__'])

        self.soilModel.sketches['__profile__'].rectangle(point1=(0, self.free_space_Y),
                                                         point2=(self.Width, self.free_space_Y + self.source_size))
        self.soilModel.sketches['__profile__'].Line(
            point1=(self.Width/2, 0), point2=(self.Width/2, self.Length))
        if self.ditch_number > 0:
            self.soilModel.sketches['__profile__'].rectangle(point1=(self.Width/2 - self.ditch_length/2, 0),
                                                             point2=(self.Width/2 + self.ditch_length/2, self.Length))
        self.soilPart.PartitionFaceBySketch(
            faces=self.soilPart.faces.findAt(
                (self.Width / 2, self.Length / 2, self.Depth)),
            sketch=self.soilModel.sketches['__profile__'], sketchUpEdge=edge)

    def draw_source(self):

        N1 = (self.free_space_X, self.free_space_Y, self.Depth)
        N2 = (self.free_space_X + self.source_size,
              self.free_space_Y, self.Depth)
        N3 = (self.free_space_X + self.source_size,
              self.free_space_Y + self.source_size, self.Depth)
        N4 = (self.free_space_X, self.free_space_Y +
              self.source_size, self.Depth)

        for i in [N1, N2, N3, N4]:
            self.soilPart.DatumPointByCoordinate(i)

        face = self.soilPart.faces.findAt(N1)
        self.soilPart.PartitionFaceByShortestPath(face, N1, N2)
        self.soilPart.PartitionFaceByShortestPath(face, N2, N3)
        self.soilPart.PartitionFaceByShortestPath(face, N3, N4)
        self.soilPart.PartitionFaceByShortestPath(face, N4, N1)
        Y = self.soilPart.faces.findAt(
            (self.free_space_X+0.01, self.free_space_Y+0.01, self.Depth)).index
        self.soilPart.Set(faces=self.f(
            self.soilPart.faces, [Y]), name="Source Face")

    def draw_ditches(self, ditch_number):
        x1 = (self.Width - self.ditch_length)/2
        x2 = x1 + self.ditch_length

        y1 = self.free_space_Y + self.source_size + self.ditch2source + \
            (ditch_number-1)*(self.ditch_width+self.ditch2ditch)

        y2 = y1 + self.ditch_width
        top_face = self.soilPart.faces.findAt(
            (self.Width/2, self.Length/2, self.Depth))
        edge_index = self.soilPart.edges.findAt(
            (self.Width, self.Length/2, self.Depth)).index
        self.soilModel.ConstrainedSketch(name="__profile__", sheetSize=self.Width * 2,
                                         transform=self.soilPart.MakeSketchTransform(sketchPlane=top_face, origin=(0, 0, self.Depth),
                                                                                     sketchPlaneSide=SIDE1, sketchUpEdge=self.soilPart.edges[edge_index], sketchOrientation=RIGHT))
        sketch = self.soilModel.sketches['__profile__']
        self.soilPart.projectReferencesOntoSketch(
            filter=COPLANAR_EDGES, sketch=sketch)
        sketch.rectangle(point1=(x1, float(y1)), point2=(x2, float(y2)))
        self.soilPart.CutExtrude(depth=self.ditch_height, flipExtrudeDirection=OFF, sketch=sketch,
                                 sketchOrientation=RIGHT, sketchPlane=top_face, sketchPlaneSide=SIDE1,
                                 sketchUpEdge=self.soilPart.edges[edge_index])
        del self.soilModel.sketches['__profile__']

    def create_ditch(self):
        x1 = self.free_space_X - (self.ditch_length - self.source_size) / 2
        x2 = x1 + self.ditch_length
        if self.ditch_number > 0:
            if self.Depth - self.ditch_height != self.parameter["Thicknesses"][0]:
                d_bottom = self.soilPart.DatumPlaneByPrincipalPlane(
                    XYPLANE, self.Depth - self.ditch_height).id
                self.soilPart.PartitionCellByDatumPlane(
                    self.soilPart.cells, self.soilPart.datums[d_bottom])

            """for i in range(1, self.ditch_number + 1):
                Y1 = self.free_space_Y + self.source_size + self.ditch2source + (i - 1) * (self.ditch_width + self.ditch2ditch)
                Y2 = Y1 + self.ditch_width
                for i in [Y1, Y2]:
                    cells = self.soilPart.cells.getByBoundingBox(0, 0, self.Depth - self.ditch_height, self.Width,
                                                                 self.Length, self.Depth)
                    dz = self.soilPart.DatumPlaneByPrincipalPlane(XZPLANE, i).id
                    self.soilPart.PartitionCellByDatumPlane(cells, self.soilPart.datums[dz])

            for i in [x1, x2]:
                cells = self.soilPart.cells.getByBoundingBox(0, 0, self.Depth - self.ditch_height, self.Width, self.Length,
                                                             self.Depth)
                dx = self.soilPart.DatumPlaneByPrincipalPlane(YZPLANE, i).id
                self.soilPart.PartitionCellByDatumPlane(cells, self.soilPart.datums[dx])"""

            for i in range(1, self.ditch_number + 1):
                self.draw_ditches(i)

    def create_instance(self):
        self.soilModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
        self.soilModel.rootAssembly.Instance(
            dependent=ON, name="Soil Part-1", part=self.soilPart)
        self.soilModel.rootAssembly.regenerate()

    def create_mesh(self):
        self.soilPart.setMeshControls(
            elemShape=HEX, regions=self.soilPart.cells, technique=STRUCTURED)
        self.soilPart.setElementType(elemTypes=(mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD),),
                                     regions=(self.soilPart.cells,))

        # Vertical Meshing
        #self.soilPart.seedEdgeBySize(edges=self.soilPart.sets["V_Edges"].edges, size=self.mesh_size,constraint=FIXED)
        self.soilPart.seedPart(size=self.mesh_size)
        # Surface Meshing
        # Y-axis
        #self.soilPart.seedEdgeBySize(edges=self.soilPart.sets["SurfaceEdges"].edges,size = self.mesh_size)
        #self.soilPart.seedEdgeBySize(edges=self.soilPart.sets["HorizontalEdges"].edges,size = self.mesh_size)
        #for edge in self.soilPart.sets["HorizontalEdges"].edges:
        #    self.soilPart.setSeedConstraints(constraint=FIXED, edges=(edge,))
        self.soilPart.generateMesh()

        # self.soilPart.seedEdgeByBias(biasMethod=DOUBLE, endEdges=self.soilPart.sets["TopEdge"].edges, minSize=float(self.mesh_size), maxSize=float(self.max_mesh_size))

    def create_nodes(self):
        self.node_list = []
        x2 = self.Width / 2
        y2 = self.free_space_Y + self.source_size + \
            cumsum(self.accelometer_pattern)
        for i in y2:
            self.node_list.append(
                self.soilPart.nodes.getClosest((x2, i, self.Depth)))
            self.node_list.append(
                self.soilPart.nodes.getClosest((x2, i, self.Depth)))

        self.soilPart.Set(nodes=mesh.MeshNodeArray(
            self.node_list), name="Accelometers")

    def create_vibration(self):
        time = arange(0, self.duration + self.time_step, self.time_step)
        accelerations = self.PGA * 9.81 * sin(2 * pi * self.frequency * time)

        self.data = [[time[i], accelerations[i]] for i in range(len(time))]

    def create_step(self):
        self.create_vibration()
        self.soilModel.ImplicitDynamicsStep(initialInc=self.time_step, timePeriod=self.duration, maxInc=self.time_step,
                                            maxNumInc=int(2 * (self.duration / self.time_step)), name='Vibration Step',
                                            previous='Initial')
        self.soilModel.TabularAmplitude(
            name="Vibration", timeSpan=STEP, smooth=SOLVER_DEFAULT, data=self.data)

    def create_boundary_conditions(self):
        Sets = self.soilModel.rootAssembly.instances["Soil Part-1"].sets
        self.soilModel.DisplacementBC(createStepName='Initial', name='BC-X',
                                      region=self.soilModel.rootAssembly.instances["Soil Part-1"].sets['X_Faces'], u1=0)
        self.soilModel.DisplacementBC(createStepName='Initial', name='BC-Z',
                                      region=self.soilModel.rootAssembly.instances[
                                          "Soil Part-1"].sets['Z_Face'], u1=0,
                                      u2=0, u3=0)
        self.soilModel.DisplacementBC(createStepName='Initial', name='BC-Y',region=self.soilModel.rootAssembly.instances["Soil Part-1"].sets['Y_Faces'], u2=0)
        self.soilModel.DisplacementBC(
            amplitude="Vibration", createStepName='Vibration Step', name='Vibration', region=Sets['Source Face'], u3=-0.001)

    def create_history_output(self):
        self.soilModel.fieldOutputRequests["F-Output-1"].deactivate(
            "Vibration Step")
        self.soilModel.HistoryOutputRequest(createStepName="Vibration Step", frequency=1, name="H-Output-2",
                                            variables=('A3',),
                                            region=self.soilModel.rootAssembly.allInstances['Soil Part-1'].sets[
                                                'Accelometers'])

        del self.soilModel.historyOutputRequests['H-Output-1']
        del self.soilModel.fieldOutputRequests['F-Output-1']

    def create_job(self):
        self.job_name = self.model_name
        mdb.Job(model=self.model_name, name=self.job_name, type=ANALYSIS, memory=90, memoryUnits=PERCENTAGE, numCpus=6,
                numDomains=6, numGPUs=1)
        mdb.jobs[self.model_name].writeInput(consistencyChecking=OFF)

    def operator(self):
        self.create_part()
        self.layer_centers()
        #self.create_face_sets()

        for i in range(len(self.parameter["Name"])):
            name = self.parameter["Name"][i]
            height = sum(self.parameter["Thicknesses"][:i + 1])
            density = self.parameter["Density"][i]
            thickness = self.parameter["Thicknesses"][i]
            Vs = self.parameter["Vs"][i]
            elasticity = (self.parameter["Elastic"]
                          [i], self.parameter["Poisson"][i])
            damping_ratio = self.parameter["Damping Ratio"]

            self.partition_cell(self.Depth - height)
            self.create_material(name, {
                                 "E": elasticity, "D": density, "Damping": damping_ratio, "Vs": Vs, "H": thickness})

        self.create_section()
        #self.create_edge_set()
        self.draw_source()
        self.create_ditch()
        self.create_datum_planes()
        self.create_instance()
        self.create_mesh()
        self.create_nodes()
        self.create_step()
        self.create_boundary_conditions()
        self.create_history_output()
        self.create_job()


model = Create_Model()
model.operator()
