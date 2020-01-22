# TagLab                                               
# A semi-automatic segmentation tool                                    
#
# Copyright(C) 2019                                         
# Visual Computing Lab                                           
# ISTI - Italian National Research Council                              
# All rights reserved.                                                      
                                                                          
# This program is free software; you can redistribute it and/or modify      
# it under the terms of the GNU General Public License as published by      
# the Free Software Foundation; either version 2 of the License, or         
# (at your option) any later version.                                       
                                                                           
# This program is distributed in the hope that it will be useful,           
# but WITHOUT ANY WARRANTY; without even the implied warranty of            
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             
#GNU General Public License (http://www.gnu.org/licenses/gpl.txt)          
# for more details.                                               

import os

from PyQt5.QtCore import Qt, QSize, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon, qRgb, qRed, qGreen, qBlue
from PyQt5.QtWidgets import QWidget, QCheckBox, QFileDialog, QSizePolicy, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from source.Annotation import Annotation
from source import utils

class QtHistogramWidget(QWidget):

    def __init__(self, annotations, scale_factor, year, parent=None):

        super(QtHistogramWidget, self).__init__(parent)

        self.scale_factor = scale_factor
        self.year = year
        self.ann = annotations
        self.labels_info = annotations.labels_info
        self.checkBoxes = []  # list of QCheckBox
        self.setStyleSheet("background-color: rgba(60,60,65); color: white")
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        # look for existing labels in annotations
        labels_set = set()

        for blob in self.ann.seg_blobs:
            labels_set.add(blob.class_name)

        labels_set.discard('Empty')
        labels_layout = QVBoxLayout()

        CLASS_LABELS_HEIGHT = 20
        LABELS_FOR_ROW = 4


        for i, label_name in enumerate(labels_set):

            chkBox = QCheckBox(label_name)
            chkBox.setChecked(True)

            btnC = QPushButton("")
            btnC.setFlat(True)

            color = self.labels_info[label_name]
            r = color[0]
            g = color[1]
            b = color[2]
            text = "QPushButton:flat {background-color: rgb(" + str(r) + "," + str(g) + "," + str(b) + "); border: none ;}"

            btnC.setStyleSheet(text)
            btnC.setAutoFillBackground(True)
            btnC.setFixedWidth(CLASS_LABELS_HEIGHT)
            btnC.setFixedHeight(CLASS_LABELS_HEIGHT)

            if i % LABELS_FOR_ROW == 0:
                layout = QHBoxLayout()
                labels_layout.addLayout(layout)

            self.checkBoxes.append(chkBox)
            layout.addWidget(chkBox)
            layout.addWidget(btnC)
            layout.addSpacing(20)

        self.btnCancel = QPushButton("Cancel")
        self.btnCancel.clicked.connect(self.close)
        self.btnPreview = QPushButton("Preview")
        self.btnPreview.clicked.connect(self.preview)
        self.btnSaveAs = QPushButton("Save As")
        self.btnSaveAs.clicked.connect(self.saveas)

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignRight)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btnCancel)
        buttons_layout.addWidget(self.btnPreview)
        buttons_layout.addWidget(self.btnSaveAs)


        self.preview_W = 800
        self.preview_H = 520
        pxmap = QPixmap(self.preview_W, self.preview_H)
        self.lblPreview = QLabel()
        self.lblPreview.setFixedWidth(self.preview_W+4)
        self.lblPreview.setFixedHeight(self.preview_H+4)
        self.lblPreview.setPixmap(pxmap)
        self.lblPreview.setUpdatesEnabled(True)

        layoutV = QVBoxLayout()
        layoutV.addWidget(self.lblPreview)
        layoutV.addLayout(labels_layout)
        layoutV.addLayout(buttons_layout)
        layoutV.setSpacing(3)
        self.setLayout(layoutV)

        self.setWindowTitle("CREATE AND EXPORT HISTOGRAM")
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        self.adjustSize()

    @pyqtSlot()
    def cancel(self):

        self.close()



    @pyqtSlot()
    def preview(self):
        list_selected = []
        list_color=[]
        for checkbox in self.checkBoxes:
            if checkbox.isChecked():
               list_selected.append(checkbox.text())
               list_color.append(self.labels_info[checkbox.text()])

        self.create_histogram(list_selected,list_color)

    def create_histogram(self, list_selected,list_color):

        class_area =[]

        for my_class in list_selected:
            my_area = []
            for blob in self.ann.seg_blobs:
                if blob.class_name == my_class:
                   blob_area = blob.area * self.scale_factor * self.scale_factor/100
                   blob_area = np.around(blob_area, decimals=2)
                   my_area.append(blob_area)
            class_area.append(my_area)

        max_area = np.zeros(len(list_selected))
        sum_area = np.zeros(len(list_selected))

        for i in range(0, len(list_selected)):
            area_array = np.asarray(class_area[i])
            max_area[i] = max(area_array)
            sum_area[i] = sum(area_array)

        # histogram plot
        total_coverage = sum(sum_area)
        bins = np.arange(0, max(max_area), 100)
        colors = [tuple(np.asanyarray(list_color[i])/255)for i in range(0, len(list_selected))]
        areas = [np.asarray(class_area[i]) for i in range(0, len(list_selected))]
        patches = [mpatches.Patch(color=tuple(np.asanyarray(list_color[i]) / 255),   label='%.4f' % (sum_area[i] / 10000) + " m^2 " + list_selected[i]) for i in range(0, len(list_selected))]

        fig = plt.figure()
        fig.set_size_inches(10, 6.5)
        plt.legend(handles=patches)
        plt.hist(areas, bins, color=colors)
        plt.xlabel("Colonies area (cm^2)")
        plt.ylabel("Number of colonies")
        plt.title('%.4f' % (total_coverage/ 10000) + " m^2 of " + '+ '.join(list_selected)+ " classes in " + self.year)
        plt.show()
        fig.canvas.draw()

        # grab the pixel buffer and dump it into a numpy array
        buf = fig.canvas.tostring_rgb()
        ncols, nrows = fig.canvas.get_width_height()
        im = np.fromstring(buf, dtype=np.uint8).reshape(nrows, ncols, 3)

        # numpy array to QPixmap
        qimg = utils.rgbToQImage(im)
        qimg = qimg.scaled(self.preview_W, self.preview_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pxmap = QPixmap(qimg)

        self.lblPreview.setPixmap(pxmap)

    @pyqtSlot()
    def saveas(self):
        """
        Save the current histograms.
        """

        filters = "PNG (*.png)"
        filename, _ = QFileDialog.getSaveFileName(self, "Save as", "", filters)

        if filename:

            pxmap = self.lblPreview.pixmap()
            qimg = pxmap.toImage()
            qimg.save(filename)
