"""Sistema de eventos simple - Implementación del patrón Observer.

La Vista emite eventos y el Presenter se suscribe para reaccionar,
evitando llamadas directas entre capas (desacoplamiento).
"""


class Event:
    """Canal de notificación basado en callbacks (patrón Observer).

    Attributes
    ----------
    suscriptores : list of callable
        Lista de funciones que se ejecutarán cuando se emita el evento.
    """

    def __init__(self):
        self.suscriptores = []

    def add_listener(self, funcion_a_conectar):
        """Registra una función que se llamará cuando se emita el evento."""
        self.suscriptores.append(funcion_a_conectar)

    def emit(self, *args):
        """Notifica a todos los suscriptores pasándoles los argumentos dados."""
        for funcion in self.suscriptores:
            funcion(*args)
