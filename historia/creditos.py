import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

if __package__:
    from .navegacao import abrir_pagina, mostrar_janela, registrar_fonte_qt
else:
    from navegacao import abrir_pagina, mostrar_janela, registrar_fonte_qt


PASTA_PROJETO = Path(__file__).resolve().parents[1]


class CenaHistoria(QWidget):
    def __init__(self):
        super().__init__()
        familia_fonte = registrar_fonte_qt()
        self.setWindowTitle("Por uma Gota - Créditos")
        self.setFixedSize(1600, 900)
        self.setStyleSheet("background-color: black;")

        texto_creditos = (
            "CRÉDITOS\n\n\n"
            "POR UMA GOTA\n\n"
            "UM SERTÃO RADIOATIVO\n\n\n\n"
            "DESENVOLVIMENTO\n\n"
            "Projeto final de curso\n\n\n\n"
            "TECNOLOGIAS\n\n"
            "Python  •  Pygame-CE  •  PyQt6  •  SQLite\n\n\n\n"
            "Músicas utilizadas\n\n"
            "Day - No, I'm Not a Human (Max Specter)\n\n"
            "Sally Face - Dark Things (Steve Gabry)\n\n"
            "The Legend of Zelda: Ocarina of Time - Title Theme (Koji Kondo)\n\n\n"
            "Jogo feito por Rafael e Kaique"
        )
        self.creditos = QLabel(texto_creditos, self)
        self.creditos.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.creditos.setWordWrap(True)
        self.creditos.setFont(QFont(familia_fonte, 18, QFont.Weight.Bold))
        self.creditos.setStyleSheet("color: white;")
        self.creditos.setGeometry(150, self.height(), 1300, 1000)

        self.voltar = QPushButton("VOLTAR AO INÍCIO", self)
        self.voltar.setGeometry(575, 800, 450, 65)
        self.voltar.setFont(QFont(familia_fonte, 14, QFont.Weight.Bold))
        self.voltar.setStyleSheet(
            """
            QPushButton {
                background-color: #003300;
                color: #D9FFD0;
                border: 3px solid #39FF14;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #39FF14;
                color: #003300;
            }
            """
        )
        self.voltar.clicked.connect(self.voltar_ao_inicio)

        self.timer_creditos = QTimer(self)
        self.timer_creditos.timeout.connect(self.rolar_creditos)
        self.timer_creditos.start(20)

    def rolar_creditos(self):
        y = self.creditos.y() - 2
        if y + self.creditos.height() < 0:
            self.timer_creditos.stop()
            return
        self.creditos.move(self.creditos.x(), y)

    def voltar_ao_inicio(self):
        caminho_inicio = PASTA_PROJETO / "tela_inicio.py"
        abrir_pagina(self, caminho_inicio, self.voltar)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = mostrar_janela(CenaHistoria())
    sys.exit(app.exec())
