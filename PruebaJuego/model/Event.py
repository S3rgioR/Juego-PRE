"""Evento simple de tipo observer, propio del paquete Model.

Sin dependencias de pygame: el Model es la capa lógica del juego y
no debe depender de la capa gráfica. Esta clase permite que el Model
notifique sucesos (ataque, detección, disparo...) sin conocer quién
escucha — el Presenter se suscribe desde fuera, sin que el Model
necesite importar nada de la Vista o del Presenter.

Misma interfaz que view.Event (add_listener / emit), para mantener
un único patrón de eventos en todo el proyecto.
"""


class Event:
    def __init__(self):
        self._listeners = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    def emit(self, *args, **kwargs):
        for callback in self._listeners:
            callback(*args, **kwargs)
