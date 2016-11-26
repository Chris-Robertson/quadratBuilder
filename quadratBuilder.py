# -*- coding: utf-8 -*-
"""
/***************************************************************************
 quadratBuilder
                                 A QGIS plugin
 Creates quadrats of designated size along a line.
                              -------------------
        begin                : 2016-11-22
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Chris Robertson
        email                : chrisxrobertson@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from quadratBuilder_dialog import quadratBuilderDialog
import os.path


class quadratBuilder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'quadratBuilder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

#==============================================================================
# CONSTANTS
#==============================================================================
        self.QUADRAT_LAYER_NAME = "Quadrats"
        self.MSG_BOX_TITLE = "Quadrat Builder"

        
        # Get user entered dimensions
        self.ql = 0
        self.qw = 0

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Quadrat Builder')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'quadratBuilder')
        self.toolbar.setObjectName(u'quadratBuilder')
        

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('quadratBuilder', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

#        # Create the dialog (after translation) and keep reference
        self.dlg = quadratBuilderDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/quadratBuilder/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create Quadrats Along Line'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Quadrat Builder'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        
        # show the dialog
        self.dlg.show()
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            
            # Get user entered values
            self.ql = self.dlg.qLengthInput.value()
            self.qw = self.dlg.qWidthInput.value()
            # Check quadrat dimensions have not been set to 0
            if self.ql <= 0 or self.qw <= 0:
                QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, "Length and width must be greater than zero", QMessageBox.Ok, QMessageBox.Ok)
                # Open dialogue box again
                self.run()

            # Gets the features from user selection
            selectedLayer = self.iface.mapCanvas().currentLayer()
            selectedFeatures = selectedLayer.selectedFeatures()
            #line = QgsGeometry()#.fromWkt('GEOMETRYCOLLECTION EMPTY')
            line = QgsGeometry.fromPolyline([])
            
            for feat in selectedFeatures:
                # Check selected features are lines
                if feat.geometry().wkbType() != QGis.WKBLineString:
                    QMessageBox.warning(self.iface.mainWindow(), self.MSG_BOX_TITLE, "Selected features must be lines", QMessageBox.Ok, QMessageBox.Ok)
                    return                    
                # Combine multiple lines
                line = line.combine(feat.geometry())
            
            # Apply Simplify and Smoothing if checked
            if self.dlg.simplifyCheck:
                line = self.lineSimplify(line)                
            if self.dlg.smoothCheck:
                line = self.lineSmooth(line)
                
            # Get the crs
            crs = selectedLayer.crs()
            
            # Create a memory layer with the selected layer's crs
            memLayer = QgsVectorLayer("Polygon?crs=epsg:" + unicode(crs.postgisSrid()) + "&index=yes&field=name:string(20)&field=sym:string(20)", self.QUADRAT_LAYER_NAME, "memory") #creating fields in advance for GPX export
            
            # Adds memory layer to layer list and turns on editing
            QgsMapLayerRegistry.instance().addMapLayer(memLayer)
            memLayer.startEditing()
            
            # Create a list of new features to pass to the data provider
            quadrats = []
            
            start = 0
            quadrats.extend(self.handle_line(start, float(self.ql), line))
            
#            quadrats = quadrats.splitQuadrats(quadrats, line)
            
            # Add features to memory layer
            provider = memLayer.dataProvider()
            provider.addFeatures(quadrats)
            
            # Refresh the canvas
            # If caching is enabled, a simple canvas refresh might not be sufficient
            # to trigger a redraw and you must clear the cached image for the layer
            if self.iface.mapCanvas().isCachingEnabled():
                selectedLayer.setCacheImage(None)
            else:
                self.iface.mapCanvas().refresh()
            
    def handle_line(self, start, quadratLength, line):
        '''Creates quadrats along the line
        '''
        length = line.length()
        distanceAlongLine = start
#        if 0 < end <= length:
#            length = end
        # array with all generated features
        feats = []
        while distanceAlongLine <= length:
            # Create a new QgsFeature and assign it the new geometry
            
            newQuadrat = self.createQuadrat(line, distanceAlongLine, quadratLength)
            print("newQuadrat")
            print(newQuadrat)
            for i in range(len(newQuadrat)):
                if newQuadrat[i] is not None:
                    newFeature = QgsFeature()
                    newFeature.setGeometry(newQuadrat[i])
                    feats.append(newFeature)
            # Increase the distance
            distanceAlongLine += quadratLength
        return feats
    
    def createQuadrat(self, line, distanceAlongLine, quadratLength):
        ''' Creates quadrats along line by making a temp line for the length of the quadrat and
            applying a buffer to it.
            
            Borrowed quite heavily from https://github.com/rduivenvoorde/featuregridcreator
        '''
        # Get current point along line
        startPoint = line.interpolate(distanceAlongLine)
        # Get point that will be the end of this quadrat
        endPoint = line.interpolate(distanceAlongLine + quadratLength)
        
        tempLine = QgsGeometry.fromPolyline([startPoint.asPoint(), endPoint.asPoint()])
        
        segment1 = line.closestSegmentWithContext(startPoint.asPoint())
        segment2 = line.closestSegmentWithContext(endPoint.asPoint())
        ii = 1
        for i in range(segment1[2], segment2[2]):
            #new_vertex = line_geom.vertexAt(segment_context[2])
            new_vertex = line.vertexAt(i)
            tempLine.insertVertex(new_vertex.x(), new_vertex.y(), ii)
            ii += 1
        
        quadrat = tempLine.buffer(self.qw, 12, 2, 0, 1)
        quadrat = self.splitQuadrat(quadrat, tempLine)
#        quadrat.splitGeometry(quadrat.asPolygon(), tempLine)
        
        return quadrat
        
    def lineSmooth(self, line):
        ''' Takes a line geometry and applies smooth
        '''
        # Get parameter values from the dialogue
        iterations = self.dlg.smoothIterations.value()
        offset = self.dlg.smoothOffset.value()
        minDist = self.dlg.smoothMinDist.value()
        maxAngle = self.dlg.smoothMaxAngle.value()
        
        # For some reason, smooth() throws a "Too many arguments" Type Error when passed more than 2 pararmeters
        # It still uses the four parameters though...
        # This try...catch works around the issue
        try:
            line = line.smooth(iterations, offset, minDist, maxAngle)
        except TypeError:
            pass
        
        return line

    def lineSimplify(self, line):
        ''' Takes a line geometry and applies smoothing
        '''
        # Get parameter values from the dialogue
        tolerance = self.dlg.simpleTolerance.value()
        
        return line.simplify(tolerance)
    
    def splitQuadrat(self, quadrat, line):
        ''' Takes a polygon and a line
            Splits the polygon with the line
        '''
        # Split the quadrat
#        splitQuadratFirstHalf = quadrat.splitGeometry(line.asPolyline(), True) # true if topological editing is enabled
        splitQuadratHalf_1 = quadrat.reshapeGeometry(line.asPolyline())
        return splitQuadratHalf_1
                
#==============================================================================
#     def create_point_or_trench_on_line(self, line, distance, interval):
#         # Get a point on the line at current distance
#         geom = line.interpolate(distance)  # interpolate returns a QgsGeometry
#         # trench width and length in meters
#         w = self.qw
#         l = self.ql
#         x1 = geom.asPoint().x()
#         y1 = geom.asPoint().y()
#         # a non rotated trench
#         #return QgsGeometry.fromRect(QgsRectangle(x1-l, y1-w, x1+l, y1+w))
#         # a trench in the direction of the line
#         geom2 = line.interpolate(distance + l)  # interpolate returns a QgsGeometry-point
#         vertices = [geom.asPoint()]
#         # BUT check if there are vertices on this line_geom in between
#         # see if there are vertices on the path here...
#         vertices.append(geom2.asPoint())
#         newLine = QgsGeometry.fromPolyline(vertices)
#         # checking if length of the generated line is as requested
#         # if the difference is more then 1 cm (comparing floats....)
#         # we either do NOT add it, or generate rounded caps
#         #if (int(l) - int(line.length())) > 1.0:
#             # buffer(distance, segments, endcapstyle, joinstyle, mitrelimit)
#             # endcap 2 = flat
#             # join 1 = round
#             #trench = line.buffer(w/2, 4, 1, 1, 1)
#             #trench = None
#             # print line_geom.touches(geom2)  # true
#             # line.closestSegmentWithContext(point, minDistPoint, afterVertex, 0, 0.00000001)
#             # returns a segmentWithContext like: (0.0, (104642,490373), 2)
#             # being: distance, point, segmentAfter
#         segment_context = line.closestSegmentWithContext(geom.asPoint())
#         segment_context2 = line.closestSegmentWithContext(geom2.asPoint())
#         ii = 1
#         for i in range(segment_context[2], segment_context2[2]):
#             #new_vertex = line_geom.vertexAt(segment_context[2])
#             new_vertex = line.vertexAt(i)
#             newLine.insertVertex(new_vertex.x(), new_vertex.y(), ii)
#             ii += 1
#         trench = line.buffer(w, 0, 2, 1, 1)
#         # trench = line.buffer(w/2, 1, 1, 1, 1) # 'round' endcap
#         return trench#, self.RESULT_FEATURE_TRENCH_BENDED_OR_SHORT  # 2 meaning this is not a straight trench (a bended one)
#==============================================================================
#        else:
#            # buffer(distance, segments, endcapstyle, joinstyle, mitrelimit)
#            # endcap 2 = flat
#            # join 1 = round
#            trench = line.singleSidedBuffer(w, 0, SideLeft, 1, 1)
#            return trench#, self.RESULT_FEATURE_TRENCH_STRAIGHT  # 1 meaning a straigh trench
#            else:
#                # a line with points
#                return geom, self.RESULT_FEATURE_POINT  # 0 meaning a point
        
            # Clean up after everything is done
#            selectedLayer.removeSelection()
            
#==============================================================================
# GPX
# uri = "path/to/gpx/file.gpx?type=track"
# vlayer = QgsVectorLayer(uri, "layer name you like", "gpx")
#==============================================================================
#==============================================================================
# # If caching is enabled, a simple canvas refresh might not be sufficient
# # to trigger a redraw and you must clear the cached image for the layer
# if iface.mapCanvas().isCachingEnabled():
#     layer.setCacheImage(None)
# else:
#     iface.mapCanvas().refresh()
#==============================================================================
#==============================================================================
# Symbol Renderer
# # http://snorf.net/blog/2014/03/04/symbology-of-vector-layers-in-qgis-python-plugins/
# # Categorized symbol renderer for different type of grid features: points, straight trench and bended or stort trench
# # define a lookup: value -> (color, label)
# ftype = {
#     '0': ('#00f', self.tr('hole')),
# }
# if self.feature_type() == self.TRENCH_FEATURES:
#     ftype = {
#         '1': ('#00f', self.tr('trench straight')),
#         '2': ('#f00', self.tr('trench bend or short')),
#         #'': ('#000', 'Unknown'),
#     }
# # create a category for each
# categories = []
# for feature_type, (color, label) in ftype.items():
#     symbol = QgsSymbolV2.defaultSymbol(memory_lyr.geometryType())
#     symbol.setColor(QColor(color))
#     category = QgsRendererCategoryV2(feature_type, symbol, label)
#     categories.append(category)
# # create the renderer and assign it to a layer
# expression = 'ftype'  # field name
# renderer = QgsCategorizedSymbolRendererV2(expression, categories)
# memory_lyr.setRendererV2(renderer)
#==============================================================================
    



















