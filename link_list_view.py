#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from PySide.QtGui import *
from PySide.QtCore import *


ICON_SIZE = 60


def base64_from_qimage(image, format):
    ba = QByteArray()
    buffer = QBuffer(ba)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, format)
    return ba.toBase64().data()


def qimage_from_base64(base64_image):
    ba = QByteArray.fromBase64(base64_image)
    return QImage.fromData(ba)


def qicon_from_base64(base64_image):
    image = qimage_from_base64(base64_image)
    return QIcon(QPixmap.fromImage(image))


def get_icon_base64(file_name, format='PNG', image=None, icon=None):
    print(file_name)

    file_info = QFileInfo(file_name)
    if not file_info.isFile():
        return

    print('!')
    image_formats = [str(format).lower() for format in QImageReader.supportedImageFormats()]
    if file_info.completeSuffix().lower() in image_formats:
        print('1')
        if image is None:
            image = QImage(file_name)
        return base64_from_qimage(image, format)

    else:
        print('2')
        if icon is None:
            icon = QFileIconProvider().icon(file_info)

        image = icon.pixmap(ICON_SIZE, ICON_SIZE).toImage()
        return base64_from_qimage(image, format)


def get_target_path_with_args_from_lnk(file_name):
    """
    Возвращает кортеэ из пути к файлу на который ссылается lnk и аргументы.

    """

    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(file_name)
    return shortcut.Targetpath, shortcut.Arguments


# TODO: подправить отступы справа -- места хватает, но иконки
# переносятся на следующую строку
class LinkListView(QWidget):
    def __init__(self, NAME_PROGRAM, ICON_PROGRAM, LIST_FILES):
        super().__init__()

        self.setWindowTitle(NAME_PROGRAM)

        icon = qicon_from_base64(ICON_PROGRAM)
        self.setWindowIcon(icon)

        self.link_list_view = QListWidget()
        self.link_list_view.setViewMode(QListView.IconMode)
        self.link_list_view.setMovement(QListView.Static)
        self.link_list_view.setResizeMode(QListView.Adjust)
        self.link_list_view.setGridSize(QSize(ICON_SIZE, ICON_SIZE))
        # self.link_list_view.installEventFilter(self)
        self.setAcceptDrops(True)

        layout = QVBoxLayout()
        layout.addWidget(self.link_list_view)
        self.setLayout(layout)

        self.list_files = list()
        for file_data in LIST_FILES:
            self.add_file_data(file_data)

    def add_item(self, item):
        self.link_list_view.addItem(item)

    def add_file_data(self, file_data):
        print(file_data['name'], file_data['file_name'], sep=', ')

        # Работаем только с файлами
        import os
        file_name = file_data['file_name']
        if not os.path.isfile(file_name):
            print('file_name is not file:', file_name)
            return

        self.list_files.append(file_data)

        icon = qicon_from_base64(file_data['icon'])
        tool_tip = file_data['name'] + "\n\n" + file_data['file_name']
        if file_data['args']:
            tool_tip += ' ' + file_data['args']

        item = QListWidgetItem(icon, file_data['name'])
        item.setToolTip(tool_tip)
        item.setData(Qt.UserRole, file_data)
        self.add_item(item)

    def add_file(self, file_name):
        print(file_name)

        file_info = QFileInfo(file_name)

        name = file_info.baseName()
        args = ''
        if file_info.isSymLink():
            file_name, args = get_target_path_with_args_from_lnk(file_name)

        if args is None:
            args = ''

        base64_image = get_icon_base64(file_name)
        file_data = {
            'name': name,
            'file_name': file_name,
            'args': args,
            'icon': base64_image,
        }
        self.add_file_data(file_data)

    def current_item(self):
        return self.link_list_view.currentItem()

    def current_item_file_data(self):
        item = self.current_item()
        if item:
            return item.data(Qt.UserRole)

        return None

    # def eventFilter(self, obj, event):
    #     if obj == self.link_list_view:
    #         if event.type() == QEvent.DragEnter:
    #             urls = event.mimeData().urls()
    #
    #             # Фильтруем: оставляем только файлы
    #             import os.path
    #             urls = [url.toLocalFile()
    #                     for url in urls
    #                     if os.path.isfile(url.toLocalFile())]
    #             if urls:
    #                 event.acceptProposedAction()
    #                 return True
    #
    #         elif event.type() == QEvent.Drop:
    #             urls = event.mimeData().urls()
    #             if not urls:
    #                 return False
    #
    #             if obj == self.link_list_view:
    #                 for url in urls:
    #                     file_name = url.toLocalFile()
    #                     self.add_file(file_name)
    #
    #             return True
    #
    #         return False
    #     else:
    #         return super().eventFilter(obj, event)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    from main import load_pyside_plugins, LIST_FILES, NAME_PROGRAM, ICON_PROGRAM
    load_pyside_plugins()

    mw = LinkListView(NAME_PROGRAM, ICON_PROGRAM, LIST_FILES)
    mw.show()

    app.exec_()
