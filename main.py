import sys
from PySide6.QtWidgets import QApplication
from appcontroller import AppController

# ----------------------- UTILIDADES ----------------------------
# Codigo utilizado para converter .ui->.py: pyuic5 myapp.ui -o myapp.py
# criando um exe: pyinstaller --noconsole main.py
# Codigo utilizado para converter .ui->.py: pyuic5 myapp.ui -o myapp.py
# Criando um exe: 
# Com DLL:
# pyinstaller --noconsole main.py
# Arquivo único:
# pyinstaller --onefile --noupx --windowed --icon=icon.ico -n EXENAME main.py
# --onefile: argumento para gerar arquivo único 
# --noupx: dispensa o uso de UPX. Esse é opcional, assim como os demais abaixo.
#   Alguns fóruns dizem que ajuda na demora para o arquivo abrir.
# --windowed funciona como o --noconsole, escondendo o console que aparece por padrão.
# --icon=iconname.ico: Caso se deseje atribuir um ícone ao executável.
# -n EXENAME: Caso se deseje atribuir um nome ao exe
# ----------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ctrl = AppController()
    ctrl.show()
    app.exec()
