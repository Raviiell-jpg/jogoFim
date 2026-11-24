import importlib
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QWidget,
)


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

_FAMILIA_FONTE_QT = None


def registrar_fonte_qt() -> str:
    """Registra a fonte PressStart2P no Qt com fallback seguro para qualquer ambiente."""
    global _FAMILIA_FONTE_QT
    if _FAMILIA_FONTE_QT is not None:
        return _FAMILIA_FONTE_QT
    if QApplication.instance() is None:
        return "Consolas"

    caminho_fonte = RAIZ_PROJETO / "PressStart2P.ttf"
    if caminho_fonte.is_file():
        font_id = QFontDatabase.addApplicationFont(str(caminho_fonte))
        if font_id >= 0:
            familias = QFontDatabase.applicationFontFamilies(font_id)
            if familias:
                _FAMILIA_FONTE_QT = familias[0]
                return _FAMILIA_FONTE_QT

    _FAMILIA_FONTE_QT = "Consolas"
    return _FAMILIA_FONTE_QT


def mostrar_janela(pagina: QWidget) -> QStackedWidget:
    if QApplication.instance() is None:
        raise RuntimeError("Crie QApplication antes de mostrar uma tela.")

    janela = QStackedWidget()
    janela.addWidget(pagina)
    janela.setWindowTitle(pagina.windowTitle())
    janela.setFixedSize(pagina.size())
    janela.show()
    return janela


def abrir_pagina(
    pagina_atual: QWidget, caminho: Path, botao: QPushButton
) -> None:
    janela = pagina_atual.window()
    if not isinstance(janela, QStackedWidget):
        raise RuntimeError("A tela não está dentro da janela de navegação.")

    destino = Path(caminho).resolve()
    botao.setEnabled(False)

    if destino.name in ("main.py", "mainSpeed.py"):
        _iniciar_jogo(janela, destino, botao)
        return

    try:
        if destino.name == "tela_inicio.py":
            modulo = importlib.import_module("tela_inicio")
            pagina_nova = modulo.Menu()
        elif destino.stem == "creditos":
            modulo = importlib.import_module("historia.creditos")
            pagina_nova = modulo.CenaHistoria()
        else:
            modulo = importlib.import_module(f"historia.{destino.stem}")
            pagina_nova = modulo.CenaHistoria()
    except (AttributeError, ImportError, OSError) as erro:
        botao.setEnabled(True)
        QMessageBox.critical(
            pagina_atual,
            "Erro ao abrir a próxima tela",
            f"Não foi possível carregar {destino}:\n{erro}",
        )
        return

    pagina_anterior = janela.currentWidget()
    janela.addWidget(pagina_nova)
    janela.setWindowTitle(pagina_nova.windowTitle())
    janela.setFixedSize(pagina_nova.size())
    janela.setCurrentWidget(pagina_nova)
    janela.removeWidget(pagina_anterior)
    pagina_anterior.deleteLater()


def iniciar_menu_principal() -> bool:
    iniciou, _ = QProcess.startDetached(
        sys.executable,
        [str(RAIZ_PROJETO / "tela_inicio.py")],
        str(RAIZ_PROJETO),
    )
    return iniciou


def _iniciar_jogo(
    janela: QStackedWidget, caminho: Path, botao: QPushButton
) -> None:
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass

    iniciou, _ = QProcess.startDetached(
        sys.executable,
        [str(caminho)],
        str(RAIZ_PROJETO),
    )
    if not iniciou:
        botao.setEnabled(True)
        QMessageBox.critical(
            janela,
            "Erro ao iniciar o jogo",
            f"Não foi possível iniciar {caminho}.",
        )
        return

    janela.close()
