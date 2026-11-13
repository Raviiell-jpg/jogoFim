import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QWidget


PASTA_PROJETO = Path(__file__).resolve().parents[1]


class CenaHistoria(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Por uma Gota - História")
        self.setFixedSize(1600, 900)

        caminho_imagem = PASTA_PROJETO / "fundos" / "historia.jpg"
        imagem = QPixmap(str(caminho_imagem))
        if imagem.isNull():
            QMessageBox.critical(
                self,
                "Imagem não encontrada",
                f"Não foi possível carregar a imagem da história:\n{caminho_imagem}",
            )
            raise FileNotFoundError(caminho_imagem)

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

        self.texto = QLabel(
            "A contaminação tomou conta da região, e a água se tornou cada vez "
            "mais rara. Agora, é preciso encontrar um jeito de sobreviver.",
            self,
        )
        self.texto.setGeometry(100, 620, 1400, 150)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setWordWrap(True)
        self.texto.setFont(QFont("Press Start 2P", 14, QFont.Weight.Bold))
        self.texto.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 170); padding: 12px;"
        )

        self.continuar = QPushButton("INICIAR JOGO", self)
        self.continuar.setGeometry(625, 800, 350, 65)
        self.continuar.setFont(QFont("Press Start 2P", 16, QFont.Weight.Bold))
        self.continuar.setStyleSheet(
            """
            QPushButton {
                background-color: lightblue;
                color: white;
                border: 3px solid #2874A6;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5DADE2;
                color: white;
            }
            """
        )
        self.continuar.clicked.connect(self.iniciar_jogo)
        self.fundo.lower()

    def iniciar_jogo(self):
        caminho_jogo = PASTA_PROJETO / "main.py"
        subprocess.Popen([sys.executable, str(caminho_jogo)])
        self.close()


app = QApplication(sys.argv)
janela = CenaHistoria()
janela.show()
sys.exit(app.exec())
