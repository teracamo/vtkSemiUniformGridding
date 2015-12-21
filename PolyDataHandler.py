#!/usr/bin/python
"""
Author: Wong Matthew Lun
Date: 2015-12-08 6:21PM
"""
import vtk
import math
import time

class CenterLineHandler(vtk.vtkPolyData):
    def __init__(self, filename):
        self.filename = filename
        self._reader = None
        self._renderer = vtk.vtkRenderer()
        # self._renderWindow = vtk.vtkRenderWindow()
        # self._renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        self._IS_READ_FLAG=False

    def Read(self, m_forceRead=False):
        """
        Initial step, should be performed before everything else starts, considering to add
        this into the class constructor so that it is read automatically.
        This step will also recaclulate the centerline from the input and repopulate regions
        between the start/end pts and middle segment of the centerline.
        :return:
        """
        # Skip redundant read if it is already done
        if self._IS_READ_FLAG and not m_forceRead:
            return

        if self.filename.split('.')[-1] == "vtp":
            m_reader = vtk.vtkXMLPolyDataReader()
        else:
            raise IOError("Input file for centerline is of incorrect format")
        m_reader.SetFileName(self.filename)
        m_reader.Update()

        m_mapper = vtk.vtkPolyDataMapper()
        m_mapper.SetInputConnection(m_reader.GetOutputPort())

        m_actor = vtk.vtkActor()
        m_actor.SetMapper(m_mapper)

        # Reconstruct centerline polydata
        m_points = vtk.vtkPoints()
        m_rawData = m_reader.GetOutput()
        m_rawStart = m_rawData.GetPoint(m_rawData.GetNumberOfPoints() - 2)
        m_rawStartMiddle = m_rawData.GetPoint(0)
        m_points.InsertNextPoint(m_rawStart)

        m_startDirection = [m_rawStartMiddle[i] - m_rawStart[i] for i in xrange(3)]
        m_startLength = math.sqrt(sum([m_startDirection[i]**2 for i in xrange(3)]))
        m_startNumOfIntervals = int(m_startLength/0.3)

        # Populate start region
        for i in xrange(m_startNumOfIntervals):
            m_rawStart = [m_rawStart[j] + m_startDirection[j] / m_startNumOfIntervals for j in xrange(3)]
            m_points.InsertNextPoint(m_rawStart)

        # Push back nodes in original middle segment
        for i in xrange(m_rawData.GetNumberOfPoints() - 2):
            m_points.InsertNextPoint(m_rawData.GetPoint(i))

        # Populate the ending region
        m_rawEnd = m_rawData.GetPoint(m_rawData.GetNumberOfPoints() - 1)
        m_rawEndMiddle = m_rawData.GetPoint(m_rawData.GetNumberOfPoints() - 3)
        m_endDirection = [m_rawEnd[i] - m_rawEndMiddle[i] for i in xrange(3)]
        m_endLength = math.sqrt(sum([m_endDirection[i]**2 for i in xrange(3)]))
        m_endNumOfIntervals = int(m_endLength/0.3)
        for i in xrange(m_endNumOfIntervals):
            m_rawEndMiddle = [m_rawEndMiddle[j] + m_endDirection[j] / m_endNumOfIntervals for j in xrange(3)]
            m_points.InsertNextPoint(m_rawEndMiddle)

        m_data = vtk.vtkPolyData()
        m_data.SetPoints(m_points)


        self._reader = m_reader
        self._renderer.AddActor(m_actor)
        self._rawData = m_rawData
        self._data = m_data
        self._IS_READ_FLAG=True
        pass

    def ShowInteractor(self):
        """
        Useless function, For Debug, will delete
        :return:
        """
        self._renderWindow.AddRenderer(self._renderer)
        self._renderWindowInteractor.SetRenderWindow(self._renderWindow)
        self._renderer.SetBackground(0,0,0)
        self._renderer.Render()
        self._renderWindowInteractor.Initialize()
        self._renderWindowInteractor.Start()
        pass

    def WriteImage(self, m_outFileName="./Dump/tmp.png",m_dimension=[400,400]):
        """
        Write current renderer to a png file. For Debug

        :param m_outFileName:   [str] Output name of the file, can be directory name. Default="./Dump/tmp.png"
        :param m_dimension:     [x, y]. Dimension, i.e. width and height of the image file.
        :return:
        """
        if self._renderer.GetRenderWindow() == None:
            self._renderWindow.AddRenderer(self._renderer)

        elif self._renderer.GetRenderWindow() != self._renderWindow:
            self._renderer.GetRenderWindow().Finalize()
            self._renderWindow = vtk.vtkRenderWindow()
            self._renderWindow.AddRenderer(self._renderer)
        else:
            self._renderWindow = vtk.vtkRenderWindow()
            self._renderWindow.AddRenderer(self._renderer)

        self._renderWindow.SetOffScreenRendering(1)
        self._renderWindow.SetSize(m_dimension)
        self._renderWindow.Render()
        self._renderWindow.SetAAFrames(10)

        m_writer = vtk.vtkPNGWriter()
        m_wintoim = vtk.vtkWindowToImageFilter()
        m_wintoim.SetInput(self._renderWindow)
        m_wintoim.Update()

        m_writer.SetInputConnection(m_wintoim.GetOutputPort())
        m_writer.SetFileName(m_outFileName)
        m_writer.Write()

        pass

    def GetData(self):
        """
        Return the data output from the reader.

        Require sequence: Read()

        :return:
        """
        return self._data

    def GetPointActor(self, m_ptId, m_radius=1, m_color=[0.5,0.5,0]):
        """
        Get a sphere source actor at the specified point. For Debug

        :param m_color:     [list]  RGB of the actor
        :param m_radius:    [float] Radius of the actor
        :param m_ptId:      [int]   vtkID
        :return:
        """
        m_ptCoord = self.GetPoint(m_ptId)
        m_sphere = vtk.vtkSphereSource()
        m_sphere.SetCenter(m_ptCoord)
        m_sphere.SetRadius(m_radius)

        m_sphereMapper = vtk.vtkPolyDataMapper()
        m_sphereMapper.SetInputConnection(m_sphere.GetOutputPort())
        m_sphereMapper.Update()

        m_actor = vtk.vtkActor()
        m_actor.SetMapper(m_sphereMapper)
        m_actor.GetProperty().SetColor(m_color)

        return m_actor

    def GetPoint(self, m_ptId):
        """
        Return coordinate of the point.
        :param m_ptId:
        :return:
        """
        return self._data.GetPoint(m_ptId)

    def GetDistance(self, int1, int2):
        """
        Return the distance between two points of the data set, specified by its ID
        Can be replaced by vtkMath() methods
        Require sequence: Read()

        :param int1: [int] ID of the first point
        :param int2: [int] ID of the second point
        :return:
        """
        m_p1, m_p2 = [self._data.GetPoint(i) for i in [int1, int2]]
        d = math.sqrt(sum([(m_p1[i] - m_p2[i])**2 for i in xrange(3)]))
        return d

    def GetEqualDistanceIntervalsIndex(self, m_distance, m_startPadding=0, m_endPadding=0):
        """
        Return a list of index indicating the id of a roughly uni-distance points.

        :param m_distance:      [float] Distance between each segments
        :param m_startingPoint: [int] Index of the user specified starting point. Default=0
        :return:
        """
        m_intevals = []
        m_loopValue = 0
        m_startPadding  = int(m_startPadding/.3)
        m_endPadding = int(m_endPadding/.3)
        m_intevals.append(m_startPadding+1)
        for i in xrange(m_startPadding+1, self._data.GetNumberOfPoints() - 1 - m_endPadding):
            m_loopValue += self.GetDistance(i, i-1)
            if m_loopValue > m_distance:
                m_intevals.append(i)
                m_loopValue = 0
        return m_intevals

    def PrintPoints(self):
        """
        Useless, for DEBUG

        Require sequence: Read()
        :return:
        """
        m_data = self._data
        m_numberOfPoints = m_data.GetNumberOfPoints()
        for i in xrange(m_numberOfPoints):
            print m_data.GetPoint(i)
        pass

    def LoopPoints(self):
        """
        Useless, for DEBUG

        Require sequence: Read()
        :return:
        """
        outList = []
        m_data = self._data
        m_numberOfPoints = m_data.GetNumberOfPoints()
        for i in xrange(m_numberOfPoints):
            outList.append(m_data.GetPoint(i))

        return outList

    def GetNormalizedTangent(self, m_pointID, range=3, step=1):
        m_indexlist = [m_pointID + i for i in xrange(-range, range+1, step)]
        m_preAverage = [0,0,0]
        m_loopFactor = 0
        for i in m_indexlist:
            l_n = [self._data.GetPoint(i % self._data.GetNumberOfPoints())[k] - self._data.GetPoint((i - 1) % self._data.GetNumberOfPoints())[k] for k in xrange(3)]
            l_magnitude = math.sqrt(sum([l_n[k]**2 for k in xrange(3)]))
            if l_magnitude == 0:
                continue
            else:
                m_preAverage = [m_preAverage[k] + l_n[k]/l_magnitude for k in xrange(3)]
                m_loopFactor += 1
        m_preAverage = [m_preAverage[k]*step/float(m_loopFactor) for k in xrange(3)]
        return m_preAverage

    def GetPoint(self, m_int):
        return self._data.GetPoint(m_int)

class ArmSurfaceHandler(vtk.vtkPolyData):
    def __init__(self, filename, centerline, openingMarker):
        """
        Create an ArmSurface object

        :param filename:    STL file of the casting
        :param centerline:  Centerline Object of the casting
        :return:
        """
        self.filename = filename
        self._reader = None
        self._renderer = vtk.vtkRenderer()
        # self._renderWindow = vtk.vtkRenderWindow()
        # self._renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        self._IS_READ_FLAG=False
        self._openingMarker = openingMarker
        self._bufferAngle = 0

        # Read Centerline if it is not read before assignment
        centerline.Read()
        self._centerLine = centerline

    def SetBufferAngle(self, angle):
        self._bufferAngle = float(angle)
        pass

    def IsRead(self):
        return self._IS_READ_FLAG

    def Read(self, m_forceRead=False):
        """
        Initial step, should be performed before everything else starts, considering to add
        this into the class constructor so that it is read automatically.
        :return:
        """

        # Skip redundant read if it is already done
        if self._IS_READ_FLAG and not m_forceRead:
            return

        if self.filename.split('.')[-1] == "vtp" or self.filename.split('.')[-1] == "vtk":
            m_reader = vtk.vtkXMLPolyDataReader()
        elif self.filename.split('.')[-1] == "stl":
            m_reader = vtk.vtkSTLReader()
        else:
            raise IOError("Input file for arm surface is of incorrect format")
        m_reader.SetFileName(self.filename)
        m_reader.Update()

        m_mapper = vtk.vtkPolyDataMapper()
        m_mapper.SetInputConnection(m_reader.GetOutputPort())

        m_actor = vtk.vtkActor()
        m_actor.SetMapper(m_mapper)

        self._reader = m_reader
        self._renderer.AddActor(m_actor)
        self._data = m_reader.GetOutput()
        self._IS_READ_FLAG = True
        pass

    def GetPoint(self, m_int):
        """
        Return the coordinate of the vtkId point

        :param m_int:   [int] vtkId
        :return:
        """
        return self._data.GetPoint(m_int)

    def SliceSurfaceOld(self, m_pt, m_normalVector, m_thickness=0.1):
        """
        Cut surface by checking dot product of the relative position vector from center line m_pt to
        all points and the normal vector of the plane. If the dot product is smaller than a
        given value, that point is accepted

        Replaced by vtkcutter function.

        :param m_pt:            [vtkID] a point of the centerline on the desired cutting plane
        :param m_normalVector:  [x, y, z] normal vector of the desired cutting plane
        :return:
        """
        m_slicepoints = []
        for i in xrange(self._data.GetNumberOfPoints()):
            m_tmp = self._data.GetPoint(i)
            m_ringVector = [m_tmp[k] - m_pt[k] for k in xrange(3)]
            m_dotProduct = sum([m_ringVector[k] * m_normalVector[k] for k in xrange(3)])
            if math.fabs(m_dotProduct) < m_thickness :
                m_slicepoints.append(i)
                # if i%100==0:
                #     print math.fabs(m_dotProduct)
        m_vtkslicepoints = vtk.vtkPolyData()
        m_vtkpts = vtk.vtkPoints()
        for i in m_slicepoints:
            m_vtkpts.InsertNextPoint(self._data.GetPoint(i))
        m_vtkslicepoints.SetPoints(m_vtkpts)
        return m_vtkslicepoints

    def SliceSurface(self, m_pt, m_normalVector):
        """
        Use vtkCutter to obtain cutted.
        :param m_pt:
        :param m_normalVector:
        :return:
        """
        m_plane=vtk.vtkPlane()
        m_plane.SetOrigin(m_pt)
        m_plane.SetNormal(m_normalVector)

        #create cutter
        m_cutter=vtk.vtkCutter()
        m_cutter.SetCutFunction(m_plane)
        m_cutter.SetInputConnection(self._reader.GetOutputPort())
        m_cutter.Update()

        m_vtkpoints = m_cutter.GetOutput().GetPoints()
        return m_vtkpoints

    def GetSemiUniDistnaceGrid(self, m_holePerSlice, m_numberOfSlice, m_errorTolerance=1, m_startPadding = 0, m_endPadding=0, m_bufferDeg=40):
        """
        Obtain a set of coordinates roughly equal to a projection of periodic square grid vertex on the arm
        surface.

        :param m_holePerSlice:      [int]   Desired number of holes per slice
        :param m_numberOfSlice:     [int]   Desired number of slices
        :param m_errorTolerance:    [float] The maximum allowed deviation of hole coordinate from idea grid
        :param m_startPadding:      [int]   Starting side padding where no holes will be drilled
        :param m_endPadding:        [int]   Ending side padding where no holes will be drilled
        :param m_bufferDeg:         [float] Angle between planes where buffers zones are in between. Default to 40
        :return: [list] List of hole coordinates
        """
        vtkmath = vtk.vtkMath()

        if not self._centerLine._IS_READ_FLAG:
            self._centerLine.Read()

        if self._bufferAngle != None:
            m_bufferDeg = self._bufferAngle

        m_totalDistance = 0
        for i in xrange(1 + int(m_startPadding/0.3), self._centerLine._data.GetNumberOfPoints() - int(m_endPadding/0.3)):
            m_totalDistance += self._centerLine.GetDistance(i, i-1)

        # Shrink the distance a bit before deviding it so that all intervals will lie in the padded segment
        m_sliceSpacing = (m_totalDistance)*0.98/(m_numberOfSlice)
        m_intervalIndexes = self._centerLine.GetEqualDistanceIntervalsIndex(m_sliceSpacing, m_startPadding, m_endPadding)
        self._centerLineIntervals = m_intervalIndexes

        m_tangents = []
        for k in xrange(len(m_intervalIndexes)):
            m_tmp = self._centerLine.GetNormalizedTangent(m_intervalIndexes[k], range=12, step=3)
            m_tangents.append(m_tmp)

        m_average = [sum([m_tangents[i][j] for i in xrange(3)])/float(len(m_tangents)) for j in xrange(3)]

        m_openingList = []
        m_holeList = []
        m_alphaNormal = None
        m_masterPt = self._centerLine.GetPoint(m_intervalIndexes[0])

        # Define cast opening zone and start drilling zone
        if m_bufferDeg != None and self._openingMarker != None:
            m_kdtree = vtk.vtkKdTreePointLocator()
            m_kdtree.SetDataSet(self._centerLine._data)
            m_kdtree.BuildLocator()
            m_closestCenterlinePointId = m_kdtree.FindClosestPoint(self._openingMarker)
            m_closestCenterlinePoint = self._centerLine.GetPoint(m_closestCenterlinePointId)
            m_masterPt = m_closestCenterlinePoint


        # Drill along intervals
        for i in xrange(len(m_intervalIndexes)):
            l_sliceCenter = self._centerLine.GetPoint(m_intervalIndexes[i])
            l_slice = self.SliceSurface(l_sliceCenter, m_average)
            if i == 0:
                # Define the starting vector for all slice
                # l_ringAlphaPt = l_slice.GetPoint(i)
                l_ringAlphaVect = [self._openingMarker[j] - m_masterPt[j] for j in xrange(3)]
                m_alphaNormal = [0,0,0]
                vtkmath.Cross(m_average, l_ringAlphaVect, m_alphaNormal)

            for j in xrange(l_slice.GetNumberOfPoints()):
                l_ringSliceAlphaVect = [l_slice.GetPoint(j)[k] - l_sliceCenter[k] for k in xrange(3)]
                l_ringSliceMasterVect = [l_slice.GetPoint(j)[k] - m_masterPt[k] for k in xrange(3)]
                if math.fabs(vtkmath.Dot(l_ringSliceMasterVect, m_alphaNormal)) < 10 and vtkmath.Dot(l_ringSliceAlphaVect, l_ringAlphaVect) > 0:
                    break

            l_uniformSectionDegree = (360. - m_bufferDeg)/m_holePerSlice
            l_sectionDegree = (360. - m_bufferDeg)/m_holePerSlice
            l_loopbreak = 0
            m_openingList.append([l_ringSliceAlphaVect[k] + l_sliceCenter[k] for k in xrange(3)]) # Include first vector
            l_holeList = []
            while(len(l_holeList) < m_holePerSlice - 1):
                if len(l_holeList) == 0:
                    l_sectionDegree += m_bufferDeg/2
                for j in xrange(l_slice.GetNumberOfPoints()):
                    l_p1 = [0.,0.,0.]
                    l_ringVect = [l_slice.GetPoint(j)[k] - l_sliceCenter[k] for k in xrange(3)]
                    vtkmath.Cross(l_ringSliceAlphaVect, l_ringVect,l_p1)
                    l_p2 = vtkmath.Dot(l_p1, m_average)
                    l_angleBetweenRunningAndInitialVector = vtkmath.AngleBetweenVectors(l_ringSliceAlphaVect, l_ringVect)
                    if l_angleBetweenRunningAndInitialVector > vtkmath.RadiansFromDegrees(l_sectionDegree - m_errorTolerance/2) and l_angleBetweenRunningAndInitialVector < vtkmath.RadiansFromDegrees(l_sectionDegree + m_errorTolerance/2.)and l_p2 > 0:
                        l_ringSliceAlphaVect = l_ringVect
                        l_holeList.append([l_ringVect[k] + l_sliceCenter[k] for k in xrange(3)])
                        l_sectionDegree += (l_uniformSectionDegree - vtkmath.DegreesFromRadians(l_angleBetweenRunningAndInitialVector))
                        break
                if l_loopbreak == m_holePerSlice:
                    raise RuntimeError("Current error tolerence setting is to low to produce anything.")
                l_loopbreak += 1
            m_holeList.extend(l_holeList)
            self._openingList = m_openingList
        return m_holeList

    def GetPointActor(self, m_ptId, m_radius=1, m_color=[0.5,0.5,0]):
        """
        Get a sphere source actor at the specified point. For Debug

        :param m_color:     [list]  RGB of the actor
        :param m_radius:    [float] Radius of the actor
        :param m_ptId:      [int]   vtkID
        :return:
        """
        m_ptCoord = self.GetPoint(m_ptId)
        m_sphere = vtk.vtkSphereSource()
        m_sphere.SetCenter(m_ptCoord)
        m_sphere.SetRadius(m_radius)

        m_sphereMapper = vtk.vtkPolyDataMapper()
        m_sphereMapper.SetInputConnection(m_sphere.GetOutputPort())
        m_sphereMapper.Update()

        m_actor = vtk.vtkActor()
        m_actor.SetMapper(m_sphereMapper)
        m_actor.GetProperty().SetColor(m_color)

        return m_actor

    def WriteImage(self, m_outFileName="./Dump/tmp.png",m_dimension=[400,400]):
        """
        Write current renderer to a png file. For Debug

        :param m_outFileName:   [str] Output name of the file, can be directory name. Default="./Dump/tmp.png"
        :param m_dimension:     [x, y]. Dimension, i.e. width and height of the image file.
        :return:
        """
        if self._renderer.GetRenderWindow() == None:
            self._renderWindow.AddRenderer(self._renderer)

        elif self._renderer.GetRenderWindow() != self._renderWindow:
            self._renderer.GetRenderWindow().Finalize()
            self._renderWindow = vtk.vtkRenderWindow()
            self._renderWindow.AddRenderer(self._renderer)
        else:
            self._renderWindow = vtk.vtkRenderWindow()
            self._renderWindow.AddRenderer(self._renderer)

        self._renderWindow.SetOffScreenRendering(1)
        self._renderWindow.SetSize(m_dimension)
        self._renderWindow.Render()
        self._renderWindow.SetAAFrames(10)

        m_writer = vtk.vtkPNGWriter()
        m_wintoim = vtk.vtkWindowToImageFilter()
        m_wintoim.SetInput(self._renderWindow)
        m_wintoim.Update()

        m_writer.SetInputConnection(m_wintoim.GetOutputPort())
        m_writer.SetFileName(m_outFileName)
        m_writer.Write()

        pass

    def SphereDrill(self, m_holelist, m_holeRadius, m_quiet=False):
        m_totalNumOfHoles = len(m_holelist)
        if not m_quiet:
            t = time.time()
            print "Drilling"

        for i in xrange(m_totalNumOfHoles):
            m_sphere = vtk.vtkSphere()
            m_sphere.SetCenter(m_holelist[i])
            m_sphere.SetRadius(m_holeRadius)


            clipper = vtk.vtkClipPolyData()
            clipper.SetInputData(self._data)
            clipper.SetClipFunction(m_sphere)
            clipper.Update()

            clipped = clipper.GetOutput()
            self._data.DeepCopy(clipped)

            if not m_quiet:
                print "\t%s/%s -- %.2f %%"%(i+1, m_totalNumOfHoles, (i+1)*100/float(m_totalNumOfHoles))
        if not m_quiet:
            print "Finished: Totaltime used = %.2f s"%(time.time() - t)
        pass