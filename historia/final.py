import argparse
import sys
from pathlib import Path

import pygame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QWidget

if __package__:
    from .navegacao import abrir_pagina, mostrar_janela, registrar_fonte_qt
else:
    from navegacao import abrir_pagina, mostrar_janela, registrar_fonte_qt

from banco_dados import formatar_tempo_ms


PASTA_PROJETO = Path(__file__).resolve().parents[1]


class CenaHistoria(QWidget):
    def __init__(
        self,
        tempo_ms=None,
        inimigos_derrotados=0,
        total_inimigos=0,
        novo_recorde=False,
        usou_gm=False,
    ):
        super().__init__()
        familia_fonte = registrar_fonte_qt()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            caminho_m = PASTA_PROJETO / "musicas" / "zelda.mp3"
            if caminho_m.is_file():
                pygame.mixer.music.load(str(caminho_m))
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Aviso de áudio (não crítico): {e}")

        self.setWindowTitle("Por uma Gota - História Final")
        self.setFixedSize(1600, 900)

        caminho_imagem = PASTA_PROJETO / "fundos" / "final.png"
        if not caminho_imagem.is_file():
            caminho_imagem = PASTA_PROJETO / "fundos" / "cenafinal.jpg"

        imagem = QPixmap(str(caminho_imagem))
        if imagem.isNull():
            imagem = QPixmap(1600, 900)
            imagem.fill(Qt.GlobalColor.black)

        self.fundo = QLabel(self)
        self.fundo.setPixmap(
            imagem.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.fundo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fundo.setGeometry(0, 0, self.width(), self.height())

        texto_narrativa = (
            "Finalmente uma água não contaminada pela radiação. Um espaço onde posso reabastecer minhas forças "
            "para assim novamente continuar tentando sobreviver neste mundo.")
        self.texto = QLabel(texto_narrativa, self)
        self.texto.setGeometry(100, 180, 1400, 100)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setWordWrap(True)
        self.texto.setFont(QFont(familia_fonte, 12, QFont.Weight.Bold))
        self.texto.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 180); border: 2px solid #39FF14; padding: 16px;"
        )

        self.voltar_inicio = QPushButton("CONTINUAR", self)
        self.voltar_inicio.setGeometry(575, 800, 450, 65)
        self.voltar_inicio.setFont(QFont(familia_fonte, 14, QFont.Weight.Bold))
        self.voltar_inicio.setStyleSheet(
            """
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #003300, stop: 0.5 #008000, stop: 1 #39FF14);
                color: #D9FFD0;
                border: 3px solid #39FF14;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #39FF14, stop: 1 #ADFF2F);
                color: #003300;
                border: 3px solid #CCFF00;
            }
            """
        )
        self.voltar_inicio.clicked.connect(self.ir_para_creditos)
        self.fundo.lower()

    def ir_para_creditos(self):
        caminho_creditos = PASTA_PROJETO / "historia" / "creditos.py"
        abrir_pagina(self, caminho_creditos, self.voltar_inicio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tempo-ms", type=int)
    parser.add_argument("--inimigos-derrotados", type=int, default=0)
    parser.add_argument("--total-inimigos", type=int, default=0)
    parser.add_argument("--novo-recorde", action="store_true")
    parser.add_argument("--usou-gm", action="store_true")
    args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)
    janela = mostrar_janela(
        CenaHistoria(
            tempo_ms=args.tempo_ms,
            inimigos_derrotados=args.inimigos_derrotados,
            total_inimigos=args.total_inimigos,
            novo_recorde=args.novo_recorde,
            usou_gm=args.usou_gm,
        )
    )
    sys.exit(app.exec())
