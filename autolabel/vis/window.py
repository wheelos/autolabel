#!/usr/bin/env python

# Copyright 2024 wheelos <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QMenuBar, QToolBar, QVBoxLayout, QWidget,
                             QPushButton, QLabel, QFileDialog, QHBoxLayout, QDockWidget, QStatusBar, QListWidget)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QMouseEvent


class AnnotationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main Window Settings
        self.setWindowTitle("Markup tools")
        self.setGeometry(100, 100, 1200, 800)

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.help_menu = self.menu_bar.addMenu("Help")

        # Open
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(open_action)

        # Tool Bar
        self.tool_bar = QToolBar("ToolBar", self)
        self.addToolBar(Qt.TopToolBarArea, self.tool_bar)

        play_action = QAction("Run", self)
        undo_action = QAction("Undo", self)
        redo_action = QAction("Redo", self)
        self.tool_bar.addAction(play_action)
        self.tool_bar.addAction(undo_action)
        self.tool_bar.addAction(redo_action)

        # Sidebar (draggable, floating)
        self.dock_widget = QDockWidget("Shape", self)
        self.dock_widget.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout()
        self.point_button = QPushButton("Point")
        self.rect_button = QPushButton("Rect")
        self.sidebar_layout.addWidget(self.point_button)
        self.sidebar_layout.addWidget(self.rect_button)
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.dock_widget.setWidget(self.sidebar_widget)

        self.point_button.clicked.connect(self.activate_point_mode)
        self.rect_button.clicked.connect(self.activate_rect_mode)

        # Main window
        self.image_label = QLabel(self)
        self.image_label.setScaledContents(True)
        self.image_label.setGeometry(200, 100, 800, 600)
        self.setCentralWidget(self.image_label)

        # Used to save the current drawing mode and graphics
        self.current_mode = None
        self.shapes = []

        # Bottom progress bar and thumbnail list
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.thumbnail_list = QListWidget(self)
        self.thumbnail_list.setFlow(QListWidget.LeftToRight)
        self.status_bar.addWidget(self.thumbnail_list, 1)

        # For drawing graphics
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()

    def open_file(self):
        # Open
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open", "", "img (*.png *.jpg);;video (*.mp4 *.avi)")
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap)
            self.add_thumbnail(pixmap)

    def add_thumbnail(self, pixmap):
        # Add image as thumbnail
        thumbnail = QLabel()
        thumbnail.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        self.thumbnail_list.addItem("缩略图")

    def activate_point_mode(self):
        self.current_mode = "point"

    def activate_rect_mode(self):
        self.current_mode = "rect"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_mode:
            self.drawing = True
            self.start_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_mode == "rect":
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()
            if self.current_mode == "point":
                self.shapes.append(("point", self.start_point))
            elif self.current_mode == "rect":
                self.shapes.append(
                    ("rect", QRect(self.start_point, self.end_point)))
            self.update()

    def paintEvent(self, event):
        if self.image_label.pixmap():
            painter = QPainter(self)
            painter.drawPixmap(self.image_label.geometry(),
                               self.image_label.pixmap())

            for shape in self.shapes:
                if shape[0] == "point":
                    painter.drawEllipse(shape[1], 5, 5)
                elif shape[0] == "rect":
                    painter.drawRect(shape[1])
            painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.shapes:
            self.shapes.pop()
            self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AnnotationWindow()
    window.show()
    sys.exit(app.exec_())
