import pygame
from pathlib import Path

TILE_SIZE = 32
INIMIGOS_INICIAIS = [
    (15, 3), (8, 11), (24, 11), (38, 11),
    (7, 17), (23, 17), (39, 17),
    (4, 24), (22, 24), (40, 24),
]

DADOS_MAPA = [
    # Topo / Terraço
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X       M              H             M           X",
    "X                                                X",
    "X  P       H       SSSS       M                  X",
    "XXXXX     XXXXXXXXX       XXXXXXXXXXXXX    XXXXXXX",
    "X             X                 X                X",
    "X    XXXX     X       H         X      XXXX      X",
    "X             X                 X                X",
    "X       M     X       M         X                X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X        M             H              M          X",
    "X      XXXXX         XXXXX          XXXXX        X",
    "X                                                X",
    "X   XXXX       SSSS       XXXX                   X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X       M             M                M         X",
    "X     XXXXX         XXXXX            XXXXX       X",
    "X                                                X",
    "X         H                  H                   X",
    "X       XXXXX              XXXXX                 X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X    M                  M                 M      X",
    "X  XXXXXX             XXXXXX            XXXXXX   X",
    "X                                                X",
    "X        SSSS                 SSSS               X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X         M                H              M      X",
    "X       XXXXX           XXXXX          XXXXX     X",
    "X                                                X",
    "X    XXXX                   XXXX                 X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X       M             M                M         X",
    "X     XXXXX         XXXXX            XXXXX       X",
    "X                                                X",
    "X             H                                  X",
    "X           XXXXX                                X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X       M             M                M         X",
    "X     XXXXX         XXXXX            XXXXX       X",
    "X                                                X",
    "X   XXXX       SSSSS        XXXX                 X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X          M             H              M        X",
    "X        XXXXX         XXXXX          XXXXX      X",
    "X                                                X",
    "X             SSSS                               X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X       M             M                M         X",
    "X     XXXXX         XXXXX            XXXXX       X",
    "X                                                X",
    "X             H                                  X",
    "X           XXXXX                                X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X        M             M               M         X",
    "X      XXXXX         XXXXX           XXXXX       X",
    "X                                                X",
    "X    XXXX        SSSS       XXXX                 X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",

    "X                                                X",
    "X       M             H                M         X",
    "X     XXXXX         XXXXX            XXXXX       X",
    "X                                                X",
    "X                                                X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]


def _adicionar_escadas(dados):
    grade = [list(linha) for linha in dados]
    largura = len(grade[0])
    pisos = [
        indice
        for indice, linha in enumerate(grade)
        if all(caractere == "X" for caractere in linha)
    ]
    if len(pisos) < 3:
        return ["".join(linha) for linha in grade]

    coluna_minima = largura - 8
    coluna_maxima = largura - 2
    coluna_atual = coluna_minima + 1
    direcao = 1
    pisos_set = set(pisos)

    def abrir_piso(linha, coluna):
        for coluna_abertura in range(
            max(1, coluna - 1),
            min(largura - 1, coluna + 2),
        ):
            if grade[linha][coluna_abertura] == "X":
                grade[linha][coluna_abertura] = " "

    abrir_piso(pisos[1], coluna_atual)

    for linha in range(pisos[1] + 1, pisos[-1]):
        if linha not in pisos_set:
            for coluna in range(coluna_minima, coluna_maxima + 1):
                if grade[linha][coluna] == "X":
                    grade[linha][coluna] = " "

    for piso_superior, piso_inferior in zip(pisos[1:-1], pisos[2:]):
        linhas_escada = range(piso_superior + 1, piso_inferior)
        for indice, linha in enumerate(linhas_escada):
            if not coluna_minima <= coluna_atual <= coluna_maxima:
                raise ValueError("A escada excedeu a faixa disponível no mapa.")
            if grade[linha][coluna_atual] != " ":
                raise ValueError(
                    f"Não foi possível criar a escada na linha {linha}."
                )
            grade[linha][coluna_atual] = "X"
            if indice < len(linhas_escada) - 1:
                coluna_atual += direcao

        if piso_inferior != pisos[-1]:
            abrir_piso(piso_inferior, coluna_atual)
            coluna_atual += direcao
        direcao *= -1

    return ["".join(linha) for linha in grade]


DADOS_MAPA = _adicionar_escadas(DADOS_MAPA)


class Mapa:
    def __init__(self):
        self.tile_size = TILE_SIZE
        pasta_projeto = Path(__file__).resolve().parents[2]
        pasta_cenario = pasta_projeto / "cenario"
        caminho_textura = pasta_cenario / "chao.png"
        self.textura_chao = pygame.image.load(str(caminho_textura)).convert()
        caminho_textura_cura = pasta_cenario / "cura.png"
        self.textura_cura = None
        if caminho_textura_cura.is_file():
            self.textura_cura = pygame.image.load(
                str(caminho_textura_cura)
            ).convert_alpha()
            self.textura_cura = pygame.transform.scale(
                self.textura_cura, (self.tile_size, self.tile_size)
            )
        largura_grade = len(DADOS_MAPA[0])
        if any(len(linha) != largura_grade for linha in DADOS_MAPA):
            raise ValueError("Todas as linhas do mapa devem ter a mesma largura.")
        self.largura = largura_grade * self.tile_size
        self.altura = len(DADOS_MAPA) * self.tile_size

        self.blocos = []
        self.espinhos = []
        self.moedas = []
        self.kits_medicos = []
        self.pos_inicial_jogador = (64, 128)

        self._processar_dados()
        self.textura_mapa = pygame.Surface((self.largura, self.altura))
        largura_textura, altura_textura = self.textura_chao.get_size()
        for y in range(0, self.altura, altura_textura):
            for x in range(0, self.largura, largura_textura):
                self.textura_mapa.blit(self.textura_chao, (x, y))

    def _processar_dados(self):
        for linha_idx, linha in enumerate(DADOS_MAPA):
            for col_idx, caractere in enumerate(linha):
                pos_x = col_idx * self.tile_size
                pos_y = linha_idx * self.tile_size

                if caractere == "X":
                    self.blocos.append(pygame.Rect(pos_x, pos_y, self.tile_size, self.tile_size))
                elif caractere == "P":
                    self.pos_inicial_jogador = (pos_x, pos_y)

                elif caractere == "M":
                    self.moedas.append(
                        pygame.Rect(pos_x + 8, pos_y + 8, 16, 16)
                    )
                elif caractere == "S":
                    self.espinhos.append(pygame.Rect(pos_x, pos_y + 16, self.tile_size, 16))
                elif caractere == "H":
                    self.kits_medicos.append(pygame.Rect(pos_x + 6, pos_y + 6, 20, 20))

        self.inimigos_iniciais = [
            (coluna * self.tile_size, linha * self.tile_size)
            for coluna, linha in INIMIGOS_INICIAIS
        ]

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela):
        # A textura usa coordenadas do mapa para não reiniciar em cada bloco.
        for bloco in self.blocos:
            bx = bloco.x - camera_x
            by = bloco.y - camera_y
            if -self.tile_size < bx < largura_tela and -self.tile_size < by < altura_tela:
                tela.blit(self.textura_mapa, (bx, by), area=bloco)

        for esp in self.espinhos:
            ex = esp.x - camera_x
            ey = esp.y - camera_y
            if -self.tile_size < ex < largura_tela and -self.tile_size < ey < altura_tela:
                pontos = [(ex, ey + 16), (ex + 16, ey), (ex + 32, ey + 16)]
                pygame.draw.polygon(tela, (180, 50, 50), pontos)
                pygame.draw.polygon(tela, (230, 90, 90), pontos, 2)

        # Kits Médicos
        for kit in self.kits_medicos:
            x_centro = kit.centerx - camera_x
            y_centro = kit.centery - camera_y
            if (
                -self.tile_size < x_centro < largura_tela + self.tile_size
                and -self.tile_size < y_centro < altura_tela + self.tile_size
            ):
                visual_cura = pygame.Rect(0, 0, self.tile_size, self.tile_size)
                visual_cura.center = (x_centro, y_centro)
                if self.textura_cura is not None:
                    tela.blit(self.textura_cura, visual_cura)
                else:
                    pygame.draw.rect(tela, (240, 240, 240), visual_cura, border_radius=4)
                    pygame.draw.rect(
                        tela, (46, 204, 113),
                        (visual_cura.x + 13, visual_cura.y + 5, 6, 22)
                    )
                    pygame.draw.rect(
                        tela, (46, 204, 113),
                        (visual_cura.x + 5, visual_cura.y + 13, 22, 6)
                    )

        for moeda in self.moedas:
            cx = moeda.centerx - camera_x
            cy = moeda.centery - camera_y
            if -16 < cx < largura_tela + 16 and -16 < cy < altura_tela + 16:
                pygame.draw.circle(tela, (255, 215, 0), (cx, cy), 8)
#