import cv2
import numpy
from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QSlider, QApplication, \
    QCheckBox

from source.QtImageViewer import QtImageViewer


class QtAlignmentToolWidget(QWidget):
    closed = pyqtSignal()

    def __init__(self, project, parent=None):
        super(QtAlignmentToolWidget, self).__init__(parent)

        # ==============================================================

        self.project = project
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMinimumWidth(1200)
        self.setMinimumHeight(600)
        self.setWindowTitle("Alignment Tool")
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        self.alpha = 50
        self.threshold = 64
        self.resolution = 1
        self.previewSize = None
        # TODO
        self.rotation = 0
        #
        self.offset = [0, 0]
        self.cachedLeftGrayArray = None
        self.cachedRightGrayArray = None
        self.cachedLeftRGBArray = None
        self.cachedRightRGBArray = None

        # ==============================================================
        # Top buttons
        # ==============================================================

        # Sync
        self.checkBoxSync = QCheckBox("Sync")
        self.checkBoxSync.setChecked(True)
        self.checkBoxSync.setFocusPolicy(Qt.NoFocus)
        self.checkBoxSync.setMinimumWidth(40)
        self.checkBoxSync.stateChanged[int].connect(self.toggleSync)

        # Preview
        self.checkBoxPreview = QCheckBox("Preview")
        self.checkBoxPreview.setChecked(False)
        self.checkBoxPreview.setFocusPolicy(Qt.NoFocus)
        self.checkBoxPreview.setMinimumWidth(40)
        self.checkBoxPreview.stateChanged[int].connect(self.togglePreview)

        # Slider
        self.alphaSliderLabel = QLabel("A:" + str(self.alpha))
        self.alphaSliderLabel.setMinimumWidth(50)
        self.alphaSlider = QSlider(Qt.Horizontal)
        self.alphaSlider.setFocusPolicy(Qt.StrongFocus)
        self.alphaSlider.setMinimum(0)
        self.alphaSlider.setMaximum(100)
        self.alphaSlider.setValue(50)
        self.alphaSlider.setTickInterval(1)
        self.alphaSlider.setAutoFillBackground(True)
        self.alphaSlider.valueChanged.connect(self.previewAlphaValueChanged)

        # Manual offset
        self.xSliderLabel = QLabel("X:" + str(self.offset[0]))
        self.xSliderLabel.setMinimumWidth(50)
        self.xSlider = QSlider(Qt.Horizontal)
        self.xSlider.setFocusPolicy(Qt.StrongFocus)
        self.xSlider.setMinimum(0)
        self.xSlider.setMaximum(64)
        self.xSlider.setTickInterval(1)
        self.xSlider.setValue(self.offset[0])
        self.xSlider.setMinimumWidth(50)
        self.xSlider.setAutoFillBackground(True)
        self.xSlider.valueChanged.connect(self.xOffsetChanged)
        self.ySliderLabel = QLabel("Y:" + str(self.offset[1]))
        self.ySliderLabel.setMinimumWidth(50)
        self.ySlider = QSlider(Qt.Horizontal)
        self.ySlider.setFocusPolicy(Qt.StrongFocus)
        self.ySlider.setMinimum(0)
        self.ySlider.setMaximum(64)
        self.ySlider.setTickInterval(1)
        self.ySlider.setValue(self.offset[1])
        self.ySlider.setMinimumWidth(50)
        self.ySlider.setAutoFillBackground(True)
        self.ySlider.valueChanged.connect(self.yOffsetChanged)

        # ThreshOld
        self.thresholdSliderLabel = QLabel("T:" + str(self.threshold))
        self.thresholdSliderLabel.setMinimumWidth(50)
        self.thresholdSlider = QSlider(Qt.Horizontal)
        self.thresholdSlider.setFocusPolicy(Qt.StrongFocus)
        self.thresholdSlider.setMinimum(0)
        self.thresholdSlider.setMaximum(256)
        self.thresholdSlider.setValue(64)
        self.thresholdSlider.setTickInterval(1)
        self.thresholdSlider.setAutoFillBackground(True)
        self.thresholdSlider.valueChanged.connect(self.thresholdValueChanged)

        # Resolution
        self.resolutions = [{"name": "Original", "factor": 1},
                            {"name": "Decreased", "factor": 2},
                            {"name": "X-Decreased", "factor": 4},
                            {"name": "XX-Decreased", "factor": 8},
                            {"name": "Extreme", "factor": 16}]
        self.resolutionCombobox = QComboBox()
        self.resolutionCombobox.setMinimumWidth(200)

        for res in self.resolutions:
            self.resolutionCombobox.addItem(res["name"])

        self.resolutionCombobox.setCurrentIndex(0)
        self.resolutionCombobox.currentIndexChanged.connect(self.resolutionChanged)

        # Layout
        self.buttons = QHBoxLayout()
        self.buttons.addWidget(self.checkBoxSync)
        self.buttons.addWidget(self.checkBoxPreview)
        self.buttons.addWidget(self.alphaSliderLabel)
        self.buttons.addWidget(self.alphaSlider)
        self.buttons.addWidget(self.xSliderLabel)
        self.buttons.addWidget(self.xSlider)
        self.buttons.addWidget(self.ySliderLabel)
        self.buttons.addWidget(self.ySlider)
        self.buttons.addWidget(self.thresholdSliderLabel)
        self.buttons.addWidget(self.thresholdSlider)
        self.buttons.addWidget(self.resolutionCombobox)

        # ==============================================================
        # Middle UI containing map selector and map viewer
        # ==============================================================

        # Left
        self.leftCombobox = QComboBox()
        self.leftCombobox.setMinimumWidth(200)

        for image in self.project.images:
            self.leftCombobox.addItem(image.name)

        self.leftCombobox.setCurrentIndex(0)
        self.leftCombobox.currentIndexChanged.connect(self.leftImageChanged)

        self.leftImgViewer = QtImageViewer()

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.leftCombobox)
        leftLayout.addWidget(self.leftImgViewer)

        # Right
        self.rightCombobox = QComboBox()
        self.rightCombobox.setMinimumWidth(200)

        for image in self.project.images:
            self.rightCombobox.addItem(image.name)

        self.rightCombobox.setCurrentIndex(0)
        self.rightCombobox.currentIndexChanged.connect(self.rightImageChanged)

        self.rightImgViewer = QtImageViewer()

        rightLayout = QVBoxLayout()
        rightLayout.addWidget(self.rightCombobox)
        rightLayout.addWidget(self.rightImgViewer)

        # Layout
        self.editLayout = QHBoxLayout()
        self.editLayout.addLayout(leftLayout)
        self.editLayout.addLayout(rightLayout)

        # ==============================================================
        # UI for preview
        # ==============================================================

        self.aplhaPreviewViewer = QtImageViewer()
        self.leftPreviewViewer = QtImageViewer()
        self.rightPreviewViewer = QtImageViewer()

        self.previewLayout = QHBoxLayout()
        self.previewLayout.addWidget(self.aplhaPreviewViewer)
        self.previewLayout.addWidget(self.leftPreviewViewer)
        self.previewLayout.addWidget(self.rightPreviewViewer)

        # ==============================================================
        # Initialize layouts
        # ==============================================================

        content = QVBoxLayout()
        content.addLayout(self.buttons)
        content.addLayout(self.editLayout)
        content.addLayout(self.previewLayout)

        self.setLayout(content)

        # ==============================================================
        # Initialize views by simulating clicks on the UI
        # ==============================================================

        self.checkBoxSync.stateChanged.emit(1)
        self.checkBoxPreview.stateChanged.emit(0)

        self.leftCombobox.currentIndexChanged.emit(0)
        self.rightCombobox.currentIndexChanged.emit(1)

        # ==============================================================

    def closeEvent(self, event):
        self.closed.emit()
        super(QtAlignmentToolWidget, self).closeEvent(event)

    @pyqtSlot(int)
    def leftImageChanged(self, index):
        """
        Callback called when the user select a new image for the left view.
        :param: index of the new image
        """
        # Forward to private method
        self.__updateImgViewer(index, True)

    @pyqtSlot(int)
    def rightImageChanged(self, index):
        """
        Callback called when the user select a new image for the right view.
        :param: index of the new image
        """
        # Forward to private method
        self.__updateImgViewer(index, False)

    @pyqtSlot(int)
    def toggleSync(self, value):
        """
        Callback called when the sync mode is toggled on/off.
        :param: value a boolean to set the enable/disable the sync mode.
        """
        # If Enabled
        if value:
            # Share each action with the other widget
            self.leftImgViewer.viewHasChanged[float, float, float].connect(self.rightImgViewer.setViewParameters)
            self.rightImgViewer.viewHasChanged[float, float, float].connect(self.leftImgViewer.setViewParameters)
        else:
            # Disconnect the two widgets
            self.leftImgViewer.viewHasChanged[float, float, float].disconnect()
            self.rightImgViewer.viewHasChanged[float, float, float].disconnect()

    @pyqtSlot(int)
    def togglePreview(self, value):
        """
        Callback called when the Preview Mode is toggled on/off.
        :param: value a boolean representing if the mode is toggled.
        """
        # Hide / Show widgets
        self.__togglePreviewMode(value)
        # If preview is set
        if value:
            # Initialize and update the view
            self.__initializePreview()
            self.__updatePreview()

    @pyqtSlot(int)
    def previewAlphaValueChanged(self, value):
        """
        Callback called when the alpha value changes.
        :param: value the new value
        """
        # Update alpha value and slider text
        self.alpha = value
        self.alphaSliderLabel.setText("A:" + str(value))
        # Update preview
        self.__updatePreview(onlyAlpha=True)

    @pyqtSlot(int)
    def xOffsetChanged(self, value):
        """
        Callback called when the x value of the offset changes.
        :param: value the new value
        """
        # Update offset value and slider text
        self.offset[0] = value
        self.xSliderLabel.setText("X:" + str(value))
        # Update preview
        self.__updatePreview()

    @pyqtSlot(int)
    def yOffsetChanged(self, value):
        """
        Callback called when the y value of the offset changes.
        :param: value the new value
        """
        # Update offset value and slider text
        self.offset[1] = value
        self.ySliderLabel.setText("Y:" + str(value))
        # Update preview
        self.__updatePreview()

    @pyqtSlot(int)
    def thresholdValueChanged(self, value):
        """
        Callback called when the threshold value changes.
        :param: value the new value
        """
        # Update threshold value and slider text
        self.threshold = value
        self.thresholdSliderLabel.setText("T:" + str(value))
        # Update preview
        self.__updatePreview()

    @pyqtSlot(int)
    def resolutionChanged(self, index):
        """
        Callback called when the resolution changes.
        :param: index of the new resolution
        """
        self.resolution = self.resolutions[index]["factor"]
        # Update preview
        self.__initializePreview()
        self.__updatePreview()

    def __updateImgViewer(self, index, isLeft):
        """
        Private method to update the viewer and ensure that two different images are selected.
        :param: index the image to show
        :param: isLeft a boolean to choose the view to update (left/right)
        """
        # Validate index
        N = len(self.project.images)
        if index == -1 or index >= N:
            return
        # Default channel (0)
        channel = self.project.images[index].channels[0]
        # Check if channel is loaded
        if channel.qimage is None:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            channel.loadData()
            QApplication.restoreOverrideCursor()
        # Check with viewer to update
        if isLeft:
            self.leftImgViewer.setImg(channel.qimage)
            # Ensure indexes are different
            if index == self.rightCombobox.currentIndex():
                self.rightCombobox.setCurrentIndex((index + 1) % N)
        else:
            self.rightImgViewer.setImg(channel.qimage)
            # Ensure indexes are different
            if index == self.leftCombobox.currentIndex():
                self.leftCombobox.setCurrentIndex((index + 1) % N)

    def __toNumpyArray(self, img, imgFormat, channels):
        """
        Private method to create a numpy array from QImage.
        :param: img contains the QImage to transform
        :param: imgFormat contains the format of the data
        :param: channels contains the number of channels of the array
        :return: an numpy array of shape (h, w, channels)
        """
        # Retrieve and convert image into selected format
        img = img.convertToFormat(imgFormat)
        h, w = img.height(), img.width()
        # Retrieve a pointer to the modifiable memory view of the image
        ptr = img.bits()
        # Update pointer size
        ptr.setsize(h * w * channels)
        # Create numpy array
        arr = numpy.frombuffer(ptr, numpy.uint8).reshape((h, w, channels)).copy()
        # Pad img
        [rh, rw] = self.previewSize
        [ph, pw] = [rh - h, rw - w]
        arr = numpy.pad(arr, [(0, ph), (0, pw), (0, 0)], mode='constant')
        # Scale down by resolution factor
        arr = arr[::self.resolution, ::self.resolution]
        return arr

    def __toQImage(self, arr, imgFormat):
        """
        Private method to transform a numpy array into a QImage.
        :param: arr is the numpy array of shape (h, w, c)
        :param: imgFormat is the format of the image to create
        :return: a QImage
        """
        # Retrieve the shape
        [h, w, c] = arr.shape
        # Create and return the image
        img = QImage(arr.data, w, h, c * w, imgFormat)
        return img

    def __offsetArrays(self, a, b):
        """
        Private method to offset two numpy arrays.
        The array are offset in a "complementary" way:
            - the first (a) is offset from the bottom right.
            - the second (b) is offset from the top left.
        :param: a the first numpy array of shape (h, w, c)
        :param: b the second numpy array of shape (h, w, c)
        :return: the tuple (offset(a), offset(b))
        """
        # Retrieve the shape
        [h, w, _] = b.shape
        # Retrieve the offset
        [dx, dy] = self.offset
        # Scale offset down by the resolution factor
        dx = dx // self.resolution
        dy = dy // self.resolution
        # Transform each array and return the tuple
        tmp1 = a[dy:, dx:]
        tmp2 = b[:h - dy, :w - dx]
        return tmp1, tmp2

    def __processPreviewArrays(self, a, b):
        """
        Private method to create a numpy array representing the difference image for the preview.
        :param: a the first numpy array with shape (h, w, c)
        :param: b the second numpy array with shape (h, w, c)
        :return: the preview numpy array
        """
        # Offset arrays
        [tmp1, tmp2] = self.__offsetArrays(a, b)
        # Compute the absolute difference by multiplying by +1/-1 if tmp1<tmp2
        tmp3 = tmp1 - tmp2
        tmp4 = numpy.uint8(tmp1 < tmp2) * 254 + 1
        tmp = tmp3 * tmp4
        # Save the shape
        shape = tmp.shape
        # Blur the image
        tmp = cv2.medianBlur(tmp, 3)
        # tmp = scipy.ndimage.gaussian_filter(tmp, sigma=5) # TOO Slow
        # Reshape
        tmp = tmp.reshape(shape)
        # Compute the threshold
        tmp = numpy.where(tmp < self.threshold, 0, tmp)
        return tmp

    def __initializePreview(self):
        """
        Private method called once when the Preview Mode is turned on.
        It initializes all the necessary numpy arrays.
        """
        # Retrieve indexes
        index1 = self.leftCombobox.currentIndex()
        index2 = self.rightCombobox.currentIndex()
        # Update preview size
        img1 = self.project.images[index1].channels[0].qimage
        img2 = self.project.images[index2].channels[0].qimage
        self.previewSize = [max(img1.height(), img2.height()), max(img1.width(), img2.width())]
        # Load arrays: Gray Scale
        self.cachedLeftGrayArray = self.__toNumpyArray(img1, QImage.Format_Grayscale8, 1)
        self.cachedRightGrayArray = self.__toNumpyArray(img2, QImage.Format_Grayscale8, 1)
        # Load arrays: RGB Scale
        self.cachedLeftRGBArray = self.__toNumpyArray(img1, QImage.Format_RGB888, 3)
        self.cachedRightRGBArray = self.__toNumpyArray(img2, QImage.Format_RGB888, 3)

    def __updatePreview(self, onlyAlpha=False):
        """
        Private method to update the preview.
        :param: onlyAlpha is a boolean that represents whether the changes are only on the alpha section.
        """
        # ==============================================================
        # Update alpha section
        # ==============================================================
        self.aplhaPreviewViewer.clear()
        tmp1, tmp2 = self.__offsetArrays(self.cachedLeftRGBArray, self.cachedRightRGBArray)
        img1 = self.__toQImage(tmp1.copy(), QImage.Format_RGB888)
        img2 = self.__toQImage(tmp2.copy(), QImage.Format_RGB888)
        self.aplhaPreviewViewer.setImg(img1)
        self.aplhaPreviewViewer.setOpacity(numpy.clip(self.alpha, 0.0, 100.0) / 100.0)
        self.aplhaPreviewViewer.setOverlayImage(img2)
        # Jump this section to make the alpha changes apply faster
        if not onlyAlpha:
            # ==============================================================
            # Gray scale
            # ==============================================================
            self.leftPreviewViewer.clear()
            tmp = self.__processPreviewArrays(self.cachedLeftGrayArray, self.cachedRightGrayArray)
            img = self.__toQImage(tmp, QImage.Format_Grayscale8)
            self.leftPreviewViewer.setImg(img)
            # ==============================================================
            # RGB scale
            # ==============================================================
            self.rightPreviewViewer.clear()
            tmp = self.__processPreviewArrays(self.cachedLeftRGBArray, self.cachedRightRGBArray)
            img = self.__toQImage(tmp, QImage.Format_RGB888)
            self.rightPreviewViewer.setImg(img)

    def __togglePreviewMode(self, isPreviewMode):
        """
        Private method to set widget visibility to toggle the Preview Mode on/off.
        :param: isPreviewMode a boolean value to enable / disable the Preview Mode
        """
        # (Preview-ONLY) widgets
        self.aplhaPreviewViewer.setVisible(isPreviewMode)
        self.leftPreviewViewer.setVisible(isPreviewMode)
        self.rightPreviewViewer.setVisible(isPreviewMode)
        self.alphaSliderLabel.setVisible(isPreviewMode)
        self.alphaSlider.setVisible(isPreviewMode)
        self.xSliderLabel.setVisible(isPreviewMode)
        self.xSlider.setVisible(isPreviewMode)
        self.ySliderLabel.setVisible(isPreviewMode)
        self.ySlider.setVisible(isPreviewMode)
        self.thresholdSliderLabel.setVisible(isPreviewMode)
        self.thresholdSlider.setVisible(isPreviewMode)
        self.resolutionCombobox.setVisible(isPreviewMode)
        # (NON-Preview-ONLY) widgets
        self.leftImgViewer.setVisible(not isPreviewMode)
        self.rightImgViewer.setVisible(not isPreviewMode)
        self.checkBoxSync.setVisible(not isPreviewMode)
        self.leftCombobox.setVisible(not isPreviewMode)
        self.rightCombobox.setVisible(not isPreviewMode)
