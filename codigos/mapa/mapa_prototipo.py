import pygame
from pathlib import Path

TILE_SIZE = 32

DADOS_MAPA = [
    # Topo / Terraço
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X           M                          H                             M         X",
    "X                         XXXXXXXXX                     XXXXXXXXX     X",
    "X                                                                              X",
    "X  P M             H     SSSS       M             M               M            X",
    "XXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXX   XXXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X       XXXXX           X           XXXXX              X           XXXXX       X",
    "X                       X                              X                       X",
    "X               XXXXX   X      H               XXXXX   X   H           XXXXX   X",
    "X                       X   XXXXXXXX                   X XXXXX                 X",
    "XXXXX   XXXXXXXXXXXXXXXXX               XXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X          H            X              M               X              M        X",
    "X       XXXXXXX         X           XXXXXXX            X           XXXXXXX     X",
    "X                       X                              X                       X",
    "X   XXXXX               X      XXXXX           SSSS    X      XXXXX            X",
    "XXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X              M        X              H               X              M        X",
    "X           XXXXX       X           XXXXX              X           XXXXX       X",
    "X                       X                              X                       X",
    "X    XXXXX      SSSS    X      XXXXX                   X      XXXXX            X",
    "XXXXX   XXXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X         M             X              M               X              M        X",
    "X      XXXXXX           X           XXXXXX             X           XXXXXX      X",
    "X                       X                              X                       X",
    "X              XXXXX    X              XXXXX           X              XXXXX    X",
    "XXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X   XXXXX               X      XXXXX        H          X      XXXXX            X",
    "X               M       X              M   XXXX        X              M        X",
    "X            XXXXXX     X           XXXXXX             X           XXXXXX      X",
    "X                       X                              X                       X",
    "XXXXX   XXXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X          M            X              M               X              M        X",
    "X       XXXXX           X           XXXXX              X           XXXXX       X",
    "X                       X                              X                       X",
    "X   XXXX       SSSSS    X      XXXX                    X      XXXX             X",
    "XXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X               M       X              M               X              M        X",
    "X            XXXXX      X           XXXXX              X           XXXXX       X",
    "X                       X                              X                       X",
    "X    XXXXX              X      XXXXX                   X      XXXXX            X",
    "XXXXX   XXXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X          M            X              M               X              M        X",
    "X       XXXXXX          X           XXXXXX             X           XXXXXX      X",
    "X                       X                              X                       X",
    "X              XXXXX    X              XXXXX           X              XXXXX    X",
    "XXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X   XXXXX               X      XXXXX                   X      XXXXX            X",
    "X               M       X              M               X              M        X",
    "X            XXXXX      X           XXXXX              X           XXXXX       X",
    "X                       X                              X                       X",
    "XXXXX   XXXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXX",
    "X                       X                              X                       X",
    "X          M            X              M               X              M        X",
    "X       XXXXXX  SSSS    X           XXXXXX     H       X           XXXXXX      X",
    "X                       X                     XXXX     X                       X",
    "X                       X                              X                       X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

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
        self.largura = len(DADOS_MAPA[0]) * self.tile_size
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
                elif caractere == "S":
                    self.espinhos.append(pygame.Rect(pos_x, pos_y + 16, self.tile_size, 16))
                elif caractere == "H":
                    self.kits_medicos.append(pygame.Rect(pos_x + 6, pos_y + 6, 20, 20))

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
#