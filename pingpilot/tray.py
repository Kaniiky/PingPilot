"""Ícone na bandeja do Windows (perto do relógio), com menu e notificações."""
import logging
import threading

logger = logging.getLogger("pingpilot")


class Tray:
    def __init__(self, icon_path, on_open, on_quit, labels=("Abrir PingPilot", "Sair")):
        self.icon = None
        try:
            import pystray
            from PIL import Image

            menu = pystray.Menu(
                pystray.MenuItem(labels[0], lambda: on_open(), default=True),  # clique no ícone
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(labels[1], lambda: on_quit()))
            self.icon = pystray.Icon("PingPilot", Image.open(icon_path), "PingPilot", menu)
            threading.Thread(target=self.icon.run, name="bandeja", daemon=True).start()
        except Exception:
            logger.exception("Ícone da bandeja indisponível; o app segue sem ele")

    def notify(self, title, message):
        """Balão de notificação do Windows (aparece mesmo com a janela escondida)."""
        if not self.icon:
            return False
        try:
            self.icon.notify(message, title)
            return True
        except Exception:
            logger.exception("Falha ao mostrar notificação")
            return False

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
