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
import logging

"""@package breakpointmodel
    there are some classes in this package:\n
    * BpInfo: a simple class that provides all really necessary information to select a breakpoint\n
    * ExtendedBreakpoint:     gdb breakpoints has some information like filename, line, ...
                            for special functionality there have to be more information like
                            name, condition, skip, ... This class extends the gdb breakpoints with
                            this informations\n

    * BreakpointModel: the model for breakpoints
"""

from PyQt4.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant, QObject
from operator import attrgetter


class ExtendedBreakpoint(QObject):
    """This class provides all members for basic gdb Breakpoint and extends it with
    more members like condition, name and interval.
    """
    def __init__(self, breakPoint, counter, connector):
        """Initializes the Object.
        The breakPoint comes from gdb. Here it will be extended.
        @param breakPoint: type is a struct, provided from gdb, then parsed
        @param counter: type is integer, every breakpoint becomes a initial name
        \"Point<nr>\", nr is the counter value
        @param connector: type is GdbConnector, needed to communicate with gdb
        @note     there is a special case when creating breakpoints. for example if
                a breakpoint is set on end of a \"if{}\" and the \"}\" is the one
                and only symbol in this line it is possible that gdb returns a
                \"<MULTIPL>\" breakpoint address. in that case it is necessary to
                ask gdb via usual interface (not mi interface) for breakpoint information.
                parsing this information the address can be figured out.
        """

        QObject.__init__(self)

        self.gdbConnector = connector
        self.file = None
        self.fullname = None
        self.func = None
        self.line = -1

        self.addr = None
        self.disp = None
        self.enabled = None
        self.numer = None
        self.original_location = None
        self.times = None
        self.type = None
        self.name = None
        self.condition = None
        self.skip = None

        if (breakPoint != None):
            self.addr = breakPoint.addr
            self.disp = breakPoint.disp
            self.enabled = breakPoint.enabled
            self.number = breakPoint.number
            self.originalLocation = breakPoint.__dict__['original-location']
            self.times = breakPoint.times
            self.type = breakPoint.type
            self.name = "Point " + str(counter)
            self.condition = "true"
            self.skip = 0

            """ proof if it is a special multiple address breakpoint"""
            if breakPoint.addr == "<MULTIPLE>":
                """ start special handling"""
                self.multipleBreakPointInit(breakPoint.number)
                self.parseOriginalLocation(breakPoint.__dict__['original-location'])
                self.func = "unknown"
            else:
                self.file = getattr(breakPoint, "file", "<unknown>")
                self.fullname = getattr(breakPoint, "fullname", "<unknown>")
                self.func = getattr(breakPoint, "func", None)
                if not self.func:
                    self.func = getattr(breakPoint, "at", None)
                self.line = getattr(breakPoint, "line", "-1")

        if not self.func:
            self.func = "unknown"

    def parseOriginalLocation(self, origLoc):
        """ needed for special case of breakpoints <MULTIPLE> address"""
        origLoc = origLoc.split(':')
        self.fullname = origLoc[0]
        self.line = origLoc[1]
        origLoc = origLoc[0].split('/')
        self.file = origLoc[len(origLoc[0]) - 1]

    def multipleBreakPointInit(self, breakPointNumber):
        """ needed for special case of breakpoints <MULTIPLE> address"""
        self.gdbConnector.getMultipleBreakpoints(breakPointNumber)


class BreakpointModel(QAbstractTableModel):
    """ Class provides the breakpointModel for breakpointView """
    def __init__(self, do, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.breakpoints = []
        self.connector = do.gdb_connector
        do.signalProxy.cleanupModels.connect(self.clearBreakpoints)
        do.signalProxy.emitRegisterWithSessionManager(self, "Breakpoints")

    def getBreakpoints(self):
        return self.breakpoints

    def toggleBreakpoint(self, fullname, line):
        """ toggles the breakpoint in file fullname with linenumber line
        @param fullname: (string), fullname of file
        @param line: (int), linenumber where the breakpoint should be toggled
        """
        if self.isBreakpointByLocation(fullname, line):
            self.deleteBreakpoint(fullname, line)
            return -1
        else:
            return self.insertBreakpoint(fullname, line)

    def isBreakpointByLocation(self, fullname, line):
        """ search for breakpoint in file fullname on linenumber line
        @param fullname: (string), name of file
        @param line: (int), number of line
        @return: (bool), True if breakpoint found in list, False else
        """
        for bp in self.breakpoints:
            if int(bp.line) == line and bp.fullname == fullname:
                return True
        return False

    def isBreakpointByNumber(self, number):
        """ search for breakpoint in file bpInfo.fullname on line bpInfo.line
        @param number: (int), gdb's internal breakpoint number
        @return: (bool), True if can find breakpoint in list, False else
        """
        for bp in self.breakpoints:
            if int(bp.number) == number:
                return True
        return False

    def clearBreakpoints(self):
        """ deletes all breakpoints in list """
        # we need to store the numbers in a separate list since self.breakpoints
        # will be modified in the loop
        numbers = [bp.number for bp in self.breakpoints]
        for number in numbers:
            # delete breakpoints by number to avoid problems where the bp's file
            # name is unknown
            self.deleteBreakpointByNumber(number)

    def insertBreakpoint(self, file_, line):
        """ inserts a breakpoint in file file_ on linenumber line
        @param file_: (string), name of file
        @param line: (int), number of line
        @return (int), returns the real linenumber that gdb is choosing
        """
        res = self.connector.insertBreakpoint(file_, line)
        extendedBreakpoint = ExtendedBreakpoint(res.bkpt, len(self.breakpoints), self.connector)

        self.beginInsertRows(QModelIndex(), len(self.breakpoints), len(self.breakpoints))
        self.breakpoints.append(extendedBreakpoint)
        self.endInsertRows()

        return int(extendedBreakpoint.line)

    def deleteBreakpoint(self, file_, line):
        """ deletes breakpoint in file file_ on linenumber line
        @param file_: (string), name of file
        @param line: (int), number of line
        """
        for bp in self.breakpoints:
            if bp.fullname == file_ and int(bp.line) == int(line):
                self.deleteBreakpointByNumber(bp.number)
                return
        else:
            logging.error("Cannot delete breakpoint (%s:%s) that is not in the model!", file_, line)

    def deleteBreakpointByNumber(self, number):
        """ deletes a breakpoint with a given number
        @param number: (int), number of the breakpoint to delete
        """
        for i, bp in enumerate(self.breakpoints):
            if bp.number == number:
                break
        else:
            logging.error("Cannot delete breakpoint (#%s) that is not in the model!", number)
            return

        self.connector.deleteBreakpoint(number)
        self.beginRemoveRows(QModelIndex(), i, i)
        self.breakpoints.remove(bp)
        self.endRemoveRows()

    def enableBreakpoint(self, number):
        """ enable breakpoint with number number
        @param number: (int), the number of breakpoint that should be enabled"""
        self.connector.enableBreakpoint(number)

    def disableBreakpoint(self, number):
        """ disable breakpoint with number number
        @param number: (int), the number of breakpoint that should be disabled"""
        self.connector.disableBreakpoint(number)

    def changeCondition(self, number, condition):
        """ sets a condition condition to the specified breakpoint with number number
        @param number: (int), the number of breakpoint that should be enabled
        @param condition: (string), a condition like "var == 2" """
        self.connector.setConditionBreakpoint(number, condition)

    def changeSkip(self, number, skip):
        """ gdb will skip the breakpoint number number skip times
        @param number: (int), the number of breakpoint that should be enabled
        @param skip: (int), specifies how often breakpoint should be skipped"""
        self.connector.setSkipBreakpoint(number, skip)

    def rowCount(self, parent):
        return len(self.breakpoints)

    def columnCount(self, parent):
        return 9

    def data(self, index, role):
        assert(index.row() < len(self.breakpoints))

        ret = None

        bp = self.breakpoints[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == 0:
                ret = bp.file
            elif index.column() == 1:
                ret = bp.line
            elif index.column() == 2:
                ret = bp.fullname
            elif index.column() == 3:
                ret = bp.number
            elif index.column() == 5:
                ret = bp.addr
            elif index.column() == 6:
                ret = bp.condition
            elif index.column() == 7:
                ret = bp.skip
            elif index.column() == 8:
                ret = bp.name
        elif role == Qt.CheckStateRole:
            if index.column() == 4:
                ret = Qt.Checked if bp.enabled == 'y' else Qt.Unchecked

        return ret

    def headerData(self, section, orientation, role):
        ret = None

        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    ret = "File"
                elif section == 1:
                    ret = "Line"
                elif section == 2:
                    ret = "Full name"
                elif section == 3:
                    ret = "Number"
                elif section == 4:
                    ret = "Enabled"
                elif section == 5:
                    ret = "Address"
                elif section == 6:
                    ret = "Condition"
                elif section == 7:
                    ret = "Skip"
                elif section == 8:
                    ret = "Name"
        return ret

    def sort(self, column, order):
        if order == Qt.AscendingOrder:
            rev = False
        else:
            rev = True

        if column == 0:
            key = 'file'
        elif column == 1:
            key = 'line'
        elif column == 2:
            key = 'fullname'
        elif column == 3:
            key = 'number'
        elif column == 4:
            key = 'enabled'
        elif column == 5:
            key = 'addr'
        elif column == 6:
            key = 'condition'
        elif column == 7:
            key = 'skip'
        elif column == 8:
            key = 'name'

        self.beginResetModel()
        self.breakpoints.sort(key=attrgetter(key), reverse=rev)
        self.endResetModel()

    def flags(self, index):
        f = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        if index.column() == 0:
            pass
        elif index.column() == 1:
            pass
        elif index.column() == 2:
            pass
        elif index.column() == 3:
            pass
        elif index.column() == 4:
            f |= Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        elif index.column() == 5:
            pass
        elif index.column() == 6:
            f |= Qt.ItemIsEnabled | Qt.ItemIsEditable
        elif index.column() == 7:
            f |= Qt.ItemIsEnabled | Qt.ItemIsEditable
        elif index.column() == 8:
            f |= Qt.ItemIsEnabled | Qt.ItemIsEditable

        return f

    def setData(self, index, value, role):
        bp = self.breakpoints[index.row()]

        #"""index.column() == 6 -> condition"""
        if index.column() == 6:
            try:
                bp.condition = str(value.toString())
                self.changeCondition(bp.number, bp.condition)
            except:
                logging.error("setData: data type missmatch bp.condition is str and value is not")
                return False

        #"""index.column() == 7 -> skip"""
        elif index.column() == 7:
            validSkip = QVariant(value).toInt()
            if not validSkip[1]:
                logging.error("setData: value from user is not int")
                return False
            bp.skip = int(validSkip[0])
            self.changeSkip(bp.number, str(bp.skip))

        #"""index.column() == 4 -> enabled"""
        elif index.column() == 4:
            if role == Qt.CheckStateRole:
                # breakpoint is active, set inactive
                if not QVariant(value).toBool():
                    bp.enabled = 'n'
                    self.disableBreakpoint(bp.number)
                # breakpoint is inactive, set active
                else:
                    bp.enabled = 'y'
                    self.enableBreakpoint(bp.number)

        elif index.column() == 8:
            bp.name = str(value.toString())

        return True

    def saveSession(self, xmlHandler):
        """Insert session info to xml file"""
        bpparent = xmlHandler.createNode("Breakpoints")
        for bp in self.getBreakpoints():
            xmlHandler.createNode("Breakpoint", bpparent, {"file": bp.file, "line": bp.line})

    def loadSession(self, xmlHandler):
        """load session info to xml file"""
        bpparent = xmlHandler.getNode("Breakpoints")
        if bpparent != None:
            childnodes = bpparent.childNodes()
            for i in range(childnodes.size()):
                attr = xmlHandler.getAttributes(childnodes.at(i))
                self.insertBreakpoint(attr["file"], attr["line"])
