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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
from qgis.core import *
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
                
        
#        self.ql = 0
#        self.qw = 0
        
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

        # Create the dialog (after translation) and keep reference
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
        
        # Clear selection drop down when dialogue pops
        self.dlg.lineSelect.clear()

        # Get all layers
        layers = QgsMapLayerRegistry.instance()
        
        # Put layers in the dropdown box
        layer_list = []
        print("Adding layers to dropdown...")
        for layer in layers.mapLayers().values():
            layer_list.append(layer.name())
            print("Added layer: " + layer.name())
        self.dlg.lineSelect.addItems(sorted(layer_list))
        
        # show the dialog
        self.dlg.show()
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            
            # Get user entered dimensions
            #TODO check for int
            self.ql = self.dlg.qLengthInput.text()
            self.qw = self.dlg.qWidthInput.text()
            
            # Selects the layer selected in the dropdown
            selectedLayerName = self.dlg.lineSelect.currentText()
            selectedLayer = layers.mapLayersByName(selectedLayerName)[0]
            selectedLayer.selectAll()
            print("Selected layer: " + str(selectedLayer.name()))
            print(selectedLayer.wkbType())
            print(type(selectedLayer))
            print(str(selectedLayer.dataProvider()))
            
            # Get all features from selected layer and iterate through them
            #TODO Check the number of features, warn if more than one
            features = selectedLayer.getFeatures()
            print(str(selectedLayer.name()) + " features loaded...")
            for feature in features:
                print("Feature added: ID%d" % feature.id())
                print(type(feature))
                
                # Gets the geometry of the feature
                geom = feature.geometry()
                print("Geometry:")
                print(geom.wkbType())
                print(type(geom))
                print(geom.asPolyline())
                
                # Bounding box will give the start and end points of a line
                bbox = geom.boundingBox()
                print("Bounding box:")
                print(bbox.toString())
            
            # Get the crs
            crs = selectedLayer.crs()
            print("CRS: " + str(crs.description()))
            
            # Create a memory layer with the selected layer's crs
            memLayer = QgsVectorLayer("Polygon?crs=epsg:" + unicode(crs.postgisSrid()) + "&index=yes&field=name:string(20)&field=sym:string(20)", self.QUADRAT_LAYER_NAME, "memory") #creating fields in advance for GPX export
            
            # Adds memory layer to layer list and turns on editing
            QgsMapLayerRegistry.instance().addMapLayer(memLayer)
            memLayer.startEditing()
            
            # Clean up after everything is done
            selectedLayer.removeSelection()
            
#==============================================================================
#             GPX
#             uri = "path/to/gpx/file.gpx?type=track"
#             vlayer = QgsVectorLayer(uri, "layer name you like", "gpx")
#==============================================================================
            



















