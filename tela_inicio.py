
import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,QLabel, QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtGui import QFont, QPixmap,  QColor
from PyQt6.QtCore import Qt


class Menu(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Por uma Gota")
        self.setFixedSize(1600, 900)

        # Fundo
        self.fundo = QLabel(self)
        imagem = QPixmap(r"C:\jogoPrototipo\main\fundos\fundo.png")

        self.fundo.setPixmap(
            imagem.scaled(1600, 900)
        )
        self.fundo.setGeometry(0, 0, 1600, 900)

        # Subtitulo
        self.titulo2 = QLabel("Um sertão radioativo", self)
        self.titulo2.setGeometry(0, 340, self.width(), 60)
        self.titulo2.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
        self.titulo2.setFont(
                    QFont("Press Start 2P", 23, QFont.Weight.Bold)
                )
        self.titulo2.setStyleSheet("color: lightgreen;")

        brilho = QGraphicsDropShadowEffect()
        
        brilho.setBlurRadius(35)
        brilho.setColor(QColor(57, 255, 20))
        brilho.setOffset(0, 0)
        
        self.titulo2.setGraphicsEffect(brilho)

        # Título
        self.titulo1 = QLabel("Por uma Gota", self)
        self.titulo1.setGeometry(0, 240, self.width(), 100)
        self.titulo1.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.titulo1.setFont(
            QFont("Press Start 2P", 45, QFont.Weight.Bold)
        )
        self.titulo1.setStyleSheet("color: lightgreen;")
        
        # Brilho verde no título
        brilho = QGraphicsDropShadowEffect()

        brilho.setBlurRadius(35)
        brilho.setColor(QColor(57, 255, 20))
        brilho.setOffset(0, 0)

        self.titulo1.setGraphicsEffect(brilho)

        # Botão iniciar
        self.iniciar = QPushButton("INICIAR JOGO", self)
        largura_botao_iniciar = 350
        self.iniciar.setGeometry(
            (self.width() - largura_botao_iniciar) // 2, 425,
            largura_botao_iniciar, 65,
        )
        self.iniciar.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))

        self.iniciar.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #003300,stop: 0.5 #008000,stop: 1 #39FF14);
                color: white;
                border-radius: 0px;
                font-size: 22px;
                color: #D9FFD0;
                border: 3px solid #39FF14;
            }
            QPushButton:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop: 0 #39FF14,stop: 1 #ADFF2F);
                color: #003300;
                border: 3px solid #CCFF00;
            }
        """)

        self.iniciar.clicked.connect(self.abrir_jogo)

        # Botão sair
        self.sair = QPushButton("SAIR", self)
        largura_botao = 250
        self.sair.setGeometry(
            (self.width() - largura_botao) // 2, 510, largura_botao, 65
        )
        self.sair.clicked.connect(self.close)
        self.sair.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))

        self.sair.setStyleSheet("""
                    QPushButton {
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop: 0 #003300,stop: 0.5 #008000,stop: 1 #39FF14);
                        color: white;
                        border-radius: 0px;
                        font-size: 22px;
                        color: #D9FFD0;
                        border: 3px solid #39FF14;
                    }
                    QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop: 0 #39FF14,stop: 1 #ADFF2F);
                        color: #003300;
                        border: 3px solid #CCFF00;
                    }
                """)
        
        self.tutorial = QPushButton("TUTORIAL", self)
        self.tutorial.setGeometry(
            (self.width() - largura_botao) // 2, 595, largura_botao, 65
        )
        self.tutorial.clicked.connect(self.mostrar_tutorial)
        self.tutorial.setFont(QFont("Press Start 2P", 12, QFont.Weight.Bold))
        
        self.tutorial.setStyleSheet("""
                            QPushButton {
                                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop: 0 #003300,stop: 0.5 #008000,stop: 1 #39FF14);
                                color: white;
                                border-radius: 0px;
                                font-size: 22px;
                                color: #D9FFD0;
                                border: 3px solid #39FF14;
                            }
                            QPushButton:hover {
                            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop: 0 #39FF14,stop: 1 #ADFF2F);
                                color: #003300;
                                border: 3px solid #CCFF00;
                            }
                        """)

    def mostrar_tutorial(self):

        mensagem = QMessageBox(self)

        mensagem.setWindowTitle("Tutorial - Por uma Gota")
        mensagem.setText("Bem-vindo ao sertão radioativo!")

        mensagem.setInformativeText(
        "Seu objetivo é sobreviver em um ambiente "
        "contaminado e preservar as gotas de água." \
        "\n\n" \
        "Controles: WASD para mover, espaço para pular. // Setas para se mover e pular." \
    )

        mensagem.setIcon(QMessageBox.Icon.Information)

        mensagem.exec()

        
        

    def abrir_jogo(self):
        caminho_historia = Path(__file__).resolve().parent / "historia" / "cena1.py"
        subprocess.Popen([sys.executable, str(caminho_historia)])
        self.close()


app = QApplication(sys.argv)

janela = Menu()
janela.show()

sys.exit(app.exec())
