#!/usr/bin/python
"""
Author: Wong Matthew Lun
Date: 2015-12-08 6:21PM

Return exit code  list:
0   Success
1   IOError - Most likely Write Failed
2   IOError - Cannot find surface/centerline files *OR* format of the input file is not correct
3   RuntimeError - Tolerance errors, please set larger error tolerance
4   ValueError - Slice alpha vector search reaches maximum tolerance
"""

import optparse
import os
import sys

import vtk

from PolyDataHandler import CenterLineHandler, ArmSurfaceHandler


def main(args):
    parser = optparse.OptionParser()
    parser.add_option("-s", "--surface",action="store", dest="surface", default=True,help="Input surface filename.")
    parser.add_option("-q", "--quiet",action="store_true", dest="quiet", default=False,help="Suppress console outputs")
    parser.add_option("-c", "--centerline",action="store", dest="centerline", default=True,help="Input centerline filename.")
    parser.add_option("-o", "--output", action="store", dest="outFileName", type=str, default="drilled.stl", help="Set output casting surface stl file name")
    parser.add_option("-O", "--outputOpening", action="store", dest="outOpeningFileName", type=str, default="buff.vtp", help="Set output buffer points vtp file name")
    parser.add_option("-m", "--holesPerSlice", action="store", dest="holesPerSlice", type=int, default=5, help="Set number of holes per slice")
    parser.add_option("-n", "--numOfSlice", action="store", dest="numOfSlice", type=int ,default=5, help="Set number of slices")
    parser.add_option("-r", "--radius", action="store", dest="radius", type=float, default=5, help="Set hole radius required")
    parser.add_option("-p", "--padding", action="store", dest="padding", type=str, default="20,10", help="Set padding level where no holes are drilled")
    parser.add_option("-e", "--errorTorlerance", action="store", dest="error", type=float, default=1, help="Set maximum error tolerance from idea grid in degrees")
    parser.add_option("-d", "--noDrillCoord", action="store", dest="omitted", default=None, help="Set the coordinates start drilling area")
    parser.add_option("-b", "--bufferAngle", action="store", dest="bufferAngle", type=float, default=0, help="Buffer angle which decide the buffer area, calculated in degrees")
    parser.add_option("-B", "--bufferPolyLines", action="store", dest="bufferPDs", type=str, default=None,
                      help="Specify buffer region by polylines. Seperate filenames with ';'. If this option is selected, buffer angle will be ignored.")
    parser.add_option("-t", "--twoSides", action="store_true", dest="twoSides", default=False,
                      help="If this option is selected, there will be two openning buffer space and output will consist two polylines in one polydata.")
    parser.add_option("-a", "--auto", action="store_true", dest="auto", default=False, help="Automatically determine parameters")


    (options, args) = parser.parse_args()
    surfaceFileName = options.surface
    centerlineFileName = options.centerline
    outFileName = options.outFileName
    [startPadding, endPadding] = [int(options.padding.split(",")[i]) for i in xrange(2)]

    try:
        if not os.path.isfile(surfaceFileName):
            if not options.quiet:
                print "[Error] Surface file %s dosen't exist!"%surfaceFileName
            raise IOError("Surface file %s dosen't exist!"%surfaceFileName)
        if not os.path.isfile(centerlineFileName):
            if not options.quiet:
                print "[Error] Centerline file %s dosen't exist exist!"%centerlineFileName
            raise IOError("Centerline file %s dosen't exist!"%centerlineFileName)
        if options.outOpeningFileName.split('.')[-1] != "vtp":
            if not options.quiet:
                print "[Error] Name specified for buffer opening points should end with suffix .vtp!"
            raise IOError("Name specified for buffer opening points should end with suffix .vtp!")

        if type(options.omitted) != None and type(options.omitted) != str and options.bufferAngle != 0:
            raise TypeError("[Error] Start drill coordinates should be specified with strings")
        else:
            openingMarker = [float(options.omitted.split(',')[i]) for i in xrange(3)]


        # create center line object
        cl = CenterLineHandler(centerlineFileName)
        cl.Read()

        # careate arm object
        arm = ArmSurfaceHandler(surfaceFileName, cl, openingMarker)
        arm.Read()
        if (options.bufferAngle > 0):
            arm.SetBufferAngle(options.bufferAngle)
        elif (options.bufferPDs != None):
            arm.SetBufferPolyLines(options.bufferPDs)
            arm.SetBufferAngle(0)

        # Get a list of holes and then drill
        holelist = arm.GetSemiUniDistnaceGrid(options.holesPerSlice + 1, options.numOfSlice - 1, options.error,
                                              startPadding, endPadding, options.bufferAngle, options.twoSides)
        arm.SphereDrill(holelist, options.radius, options.quiet)

        clippermapper = vtk.vtkPolyDataMapper()
        if vtk.vtkVersion().GetVTKVersion < 6:
            clippermapper.SetInput(arm._data)
        else:
            clippermapper.SetInputData(arm._data)

        writer = vtk.vtkSTLWriter()
        writer.SetFileName(outFileName)
        writer.SetInputData(arm._data)

        # Make a polyline
        polyline = arm.GetOpenningLine()

        polylineWriter = vtk.vtkXMLPolyDataWriter()
        polylineWriter.SetInputData(polyline)
        polylineWriter.SetFileName(options.outOpeningFileName)

        if writer.Write() != 1:
            if not options.quiet:
                raise IOError("[Error] Write failed...")
            return 1
        else:
            if not options.quiet:
                print "Successful. File written to %s"%(options.outFileName)

            if (options.bufferPDs != None):
                if not options.quiet:
                    print "No drill region supplied, there will not be opening line output!"
            elif polylineWriter.Write() != 1:
                if not options.quiet:
                    raise IOError("[Error] Opening line write failed")
                return 1
            else:
                if not options.quiet:
                    print "Openning line written to %s"%(options.outOpeningFileName)
            return 0
    except IOError, err:
        if not options.quiet:
            print str(err)
        return 2
    except RuntimeError, err:
        if not options.quiet:
            print str(err)
        return 3
    except ValueError, err:
        if not options.quiet:
            print str(err)
        return 4


if __name__ == '__main__':
    exitCode = main(sys.argv)
    exit(exitCode)



