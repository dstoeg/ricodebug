# ricodebug - A GDB frontend which focuses on visually supported
# debugging using data structure graphs and SystemC features.
#
# Copyright (C) 2011  The ricodebug project team at the
# Upper Austrian University Of Applied Sciences Hagenberg,
# Department Embedded Systems Design
#
# This file is part of ricodebug.
#
# ricodebug is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further information see <http://syscdbg.hagenberg.servus.at/>.

from PyQt4.QtCore import Qt, QAbstractTableModel, QObject, QModelIndex
#from PyQt4 import QtGui
from operator import attrgetter
from helpers.svgdrawwaveforms import SvgDrawWaveform
from datagraph.SVGImage import SVGImage
from datagraph.svgview import SVGDataGraphVW
from StringIO import StringIO
import traceback
import logging

class TracepointWaveDrawing(QObject):

    def __init__(self, distributedObjects):
        self.distributedObjects = distributedObjects
        self.f = StringIO("")

        # Datagraph image
        self.svg_image = SVGImage("Tracepoint", self.f)
        self.svg_image_wrapper = SVGDataGraphVW(self.svg_image, self.distributedObjects)

        # Drawing library
        self.svg = SvgDrawWaveform(self.f, 0, 0, "int")

        self.action = self.distributedObjects.actions.\
            getAddSVGToDatagraphAction(self.svg_image_wrapper,
                                       self.distributedObjects.
                                       datagraphController.addSVG)


    def refresh(self, no_waves):
        self.svg.refresh(no_waves)

    def display(self):
        self.f.seek(0)
        self.svg.finish()

    def __del__(self):
        self.f.close()


class TracepointWaveModel(QAbstractTableModel):
    """TableModel for TracepointWaveView.
    Holds a list of TracepointWaveGraphicsViews.
    Every TracepointWaveGraphicsView holds a TracepointWaveScene
    which represents a waveform.
    """

    def __init__(self, distributedObjects):
        QAbstractTableModel.__init__(self)
        
        self.supportedTypes = ["bool", "int", "float", "double"]
        self.distributedObjects = distributedObjects
        self.waveform = TracepointWaveDrawing(distributedObjects)

        # each TracepointWaveGraphicsView in list holds one TracepointWaveScene
        self.waveforms = []

        # factor for zoom in/out functions
        self.zoomfactor = 1.05

        # stepwidth
        self.duration = 30

        # const column of waveform
        self.wavecolumn = 1
        
        self.distributedObjects.signalProxy.\
            cleanupModels.connect(self.cleanUp)

    def cleanUp(self):
        pass

    def updateTracepointWave(self, list_):
        ''' Repaint tracepoint waves
            @param list_: list of ValueList objects
        '''
        # TODO: write log message
        if len(list_) == 0:
            return 

        self.waveform.refresh(len(list_))
        
        for item in list_:
            if item.type in self.supportedTypes:
                i = self.__getTracepointWaveIndex(item.name, item.type)

                for v in item.values:
                    self.waveform.svg.drawWaveform(i, v, item.type, item.name)
        
                if i is not None:
                    self.waveform.svg_image_wrapper.setDirty(True) # render immediatly
                else:
                    self.waveform.action.commit()
                    self.waveforms.append({"name" : item.name,
                                           "type" : item.type})
            else:
                logging.error("Could not update tracepoint wave. Illegal variable type.")
                    
        self.waveform.display()



    def __getTracepointWaveIndex(self, name, type_):
        for wf in self.waveforms:
            if wf["name"] == name and wf["type"] == type_:
                return self.waveforms.index(wf)
        return None

    def zoomIn(self):
        '''Zoom wave horizontally'''
        self.duration = self.duration * self.zoomfactor

    def zoomOut(self):
        '''Zoom wave horizontally'''
        self.duration = self.duration / self.zoomfactor

    def data(self, index, role):
        ret = None
        if(index.row() < len(self.waveforms)):
            wave = self.waveforms[index.row()]
            if role == Qt.DisplayRole:
                if index.column() == 0:
                    ret = wave.getName()
                elif index.column() == self.wavecolumn:
                    ret = wave
            elif role == Qt.EditRole:
                if index.column() == self.wavecolumn:
                    ret = wave
        return ret

    def sort(self, column, order):
        if order == Qt.AscendingOrder:
            rev = False
        else:
            rev = True

        if column == 0:
            key = 'name'
            self.beginResetModel()
            self.waveforms.sort(key=attrgetter(key), reverse=rev)
            self.endResetModel()
            self.orderChanged.emit()

    def headerData(self, section, orientation, role):
        ret = None
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    ret = "Variable"
                if section == self.wavecolumn:
                    ret = "Wave"
        return ret


    
    
    
    

