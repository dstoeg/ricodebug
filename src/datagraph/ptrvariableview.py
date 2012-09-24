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

from datagraph.datagraphvw import DataGraphVW, HtmlTemplateHandler
from PyQt4 import QtCore
from PyQt4.QtGui import QWidgetAction, QLineEdit
import logging


class PtrVariableTemplateHandler(HtmlTemplateHandler):
    """ TemplateHandler for Pointer-Variables """

    def __init__(self, varWrapper, distributedObjects):
        """ Constructor
        @param varWrapper    datagraph.datagraphvw.DataGraphVW, holds the Data to show """
        HtmlTemplateHandler.__init__(self, varWrapper, distributedObjects, 'ptrvariableview.mako')

    @QtCore.pyqtSlot()
    def dereference(self):
        dgvw = self.varWrapper.dereference()
        if (dgvw != None):
            logging.debug("dereferenced variable wrapper: new expression is %s", dgvw.exp)
            self.distributedObjects.datagraphController.addVar(dgvw)
            self.distributedObjects.datagraphController.addPointer(self.varWrapper.getView(), dgvw.getView())
        else:
            logging.error("Null-Pointer wasn't dereferenced.")

    @QtCore.pyqtSlot()
    def showCustom(self):
        vw = self.distributedObjects.datagraphController.addWatch(self.showCustomEdit.text())
        self.distributedObjects.datagraphController.addPointer(self.varWrapper.getView(), vw.getView())
        self.showCustomEdit.parent().hide()

    def prepareContextMenu(self, menu):
        HtmlTemplateHandler.prepareContextMenu(self, menu)
        menu.addAction("Dereference %s" % self.varWrapper.exp, self.dereference)
        submenu = menu.addMenu("Show custom...")

        # we cannot construct the lineedit in our ctor since it will be automatically deleted once the menu is closed
        self.showCustomEdit = QLineEdit()
        self.showCustomEdit.returnPressed.connect(self.showCustom)
        self.showCustomEdit.setText("*(%s)" % self.varWrapper.exp)
        we = QWidgetAction(menu)
        we.setDefaultWidget(self.showCustomEdit)
        submenu.addAction(we)


class PtrDataGraphVW(DataGraphVW):
    """ VariableWrapper for Pointer-Variables """

    def __init__(self, variable, distributedObjects, vwFactory):
        """ Constructor
        @param variable            variables.variable.Variable, Variable to wrap with the new DataGraphVW
        @param distributedObjects  distributedobjects.DistributedObjects, the DistributedObjects-Instance
        """
        DataGraphVW.__init__(self, variable, distributedObjects)
        self.factory = vwFactory
        self.templateHandler = PtrVariableTemplateHandler(self, self.distributedObjects)

    def dereference(self):
        """ dereferences the Variable
        @return     datagraph.datagraphvw.DataGraphVW or None,
                    the Wrapper of the dereferenced Variable if the Variable can be dereferenced,
                    None otherwise
        """
        dereferencedVar = self._v.dereference()
        if dereferencedVar is not None:
            return dereferencedVar.makeWrapper(self.factory)
        else:
            return None
