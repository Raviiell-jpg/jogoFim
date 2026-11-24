import argparse
import sys
from pathlib import Path

import pygame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

if __package__:
    from .navegacao import abrir_pagina, mostrar_janela, registrar_fonte_qt
else:
    from navegacao import abrir_pagina, mostrar_janela, registrar_fonte_qt

from banco_dados import BancoDados, formatar_tempo_ms

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
        self.banco = BancoDados()

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

        self.painel = QWidget(self)
        self.painel.setGeometry(170, 95, 1260, 650)
        self.painel.setStyleSheet(
            "background-color: rgba(4, 14, 8, 225); "
            "border: 2px solid #39FF14; border-radius: 8px;"
        )

        fonte_titulo = QFont(familia_fonte, 24, QFont.Weight.Bold)
        fonte_texto = QFont(familia_fonte, 12, QFont.Weight.Bold)
        fonte_detalhe = QFont(familia_fonte, 10)

        def criar_texto(texto, y, altura, fonte, cor):
            label = QLabel(texto, self.painel)
            label.setGeometry(30, y, 1200, altura)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setFont(fonte)
            label.setStyleSheet(f"color: {cor}; background: transparent; border: none;")
            return label

        criar_texto(
            "FUGA BEM-SUCEDIDA!",
            30,
            55,
            fonte_titulo,
            "#39FF14",
        )
        criar_texto(
            "Você alcançou o reservatório subterrâneo de água pura!",
            95,
            40,
            fonte_texto,
            "#D2FFD2",
        )
        tempo_formatado = (
            formatar_tempo_ms(tempo_ms) if tempo_ms is not None else "--:--.---"
        )
        criar_texto(
            f"TEMPO FINAL: {tempo_formatado}",
            145,
            45,
            QFont(familia_fonte, 18, QFont.Weight.Bold),
            "#FFFFFF",
        )

        if novo_recorde:
            criar_texto(
                "NOVO RECORDE PESSOAL!",
                200,
                35,
                fonte_texto,
                "#FFD700",
            )

        if usou_gm:
            criar_texto(
                "Partida com auxílio de GM; não entra no ranking oficial.",
                240 if novo_recorde else 200,
                35,
                fonte_detalhe,
                "#FF7878",
            )

        y_estatisticas = 285 if (novo_recorde or usou_gm) else 220
        criar_texto(
            f"Inimigos eliminados: {inimigos_derrotados}/{total_inimigos}",
            y_estatisticas,
            35,
            fonte_detalhe,
            "#B4E6BE",
        )

        y_ranking = y_estatisticas + 55
        criar_texto(
            "TOP 3 SOBREVIVENTES",
            y_ranking,
            35,
            fonte_texto,
            "#87CEFA",
        )
        ranking_top = self.banco.obter_ranking(limite=3, apenas_legitimos=True)
        if ranking_top:
            for indice, registro in enumerate(ranking_top):
                texto = (
                    f"#{registro['posicao']} {registro['username']} - "
                    f"{registro['tempo_formatado']} "
                    f"(Abates: {registro.get('inimigos_derrotados', 0)})"
                )
                criar_texto(
                    texto,
                    y_ranking + 42 + indice * 32,
                    30,
                    fonte_detalhe,
                    "#F0F0F0",
                )
        else:
            criar_texto(
                "Ainda não há corridas oficiais no ranking.",
                y_ranking + 42,
                30,
                fonte_detalhe,
                "#F0F0F0",
            )

        criar_texto(
            "Pressione CONTINUAR para ver os créditos.",
            570,
            35,
            fonte_detalhe,
            "#78FFAA",
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
