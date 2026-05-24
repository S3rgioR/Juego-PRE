"""Sistema de guardado y carga de partida - Clase SaveManager.

Maneja la serialización y deserialización del estado del juego
en archivos JSON. Responsabilidad única: persistencia.
"""

import json
import os


class SaveManager:
    """Gestor de guardado y carga de partida.

    Attributes
    ----------
    ruta : str
        Ruta del archivo de guardado.
    """

    def __init__(self, ruta: str = "savegame.txt"):
        """Inicializa el SaveManager con una ruta de guardado.

        Parameters
        ----------
        ruta : str, optional
            Ruta del archivo de guardado (default: "savegame.txt")
        """
        self.ruta = ruta

    def guardar(self, datos: dict) -> bool:
        """Guarda el estado del juego en un archivo JSON.

        Parameters
        ----------
        datos : dict
            Estado a guardar. Debe contener claves serializables (no pygame.Rect).
            Ejemplo: {'pos': [x, y], 'hp': 5, 'camara': [cx, cy]}

        Returns
        -------
        bool
            True si se guardó correctamente, False si hubo un error.
        """
        try:
            with open(self.ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            print(f"[SaveManager] Error al guardar: {e}")
            return False

    def cargar(self) -> dict | None:
        """Carga el estado del juego desde un archivo JSON.

        Returns
        -------
        dict or None
            Diccionario con el estado guardado, o None si no existe o hay error.
        """
        if not self.existe():
            return None
        try:
            with open(self.ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[SaveManager] Error al cargar: {e}")
            return None

    def existe(self) -> bool:
        """Comprueba si existe un archivo de guardado.

        Returns
        -------
        bool
            True si el archivo existe, False en caso contrario.
        """
        return os.path.exists(self.ruta)

    def eliminar(self) -> bool:
        """Elimina el archivo de guardado.

        Returns
        -------
        bool
            True si se eliminó, False si hubo error o no existe.
        """
        try:
            if self.existe():
                os.remove(self.ruta)
                return True
            return False
        except OSError as e:
            print(f"[SaveManager] Error al eliminar: {e}")
            return False