#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import sys

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


def load_pyside_plugins():
    """
    Функция загружает Qt плагины.

    """

    import PySide
    import os

    qApp = PySide.QtGui.QApplication.instance()

    for plugins_dir in [os.path.join(p, "plugins") for p in PySide.__path__]:
        qApp.addLibraryPath(plugins_dir)


LIST_FILES = list()
NAME_PROGRAM = ""
ICON_PROGRAM = ""

try:
    import STATIC_CONFIG
    LIST_FILES = STATIC_CONFIG.LIST_FILES
    NAME_PROGRAM = STATIC_CONFIG.NAME_PROGRAM
    ICON_PROGRAM = STATIC_CONFIG.ICON_PROGRAM
except:
    print('except')
    LIST_FILES = list()
    NAME_PROGRAM = ""
    ICON_PROGRAM = None


def get_target_path_with_args_from_lnk(file_name):
    """
    Возвращает путь к файлу на который ссылается lnk и аргументы.

    """

    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(file_name)
    return shortcut.Targetpath + " " + shortcut.Arguments


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.link_list_view = QListWidget()

        self.link_list_view.setViewMode(QListView.IconMode)
        self.link_list_view.setMovement(QListView.Static)
        self.link_list_view.setResizeMode(QListView.Adjust)
        self.link_list_view.setGridSize(QSize(ICON_SIZE, ICON_SIZE))
        self.link_list_view.installEventFilter(self)

        main_tool_bar = self.addToolBar('main_tool_bar')
        save_action = main_tool_bar.addAction('Save')
        save_action.triggered.connect(self.save)

        main_layout = QVBoxLayout()

        self.name_program_line_edit = QLineEdit()
        self.path_to_icon_program_line_edit = QLineEdit()
        self.path_to_icon_program_line_edit.installEventFilter(self)

        layout = QFormLayout()
        layout.addRow("Name:", self.name_program_line_edit)
        layout.addRow("Path icon:", self.path_to_icon_program_line_edit)
        main_layout.addLayout(layout)

        main_layout.addWidget(self.link_list_view)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setAcceptDrops(True)

        self.update_states()

        self.list_files = list()
        for file_data in LIST_FILES:
            self.add_file_data(file_data)

    def add_file_data(self, file_data):
        print(file_data)

        # Работаем только с файлами
        import os
        if not os.path.isfile(file_data['target']):
            return

        self.list_files.append(file_data)

        icon = qicon_from_base64(file_data['icon'])

        item = QListWidgetItem(icon, file_data['name'])
        item.setToolTip(file_data['name'] + "\n\n" + file_data['target'])
        self.link_list_view.addItem(item)

    def add_file(self, file_name):
        print(file_name)

        file_info = QFileInfo(file_name)

        name = file_info.baseName()
        target = file_name
        if file_info.isSymLink():
            target = get_target_path_with_args_from_lnk(file_name)

        base64_image = get_icon_base64(file_name)
        file_data = {
            'name': name,
            'target': target,
            'icon': base64_image,
        }
        self.add_file_data(file_data)

    def update_states(self):
        self.setWindowTitle(NAME_PROGRAM)
        self.name_program_line_edit.setText(NAME_PROGRAM)

        icon = qicon_from_base64(ICON_PROGRAM)
        self.setWindowIcon(icon)

    def save(self):
        global LIST_FILES, NAME_PROGRAM, ICON_PROGRAM
        LIST_FILES = self.list_files
        NAME_PROGRAM = self.name_program_line_edit.text()

        file_name = self.path_to_icon_program_line_edit.text()
        if file_name:
            ICON_PROGRAM = get_icon_base64(file_name)

        with open('STATIC_CONFIG.py', mode='w', encoding='utf-8') as f:
            f.write("""\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


LIST_FILES = {}
NAME_PROGRAM = "{}"
ICON_PROGRAM = {}

            """.format(
                LIST_FILES,
                NAME_PROGRAM,
                ICON_PROGRAM,
            ))

        self.update_states()

    def eventFilter(self, obj, event):
        if obj == self.link_list_view or obj == self.path_to_icon_program_line_edit:
            if event.type() == QEvent.DragEnter:
                urls = event.mimeData().urls()

                # Фильтруем: оставляем только файлы
                import os.path
                urls = [url.toLocalFile()
                        for url in urls
                        if os.path.isfile(url.toLocalFile())]
                if urls:
                    event.acceptProposedAction()
                    return True

            elif event.type() == QEvent.Drop:
                urls = event.mimeData().urls()
                if not urls:
                    return False

                if obj == self.link_list_view:
                    for url in urls:
                        file_name = url.toLocalFile()
                        self.add_file(file_name)

                elif obj == self.path_to_icon_program_line_edit:
                    obj == self.path_to_icon_program_line_edit.setText(urls[0].toLocalFile())

                return True

            return False
        else:
            return super().eventFilter(obj, event)


# TODO: http://doc.qt.io/qt-4.8/qlistview.html
# TODO: http://doc.qt.io/qt-5/qabstractlistmodel.html


if __name__ == '__main__':
    app = QApplication(sys.argv)
    load_pyside_plugins()

    mw = MainWindow()
    mw.show()

    app.exec_()
