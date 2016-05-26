#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import sys

from PySide.QtGui import *
from PySide.QtCore import *


def load_pyside_plugins():
    """
    Функция загружает Qt плагины.

    """

    import PySide
    import os

    qApp = PySide.QtGui.QApplication.instance()

    for plugins_dir in [os.path.join(p, "plugins") for p in PySide.__path__]:
        qApp.addLibraryPath(plugins_dir)


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


# TODO: C:/Users/Public/Desktop/NetBeans IDE 8.0.1.lnk
# C:\Program Files (x86)\NetBeans 8.0.1\bin\netbeans64.exe
# NetBeans IDE 8, C:\Program Files (x86)\NetBeans 8.0.1\bin\netbeans64.exe
# file_name is not file: C:\Program Files (x86)\NetBeans 8.0.1\bin\netbeans64.exe

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        from link_list_view import LinkListView
        self.link_list_view = LinkListView(NAME_PROGRAM, ICON_PROGRAM, LIST_FILES)
        self.link_list_view.installEventFilter(self)

        main_tool_bar = self.addToolBar('main_tool_bar')

        # TODO: перенести в class LinkListView
        run_action = main_tool_bar.addAction('Run')
        # run_action.triggered.connect(self.run)
        run_action.triggered.connect(self.link_list_view.run)

        save_action = main_tool_bar.addAction('Save')
        save_action.triggered.connect(self.save)

        build_action = main_tool_bar.addAction('Build')
        build_action.triggered.connect(self.build)

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

    def update_states(self):
        self.setWindowTitle(NAME_PROGRAM)
        self.name_program_line_edit.setText(NAME_PROGRAM)

        from link_list_view import qicon_from_base64
        icon = qicon_from_base64(ICON_PROGRAM)
        self.setWindowIcon(icon)

    def save(self):
        """
        Функция сохранения статичного конфига.

        """

        global LIST_FILES, NAME_PROGRAM, ICON_PROGRAM
        LIST_FILES = self.link_list_view.list_files
        NAME_PROGRAM = self.name_program_line_edit.text()

        file_name = self.path_to_icon_program_line_edit.text()
        if file_name:
            from link_list_view import get_icon_base64
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

    def build(self):
        """
        Функция для сборки текущего скрипта в ехе.

        """

        # self.save()

        icon_file_name = 'app.ico'

        from link_list_view import qicon_from_base64, ICON_SIZE
        icon = qicon_from_base64(ICON_PROGRAM)
        pixmap = icon.pixmap(ICON_SIZE)
        pixmap.save(icon_file_name)
        print('Save ico:', icon_file_name)

        build_command = 'pyinstaller --onefile --windowed --icon={} -n "{}" link_list_view.py'.format(icon_file_name, NAME_PROGRAM)
        print('build_command:', build_command)

        from subprocess import Popen, PIPE, STDOUT
        with Popen(build_command, universal_newlines=True, stdout=PIPE, stderr=STDOUT) as process:
            print('-' * 10)
            print('Start:')

            for line in process.stdout:
                print(line, end='')

            print('End.')
            print('-' * 10)

        import os
        if os.path.exists(icon_file_name):
            print('Remove ico:', icon_file_name)
            os.remove(icon_file_name)

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
                        self.link_list_view.add_file(file_name)

                elif obj == self.path_to_icon_program_line_edit:
                    obj == self.path_to_icon_program_line_edit.setText(urls[0].toLocalFile())

                return True

            return False
        else:
            return super().eventFilter(obj, event)


# TODO: http://doc.qt.io/qt-4.8/qlistview.html
# TODO: http://doc.qt.io/qt-5/qabstractlistmodel.html
# TODO: добавление / удаление через кнопку
# TODO: логирование в окне программы
# TODO: сгенерированная прога не имеет возможности добавления / изменения компонентов -- только readonly

if __name__ == '__main__':
    app = QApplication(sys.argv)
    load_pyside_plugins()

    mw = MainWindow()
    mw.show()

    app.exec_()
