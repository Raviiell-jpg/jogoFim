import pygame
from pathlib import Path

class SistemaSaude:
    def __init__(self, vida_maxima=100, tempo_imunidade_max=60):
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.vida_visual = float(vida_maxima)
        self.tempo_invencivel = 0
        self.tempo_imunidade_max = tempo_imunidade_max

        # Fontes do HUD: prioriza PressStart2P.ttf com fallback robusto
        caminho_fonte = Path(__file__).resolve().parents[2] / "PressStart2P.ttf"
        if caminho_fonte.is_file():
            try:
                self.fonte_hud = pygame.font.Font(str(caminho_fonte), 16)
                self.fonte_hud.set_bold(True)
                self.fonte_game_over = pygame.font.Font(str(caminho_fonte), 48)
                self.fonte_game_over.set_bold(True)
                self.fonte_sub = pygame.font.Font(str(caminho_fonte), 22)
            except Exception:
                self.fonte_hud = pygame.font.SysFont("Press Start 2P", 16, bold=True)
                self.fonte_game_over = pygame.font.SysFont("Press Start 2P", 48, bold=True)
                self.fonte_sub = pygame.font.SysFont("Press Start 2P", 22)
        else:
            self.fonte_hud = pygame.font.SysFont("Press Start 2P, consolas, arial", 16, bold=True)
            self.fonte_game_over = pygame.font.SysFont("Press Start 2P", 48, bold=True)
            self.fonte_sub = pygame.font.SysFont("Press Start 2P, consolas, arial", 22)

    def tomar_dano(self, quantidade=25):
        """Aplica dano caso o jogador não esteja no período de invulnerabilidade."""
        if self.tempo_invencivel <= 0 and self.vida_atual > 0:
            self.vida_atual = max(0, self.vida_atual - quantidade)
            self.tempo_invencivel = self.tempo_imunidade_max
            return True
        return False

    def curar(self, quantidade=25):
        """Restaura pontos de vida respeitando a vida máxima."""
        if self.vida_atual < self.vida_maxima:
            self.vida_atual = min(self.vida_maxima, self.vida_atual + quantidade)
            return True
        return False

    def esta_vivo(self):
        return self.vida_atual > 0

    def deve_desenhar_jogador(self):
        if self.tempo_invencivel > 0 and (self.tempo_invencivel // 5) % 2 == 0:
            return False
        return True

    def reiniciar(self):
        self.vida_atual = self.vida_maxima
        self.vida_visual = float(self.vida_maxima)
        self.tempo_invencivel = 0

    def atualizar(self):
        """Processa os temporizadores de imunidade e a animação suave da barra de vida."""
        if self.tempo_invencivel > 0:
            self.tempo_invencivel -= 1

        # Interpolação linear da barra de vida para efeito visual suave
        if self.vida_visual > self.vida_atual:
            self.vida_visual -= (self.vida_visual - self.vida_atual) * 0.1
            if abs(self.vida_visual - self.vida_atual) < 0.2:
                self.vida_visual = float(self.vida_atual)
        elif self.vida_visual < self.vida_atual:
            self.vida_visual += (self.vida_atual - self.vida_visual) * 0.1
            if abs(self.vida_visual - self.vida_atual) < 0.2:
                self.vida_visual = float(self.vida_atual)

    def desenhar_hud(self, tela):
        """Renderiza a barra de vida moderna e estilizada na tela."""
        # Se o jogador estiver piscando por invulnerabilidade, o HUD permanece legível
        largura_total = 220
        altura_barra = 20
        pos_x = 24
        pos_y = 24

        # Moldura de Fundo
        pygame.draw.rect(tela, (20, 24, 28), (pos_x - 3, pos_y - 3, largura_total + 6, altura_barra + 6), border_radius=4)
        pygame.draw.rect(tela, (60, 68, 76), (pos_x - 3, pos_y - 3, largura_total + 6, altura_barra + 6), 2, border_radius=4)

        # Barra de Sangue Secundária (Dano Sofrido Recente)
        prop_visual = max(0.0, min(1.0, self.vida_visual / self.vida_maxima))
        largura_visual = int(largura_total * prop_visual)
        if largura_visual > 0:
            pygame.draw.rect(tela, (220, 100, 50), (pos_x, pos_y, largura_visual, altura_barra), border_radius=3)

        # Barra de Vida Real Atual
        prop_atual = max(0.0, min(1.0, self.vida_atual / self.vida_maxima))
        largura_atual = int(largura_total * prop_atual)
        if largura_atual > 0:
            cor_vida = (135, 206, 250)
            pygame.draw.rect(tela, cor_vida, (pos_x, pos_y, largura_atual, altura_barra), border_radius=3)

        # Texto numérico da vida
        texto_vida = f"HP {self.vida_atual}/{self.vida_maxima}"
        lbl_vida = self.fonte_hud.render(texto_vida, True, (255, 255, 255))
        tela.blit(lbl_vida, (pos_x + largura_total + 14, pos_y + 1))

    def desenhar_game_over(self, tela, largura_tela, altura_tela):
        """Desenha a tela de Game Over e informa como reiniciar a partida."""
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        texto_game_over = self.fonte_game_over.render("GAME OVER", True, (231, 76, 60))
        texto_reiniciar = self.fonte_sub.render(
            "Pressione 'R' para Renascer", True, (255, 255, 255)
        )

        tela.blit(
            texto_game_over,
            texto_game_over.get_rect(
                center=(largura_tela // 2, altura_tela // 2 - 25)
            ),
        )
        tela.blit(
            texto_reiniciar,
            texto_reiniciar.get_rect(
                center=(largura_tela // 2, altura_tela // 2 + 30)
            ),
        )
