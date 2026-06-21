import os
import sys

import os
import sys


def obtener_ruta(ruta_relativa):
    """ Devuelve la ruta absoluta exacta corrigiendo cualquier problema de ejecución """
    # 1. Forzamos que las barras se adapten a Windows (\) automáticamente
    ruta_normalizada = ruta_relativa.replace('/', os.sep).replace('\\', os.sep)

    # 2. Si corre desde el .exe
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_normalizada)

    # 3. Si corre desde PyCharm (Usa la ubicación de Import.py como raíz del proyecto)
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, ruta_normalizada)