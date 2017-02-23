from PyQt5.QtCore import QEvent, QLocale, QRegularExpression, QSize, Qt
from PyQt5.QtGui import QColor, QRegularExpressionValidator
from PyQt5.QtWidgets import (
    QApplication, QDoubleSpinBox, QGridLayout, QHeaderView, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)
from defconQt.controls.accordionBox import AccordionBox
from defconQt.controls.colorVignette import ColorVignette
from defconQt.controls.listView import ListView
from defconQt.tools.drawing import colorToQColor
from trufont.controls.glyphAlignmentWidget import GlyphAlignmentWidget
from trufont.objects import icons
from trufont.tools.colorGenerator import ColorGenerator
# TODO: switch to QFormLayout
from trufont.tools.rlabel import RLabel


def PushButton(parent=None):
    btn = QPushButton(parent)
    btn.setFlat(True)
    btn.setFocusPolicy(Qt.NoFocus)
    btn.setIconSize(QSize(20, 20))
    return btn


class SpinBox(QDoubleSpinBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        self.setDecimals(3)

    def keyPressEvent(self, event):
        key_ = None
        if event.modifiers() & Qt.ShiftModifier:
            key = event.key()
            preDelta = None
            if key == Qt.Key_Up:
                key_ = Qt.Key_PageUp
                preDelta = 90
            elif key == Qt.Key_Down:
                key_ = Qt.Key_PageDown
                preDelta = -90
            if preDelta and event.modifiers() & Qt.ControlModifier:
                self.stepBy(preDelta)
        if key_ is not None:
            event = event.__class__(
                event.type(), key_, event.modifiers(), "",
                event.isAutoRepeat(), event.count())
        oldValue = self.value()
        super().keyPressEvent(event)
        if self.value() != oldValue:
            self.editingFinished.emit()

    def setValue(self, value):
        if value is None:
            self.clear()
            return
        super().setValue(value)

    def textFromValue(self, value):
        decimalPoint = QLocale().decimalPoint()
        if value.is_integer():
            return str(int(value))
        else:
            return str(value).replace(".", decimalPoint)


class NumberBox(SpinBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignLeft)
        self.setButtonSymbols(QSpinBox.NoButtons)
        # TODO: MAX_INT?
        self.setRange(-900000, 900000)


class PropertiesWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        self._font = None
        self._glyph = None
        self._shouldEditLastName = False

        glyphGroup = AccordionBox(self.tr("Glyph"), self)
        glyphLayout = QGridLayout(self)
        columnOneWidth = self.fontMetrics().width('0') * 7

        nameLabel = RLabel(self.tr("Name:"), self)
        self.nameEdit = QLineEdit(self)
        self.nameEdit.editingFinished.connect(self.writeGlyphName)
        unicodesLabel = RLabel(self.tr("Unicode:"), self)
        self.unicodesEdit = QLineEdit(self)
        self.unicodesEdit.editingFinished.connect(self.writeUnicodes)
        unicodesRegExp = QRegularExpression(
            "(|([a-fA-F0-9]{4,6})( ([a-fA-F0-9]{4,6}))*)")
        unicodesValidator = QRegularExpressionValidator(unicodesRegExp, self)
        self.unicodesEdit.setValidator(unicodesValidator)
        widthLabel = RLabel(self.tr("Width:"), self)
        self.widthEdit = NumberBox(self)
        self.widthEdit.setMaximumWidth(columnOneWidth)
        self.widthEdit.editingFinished.connect(self.writeWidth)
        leftMarginLabel = RLabel(self.tr("Left:"), self)
        self.leftMarginEdit = NumberBox(self)
        self.leftMarginEdit.setMaximumWidth(columnOneWidth)
        self.leftMarginEdit.editingFinished.connect(
            self.writeleftMargin)
        rightMarginLabel = RLabel(self.tr("Right:"), self)
        self.rightMarginEdit = NumberBox(self)
        self.rightMarginEdit.setMaximumWidth(columnOneWidth)
        self.rightMarginEdit.editingFinished.connect(
            self.writerightMargin)
        markColorLabel = RLabel(self.tr("Flag:"), self)
        self.markColorWidget = ColorVignette(self)
        self.markColorWidget.colorChanged.connect(
            self.writeMarkColor)
        self.markColorWidget.setMaximumWidth(columnOneWidth)

        l = 0
        glyphLayout.addWidget(nameLabel, l, 0)
        glyphLayout.addWidget(self.nameEdit, l, 1, 1, 5)
        l += 1
        glyphLayout.addWidget(unicodesLabel, l, 0)
        glyphLayout.addWidget(self.unicodesEdit, l, 1, 1, 5)
        l += 1
        glyphLayout.addWidget(widthLabel, l, 0)
        glyphLayout.addWidget(self.widthEdit, l, 1)
        l += 1
        glyphLayout.addWidget(leftMarginLabel, l, 0)
        glyphLayout.addWidget(self.leftMarginEdit, l, 1)
        glyphLayout.addWidget(rightMarginLabel, l, 2)
        glyphLayout.addWidget(self.rightMarginEdit, l, 3)
        l += 1
        glyphLayout.addWidget(markColorLabel, l, 0)
        glyphLayout.addWidget(self.markColorWidget, l, 1)
        glyphGroup.setLayout(glyphLayout)

        transformGroup = AccordionBox(self.tr("Transform"), self)
        transformLayout = QGridLayout(self)

        self.alignmentWidget = GlyphAlignmentWidget(self)

        # TODO: should this be implemented for partial selection?
        invScaleButton = PushButton(self)
        invScaleButton.setToolTip(
            self.tr("Scale down selection"))
        invScaleButton.clicked.connect(self.scaleGlyph)
        invScaleButton.setProperty("inverted", True)
        invScaleButton.setIcon(icons.icon("i_invscale"))
        self.scaleXEdit = SpinBox(self)
        self.scaleXEdit.setSuffix(" %")
        self.scaleXEdit.setMaximum(500)
        self.scaleXEdit.setMinimum(-500)
        self.scaleXEdit.setValue(2)
        scaleButton = PushButton(self)
        scaleButton.setToolTip(
            self.tr("Scale up selection"))
        scaleButton.clicked.connect(self.scaleGlyph)
        scaleButton.setIcon(icons.icon("i_scale"))
        self.scaleYEdit = SpinBox(self)
        self.scaleYEdit.setSuffix(" %")
        self.scaleYEdit.setMaximum(500)
        self.scaleYEdit.setMinimum(-500)
        self.scaleYEdit.setValue(2)

        rotateButton = PushButton(self)
        rotateButton.setToolTip(
            self.tr("Rotate selection counter-clockwise"))
        rotateButton.clicked.connect(self.rotateGlyph)
        rotateButton.setIcon(icons.icon("i_rotate"))
        self.rotateEdit = SpinBox(self)
        self.rotateEdit.setSuffix("º")
        # XXX: calling stepDown() from zero shows 359.999
        self.rotateEdit.setMaximum(359.999)
        self.rotateEdit.setValue(40)
        self.rotateEdit.setWrapping(True)
        invRotateButton = PushButton(self)
        invRotateButton.setToolTip(
            self.tr("Rotate selection clockwise"))
        invRotateButton.clicked.connect(self.rotateGlyph)
        invRotateButton.setProperty("inverted", True)
        invRotateButton.setIcon(icons.icon("i_invrotate"))

        invSkewButton = PushButton(self)
        invSkewButton.setToolTip(
            self.tr("Skew selection counter-clockwise"))
        invSkewButton.clicked.connect(self.skewGlyph)
        invSkewButton.setProperty("inverted", True)
        invSkewButton.setIcon(icons.icon("i_invskew"))
        self.skewEdit = SpinBox(self)
        self.skewEdit.setSuffix("º")
        self.skewEdit.setMaximum(100)
        self.skewEdit.setValue(6)
        self.skewEdit.setWrapping(True)
        skewButton = PushButton(self)
        skewButton.setToolTip(
            self.tr("Skew selection clockwise"))
        skewButton.clicked.connect(self.skewGlyph)
        skewButton.setIcon(icons.icon("i_skew"))

        snapButton = PushButton(self)
        snapButton.setToolTip(
            self.tr("Snap selection to precision"))
        snapButton.clicked.connect(self.snapGlyph)
        snapButton.setIcon(icons.icon("i_snap"))
        self.snapEdit = SpinBox(self)
        self.snapEdit.setValue(1)

        unionButton = PushButton(self)
        unionButton.setToolTip(
            self.tr("Remove selection overlap"))
        unionButton.clicked.connect(self.union)
        unionButton.setIcon(icons.icon("i_union"))
        subtractButton = PushButton(self)
        subtractButton.setToolTip(
            self.tr("Subtract selected or top contour"))
        subtractButton.clicked.connect(self.subtract)
        subtractButton.setIcon(icons.icon("i_subtract"))
        intersectButton = PushButton(self)
        intersectButton.setToolTip(
            self.tr("Intersect selected or top contour"))
        intersectButton.clicked.connect(self.intersect)
        intersectButton.setIcon(icons.icon("i_intersect"))
        xorButton = PushButton(self)
        xorButton.setToolTip(
            self.tr("Xor selected or top contour"))
        xorButton.clicked.connect(self.xor)
        xorButton.setIcon(icons.icon("i_xor"))
        hMirrorButton = PushButton()
        hMirrorButton.setToolTip(
            self.tr("Mirror selection horizontally"))
        hMirrorButton.clicked.connect(self.hMirror)
        hMirrorButton.setIcon(icons.icon("i_hmirror"))
        vMirrorButton = PushButton()
        vMirrorButton.setToolTip(
            self.tr("Mirror selection vertically"))
        vMirrorButton.clicked.connect(self.vMirror)
        vMirrorButton.setIcon(icons.icon("i_vmirror"))

        alignHLeftButton = PushButton(self)
        alignHLeftButton.setToolTip(
            self.tr("Push selection left"))
        alignHLeftButton.clicked.connect(self.alignHLeft)
        alignHLeftButton.setIcon(icons.icon("i_alignhleft"))
        alignHCenterButton = PushButton(self)
        alignHCenterButton.setToolTip(
            self.tr("Push selection to horizontal center"))
        alignHCenterButton.clicked.connect(self.alignHCenter)
        alignHCenterButton.setIcon(icons.icon("i_alignhcenter"))
        alignHRightButton = PushButton(self)
        alignHRightButton.setToolTip(
            self.tr("Push selection right"))
        alignHRightButton.clicked.connect(self.alignHRight)
        alignHRightButton.setIcon(icons.icon("i_alignhright"))
        alignVTopButton = PushButton(self)
        alignVTopButton.setToolTip(
            self.tr("Push selection top"))
        alignVTopButton.clicked.connect(self.alignVTop)
        alignVTopButton.setIcon(icons.icon("i_alignvtop"))
        alignVCenterButton = PushButton(self)
        alignVCenterButton.setToolTip(
            self.tr("Push selection to vertical center"))
        alignVCenterButton.clicked.connect(self.alignVCenter)
        alignVCenterButton.setIcon(icons.icon("i_alignvcenter"))
        alignVBottomButton = PushButton(self)
        alignVBottomButton.setToolTip(
            self.tr("Push selection bottom"))
        alignVBottomButton.clicked.connect(self.alignVBottom)
        alignVBottomButton.setIcon(icons.icon("i_alignvbottom"))

        buttonsLayout = QGridLayout()
        buttonsLayout.setSpacing(0)
        l = 0
        buttonsLayout.addWidget(unionButton, l, 0)
        buttonsLayout.addWidget(subtractButton, l, 1)
        buttonsLayout.addWidget(intersectButton, l, 2)
        buttonsLayout.addWidget(xorButton, l, 3)
        buttonsLayout.addWidget(hMirrorButton, l, 4)
        buttonsLayout.addWidget(vMirrorButton, l, 5)
        l += 1
        buttonsLayout.addWidget(alignHLeftButton, l, 0)
        buttonsLayout.addWidget(alignHCenterButton, l, 1)
        buttonsLayout.addWidget(alignHRightButton, l, 2)
        buttonsLayout.addWidget(alignVTopButton, l, 3)
        buttonsLayout.addWidget(alignVCenterButton, l, 4)
        buttonsLayout.addWidget(alignVBottomButton, l, 5)

        l = 0
        transformLayout.addWidget(self.alignmentWidget, l, 1)
        l += 1
        transformLayout.addWidget(invScaleButton, l, 0)
        transformLayout.addWidget(self.scaleXEdit, l, 1)
        transformLayout.addWidget(scaleButton, l, 2)
        l += 1
        transformLayout.addWidget(self.scaleYEdit, l, 1)
        l += 1
        transformLayout.addWidget(rotateButton, l, 0)
        transformLayout.addWidget(self.rotateEdit, l, 1)
        transformLayout.addWidget(invRotateButton, l, 2)
        l += 1
        transformLayout.addWidget(invSkewButton, l, 0)
        transformLayout.addWidget(self.skewEdit, l, 1)
        transformLayout.addWidget(skewButton, l, 2)
        l += 1
        transformLayout.addWidget(snapButton, l, 0)
        transformLayout.addWidget(self.snapEdit, l, 1)
        l += 1
        transformLayout.addLayout(buttonsLayout, l, 0, 1, 3)
        transformGroup.setLayout(transformLayout)

        layersGroup = AccordionBox(self.tr("Layers"), self)
        layersLayout = QGridLayout(self)

        self.layerSetView = ListView(self)
        self.layerSetView.setDragEnabled(True)
        # HACK: we need this to setup headers and signals
        self.layerSetView.setList([[None, None, None]])
        hdr = self.layerSetView.header()
        hdr.setMinimumSectionSize(20)
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.resizeSection(0, 20)
        hdr.resizeSection(2, 34)
        self.layerSetView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layerSetView.dataDropped.connect(self.writeLayerOrder)
        self.layerSetView.valueChanged.connect(self.writeLayerAttribute)

        layerAddButton = PushButton(self)
        layerAddButton.setIconSize(QSize(16, 16))
        layerAddButton.setIcon(icons.icon("i_plus"))
        layerAddButton.setToolTip(self.tr("Add a layer"))
        layerAddButton.clicked.connect(self.addLayer)
        layerRemoveButton = PushButton(self)
        layerRemoveButton.setIconSize(QSize(16, 16))
        layerRemoveButton.setIcon(icons.icon("i_minus"))
        layerRemoveButton.setToolTip(self.tr("Remove selected layer"))
        layerRemoveButton.clicked.connect(self.removeLayer)
        layerDownButton = PushButton(self)
        layerDownButton.setIconSize(QSize(16, 16))
        layerDownButton.setIcon(icons.icon("i_down"))
        layerDownButton.setToolTip(self.tr("Lower selected layer"))
        layerDownButton.clicked.connect(lambda: self.layerOffset(1))
        layerUpButton = PushButton(self)
        layerUpButton.setIconSize(QSize(16, 16))
        layerUpButton.setIcon(icons.icon("i_up"))
        layerUpButton.setToolTip(self.tr("Raise selected layer"))
        layerUpButton.clicked.connect(lambda: self.layerOffset(-1))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layersLayout.setSpacing(0)
        l = 0
        layersLayout.addWidget(self.layerSetView, l, 0, 1, 5)
        l += 1
        layersLayout.addWidget(layerAddButton, l, 0)
        layersLayout.addWidget(layerRemoveButton, l, 1)
        layersLayout.addWidget(spacer, l, 2)
        layersLayout.addWidget(layerDownButton, l, 3)
        layersLayout.addWidget(layerUpButton, l, 4)
        layersGroup.setLayout(layersLayout)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(glyphGroup)
        mainLayout.addWidget(transformGroup)
        mainLayout.addWidget(layersGroup)
        mainLayout.addWidget(spacer)
        self.setLayout(mainLayout)

    # -------------
    # Notifications
    # -------------

    def _unsubscribeFromGlyph(self):
        glyph = self._glyph
        if glyph is not None:
            glyph.removeObserver(self, "Glyph.Changed")

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(
                self, "_updateGlyphAttributes", "Glyph.Changed")

    def _unsubscribeFromFont(self):
        font = self._font
        if font is not None:
            layerSet = font.layers
            if layerSet is not None:
                layerSet.removeObserver(self, "LayerSet.Changed")

    def _subscribeToFont(self, font):
        if font is not None:
            layerSet = font.layers
            if layerSet is not None:
                layerSet.addObserver(
                    self, "_updateLayerAttributes", "LayerSet.Changed")

    def _updateGlyph(self, *_):
        self._unsubscribeFromGlyph()
        app = QApplication.instance()
        self._glyph = app.currentGlyph()
        self._subscribeToGlyph(self._glyph)
        self.alignmentWidget.setGlyph(self._glyph)
        self._updateGlyphAttributes()

    def _updateFont(self, *_):
        self._unsubscribeFromFont()
        app = QApplication.instance()
        self._font = app.currentFont()
        self._subscribeToFont(self._font)
        self._updateLayerAttributes()

    def _updateGlyphAttributes(self, *_):
        name = None
        unicodes = None
        width = None
        leftMargin = None
        rightMargin = None
        markColor = None
        if self._glyph is not None:
            name = self._glyph.name
            unicodes = " ".join("%06X" % u if u > 0xFFFF else "%04X" %
                                u for u in self._glyph.unicodes)
            width = round(self._glyph.width)
            if self._glyph.leftMargin is not None:
                leftMargin = round(self._glyph.leftMargin)
            if self._glyph.rightMargin is not None:
                rightMargin = round(self._glyph.rightMargin)
            if self._glyph.markColor is not None:
                markColor = QColor.fromRgbF(
                    *tuple(self._glyph.markColor))

        self.nameEdit.setText(name)
        self.unicodesEdit.setText(unicodes)
        self.widthEdit.setValue(width)
        self.leftMarginEdit.setValue(leftMargin)
        self.rightMarginEdit.setValue(rightMargin)
        self.markColorWidget.setColor(markColor)

    def _updateLayerAttributes(self, *_):
        font = self._font
        if font is None or font.layers is None:
            self.layerSetView.setList([[None, None, None]])
            return
        layers = []
        for layer in font.layers:
            color = layer.color
            if color is not None:
                color = colorToQColor(color)
            else:
                color = QColor()
            # XXX: add layer.visible
            layers.append([True, layer.name, color])
        self.layerSetView.setList(layers)
        if self._shouldEditLastName:
            self.layerSetView.editItem(len(layers)-1, 1)
            self._shouldEditLastName = False

    # ---------
    # Callbacks
    # ---------

    # glyph attributes

    def writeGlyphName(self):
        if self._glyph is None:
            return
        # TODO: should there be an API for this (e.g. glyph.rename())
        layerSet = self._glyph.layerSet
        newName = self.nameEdit.text()
        if layerSet is not None:
            oldName = self._glyph.name
            for layer in layerSet:
                if oldName in layer:
                    glyph = layer[oldName]
                    glyph.name = newName
        else:
            self._glyph.name = newName

    def writeUnicodes(self):
        if self._glyph is None:
            return
        text = self.unicodesEdit.text()
        if text:
            value = [int(uni, 16) for uni in text.split(" ")]
        else:
            value = []
        self._glyph.unicodes = value

    def writeWidth(self):
        if self._glyph is None:
            return
        self._glyph.width = self.widthEdit.value()

    def writeleftMargin(self):
        if self._glyph is None:
            return
        self._glyph.leftMargin = self.leftMarginEdit.value()

    def writerightMargin(self):
        if self._glyph is None:
            return
        self._glyph.rightMargin = self.rightMarginEdit.value()

    def writeMarkColor(self):
        color = self.markColorWidget.color()
        if color is not None:
            color = color.getRgbF()
        self._glyph.markColor = color

    def writeLayerAttribute(self, index, previous, current):
        font = self._font
        if font is None or font.layers is None:
            return
        row, column = index.row(), index.column()
        layers = font.layers
        layer = layers[layers.layerOrder[row]]
        if column == 0:
            pass  # TODO
        elif column == 1:
            # name
            layer.name = current
        elif column == 2:
            # color
            if current.isValid():
                color = current.getRgbF()
            else:
                color = None
            layer.color = color
        else:
            raise ValueError("invalid column selected: %d." % column)

    def writeLayerOrder(self):
        font = self._font
        if font is None or font.layers is None:
            return
        data = self.layerSetView.list()
        layerSet = font.layers
        layerOrder = []
        for _, name, _ in data:
            layerOrder.append(name)
        # defcon has data validity assertion (constant len etc.)
        layerSet.layerOrder = layerOrder

    # transforms

    def lockScale(self, checked):
        self.scaleYEdit.setEnabled(not checked)

    def scaleGlyph(self):
        glyph = self._glyph
        # TODO: consider disabling the buttons in that case?
        if glyph is None:
            return
        glyph.prepareUndo()
        sX = self.scaleXEdit.value()
        if not self.scaleYEdit.isEnabled():
            sY = sX
        else:
            sY = self.scaleYEdit.value()
        if self.sender().property("inverted"):
            sX, sY = -sX, -sY
        sX = 1 + .01 * sX
        sY = 1 + .01 * sY
        center = self.alignmentWidget.origin()
        glyph.scale((sX, sY), center=center)

    def rotateGlyph(self):
        glyph = self._glyph
        if glyph is None:
            return
        glyph.prepareUndo()
        value = self.rotateEdit.value()
        if self.sender().property("inverted"):
            value = -value
        origin = self.alignmentWidget.origin()
        glyph.rotate(value, offset=origin)

    def skewGlyph(self):
        glyph = self._glyph
        if glyph is None:
            return
        glyph.prepareUndo()
        value = self.skewEdit.value()
        if self.sender().property("inverted"):
            value = -value
        glyph.skew((value, 0))

    def snapGlyph(self):
        glyph = self._glyph
        if glyph is None:
            return
        glyph.prepareUndo()
        base = self.snapEdit.value()
        glyph.snap(base)

    def union(self):
        # TODO: disable button instead
        glyph = self._glyph
        if glyph is None:
            return
        # unselected bookkeeping
        unselContours = []
        for contour in glyph:
            if not contour.selection:
                unselContours.append(contour)
        partialSelection = unselContours and len(unselContours) < len(glyph)
        if partialSelection:
            for contour in reversed(unselContours):
                glyph.removeContour(contour)
        glyph.removeOverlap()
        if partialSelection:
            for contour in unselContours:
                glyph.appendContour(contour)

    def subtract(self):
        pass

    def intersect(self):
        pass

    def xor(self):
        pass

    def hMirror(self):
        glyph = self._glyph
        if glyph is None or glyph.controlPointBounds is None:
            return
        glyph.prepareUndo()
        xMin, _, xMax, _ = glyph.controlPointBounds
        for contour in glyph:
            for point in contour:
                point.x = xMin + xMax - point.x
        glyph.dirty = True

    def vMirror(self):
        glyph = self._glyph
        if glyph is None or glyph.controlPointBounds is None:
            return
        glyph.prepareUndo()
        _, yMin, _, yMax = glyph.controlPointBounds
        for contour in glyph:
            for point in contour:
                point.y = yMin + yMax - point.y
        glyph.dirty = True

    def alignHLeft(self):
        glyph = self._glyph
        if glyph is None:
            return
        selectedContours = []
        xMin_all = None
        for contour in glyph:
            sel = False
            xMin = None
            for pt in contour:
                if xMin is None or xMin > pt.x:
                    xMin = pt.x
                if pt.selected:
                    sel = True
            if sel:
                selectedContours.append((contour, xMin))
                if xMin_all is None or xMin_all > xMin:
                    xMin_all = xMin
        if not selectedContours:
            return
        glyph.prepareUndo()
        for contour, xMin in selectedContours:
            if xMin > xMin_all:
                delta = xMin_all - xMin
                contour.move((delta, 0))

    def alignHCenter(self):
        glyph = self._glyph
        if glyph is None:
            return
        selectedContours = []
        xMin_all, xMax_all = None, None
        for contour in glyph:
            sel = False
            xMin, xMax = None, None
            for pt in contour:
                if xMin is None or xMin > pt.x:
                    xMin = pt.x
                if xMax is None or xMax < pt.x:
                    xMax = pt.x
                if pt.selected:
                    sel = True
            if sel:
                selectedContours.append((contour, xMin, xMax))
                if xMin_all is None or xMin_all > xMin:
                    xMin_all = xMin
                if xMax_all is None or xMax_all < xMax:
                    xMax_all = xMax
        if not selectedContours:
            return
        glyph.prepareUndo()
        xAvg_all = xMin_all + round(.5 * (xMax_all - xMin_all))
        for contour, xMin, xMax in selectedContours:
            xAvg = xMin + round(.5 * (xMax - xMin))
            if xAvg != xAvg_all:
                delta = xAvg_all - xAvg
                contour.move((delta, 0))

    def alignHRight(self):
        glyph = self._glyph
        if glyph is None:
            return
        selectedContours = []
        xMax_all = None
        for contour in glyph:
            sel = False
            xMax = None
            for pt in contour:
                if xMax is None or xMax < pt.x:
                    xMax = pt.x
                if pt.selected:
                    sel = True
            if sel:
                selectedContours.append((contour, xMax))
                if xMax_all is None or xMax_all < xMax:
                    xMax_all = xMax
        if not selectedContours:
            return
        glyph.prepareUndo()
        for contour, xMax in selectedContours:
            if xMax < xMax_all:
                delta = xMax_all - xMax
                contour.move((delta, 0))

    def alignVTop(self):
        glyph = self._glyph
        if glyph is None:
            return
        selectedContours = []
        yMax_all = None
        for contour in glyph:
            sel = False
            yMax = None
            for pt in contour:
                if yMax is None or yMax < pt.y:
                    yMax = pt.y
                if pt.selected:
                    sel = True
            if sel:
                selectedContours.append((contour, yMax))
                if yMax_all is None or yMax_all < yMax:
                    yMax_all = yMax
        if not selectedContours:
            return
        glyph.prepareUndo()
        for contour, yMax in selectedContours:
            if yMax < yMax_all:
                delta = yMax_all - yMax
                contour.move((0, delta))

    def alignVCenter(self):
        glyph = self._glyph
        if glyph is None:
            return
        selectedContours = []
        yMin_all, yMax_all = None, None
        for contour in glyph:
            sel = False
            yMin, yMax = None, None
            for pt in contour:
                if yMin is None or yMin > pt.y:
                    yMin = pt.y
                if yMax is None or yMax < pt.y:
                    yMax = pt.y
                if pt.selected:
                    sel = True
            if sel:
                selectedContours.append((contour, yMin, yMax))
                if yMin_all is None or yMin_all > yMin:
                    yMin_all = yMin
                if yMax_all is None or yMax_all < yMax:
                    yMax_all = yMax
        if not selectedContours:
            return
        glyph.prepareUndo()
        yAvg_all = yMin_all + round(.5 * (yMax_all - yMin_all))
        for contour, yMin, yMax in selectedContours:
            yAvg = yMin + round(.5 * (yMax - yMin))
            if yAvg != yAvg_all:
                delta = yAvg_all - yAvg
                contour.move((0, delta))

    def alignVBottom(self):
        glyph = self._glyph
        if glyph is None:
            return
        selectedContours = []
        yMin_all = None
        for contour in glyph:
            sel = False
            yMin = None
            for pt in contour:
                if yMin is None or yMin > pt.y:
                    yMin = pt.y
                if pt.selected:
                    sel = True
            if sel:
                selectedContours.append((contour, yMin))
                if yMin_all is None or yMin_all > yMin:
                    yMin_all = yMin
        if not selectedContours:
            return
        glyph.prepareUndo()
        for contour, yMin in selectedContours:
            if yMin > yMin_all:
                delta = yMin_all - yMin
                contour.move((0, delta))

    # layer operations

    def addLayer(self):
        font = self._font
        if font is None or font.layers is None:
            return
        name = "New layer"  # XXX: mangle
        self._shouldEditLastName = True
        layer = font.layers.newLayer(name)
        layer.color = ColorGenerator.getColor() + [1]

    def removeLayer(self):
        font = self._font
        if font is None or font.layers is None:
            return
        if len(font.layers) <= 1:
            return
        name = self.layerSetView.currentRow()[1]
        del font.layers[name]

    def layerOffset(self, offset):
        font = self._font
        if font is None or font.layers is None:
            return
        data = self.layerSetView.list()
        i = self.layerSetView.currentIndex().row()
        ni = (i + offset) % len(data)
        layerSet = font.layers
        layerOrder = layerSet.layerOrder
        layerOrder[i], layerOrder[ni] = layerOrder[ni], layerOrder[i]
        # defcon has data validity assertion (constant len etc.)
        layerSet.layerOrder = layerOrder

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        # TODO: shouldn't size policy do this for us?
        return self.minimumSizeHint()

    def showEvent(self, event):
        super().showEvent(event)
        app = QApplication.instance()
        self._updateGlyph()
        app.dispatcher.addObserver(self, "_updateGlyph", "currentGlyphChanged")
        self._updateFont()
        app.dispatcher.addObserver(self, "_updateFont", "currentFontChanged")

    def hideEvent(self, event):
        super().hideEvent(event)
        app = QApplication.instance()
        app.dispatcher.removeObserver(self, "currentGlyphChanged")
        app.dispatcher.removeObserver(self, "currentFontChanged")


class PropertiesView(QScrollArea):
    propertiesWidgetClass = PropertiesWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._propertiesWidget = self.propertiesWidgetClass(self)
        self.setWidget(self._propertiesWidget)

    def eventFilter(self, obj, event):
        # this works because QScrollArea.setWidget installs an eventFilter
        # on the widget
        if obj == self.widget() and event.type() == QEvent.Resize:
            self.setMinimumWidth(self.widget().minimumSizeHint().width(
                ))  # + self.verticalScrollBar().width())
        return super().eventFilter(obj, event)
