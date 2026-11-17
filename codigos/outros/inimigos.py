import pygame


class Inimigo:
    DURACAO_QUADRO_MS = 120
    DURACAO_ATAQUE = 12
    ESCALA_SPRITE = 2.4

    def __init__(
        self,
        x,
        y,
        largura=26,
        altura=30,
        vida=70,
        velocidade=2,
        imagem=None,
        quadros=None,
        quadros_ataque=None,
    ):
        self.rect = pygame.Rect(x, y, largura, altura)
        if quadros is not None:
            imagens = quadros
        elif imagem is not None:
            imagens = [imagem]
        else:
            imagens = []
        if quadros_ataque and not imagens:
            raise ValueError(
                "Os quadros de ataque exigem pelo menos um quadro normal."
            )
        if imagens:
            altura_sprite = round(altura * self.ESCALA_SPRITE)
            largura_sprite = max(
                round(largura * self.ESCALA_SPRITE),
                round(
                    altura_sprite
                    * imagens[0].get_width()
                    / imagens[0].get_height()
                ),
            )
            tamanho_sprite = (largura_sprite, altura_sprite)
            self.quadros = [
                pygame.transform.scale(quadro, tamanho_sprite)
                for quadro in imagens
            ]
            self.quadros_esquerda = [
                pygame.transform.flip(quadro, True, False)
                for quadro in self.quadros
            ]
            self.quadros_ataque = [
                pygame.transform.scale(quadro, tamanho_sprite)
                for quadro in (quadros_ataque or [])
            ]
            self.quadros_ataque_esquerda = [
                pygame.transform.flip(quadro, True, False)
                for quadro in self.quadros_ataque
            ]
        else:
            self.quadros = []
            self.quadros_esquerda = []
            self.quadros_ataque = []
            self.quadros_ataque_esquerda = []
        self.vida = vida
        self.vida_maxima = vida
        self.velocidade = velocidade
        self.direcao = 1
        self.vel_y = 0
        self.vel_recuo_x = 0.0
        self.esta_vivo = True

        self.tempo_dano = 0
        self.tempo_atordoado = 0
        self.alcance_visao = 42
        self.atacando = False
        self.timer_preparacao = 0
        self.timer_ataque = 0
        self.cooldown_ataque = 0
        self.hitbox_ataque = None
        self.dano_ataque = 20

    def atualizar(self, blocos, jogador_rect=None, hitbox_escudo=None):
        if not self.esta_vivo:
            return

        if self.tempo_dano > 0:
            self.tempo_dano -= 1

        if self.tempo_atordoado > 0:
            self.tempo_atordoado -= 1

        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= 1

        if abs(self.vel_recuo_x) > 0.1:
            self.vel_recuo_x *= 0.82
        else:
            self.vel_recuo_x = 0.0

        if self.timer_preparacao > 0:
            self.timer_preparacao -= 1
            if self.timer_preparacao <= 0:
                self.atacando = True
                self.timer_ataque = self.DURACAO_ATAQUE

        if self.atacando:
            self.timer_ataque -= 1
            largura_golpe = 26
            altura_golpe = 20
            if self.direcao == 1:
                hx = self.rect.right
            else:
                hx = self.rect.left - largura_golpe
            hy = self.rect.centery - (altura_golpe // 2)
            self.hitbox_ataque = pygame.Rect(
                hx, hy, largura_golpe, altura_golpe
            )

            if self.timer_ataque <= 0:
                self.atacando = False
                self.hitbox_ataque = None
                self.cooldown_ataque = 45
        else:
            self.hitbox_ataque = None

        if (
            jogador_rect is not None
            and self.tempo_atordoado <= 0
            and not self.atacando
            and self.timer_preparacao <= 0
            and self.cooldown_ataque <= 0
        ):
            dist_y = abs(self.rect.centery - jogador_rect.centery)
            dist_x = jogador_rect.centerx - self.rect.centerx
            if dist_y < 32 and abs(dist_x) <= self.alcance_visao:
                self.direcao = 1 if dist_x >= 0 else -1
                self.timer_preparacao = 14

        movimento_patrulha = 0
        if (
            self.tempo_atordoado <= 0
            and not self.atacando
            and self.timer_preparacao <= 0
            and abs(self.vel_recuo_x) < 1.0
        ):
            movimento_patrulha = self.direcao * self.velocidade

        deslocamento_x = int(movimento_patrulha + self.vel_recuo_x)
        self.rect.x += deslocamento_x

        for bloco in blocos:
            if self.rect.colliderect(bloco):
                if deslocamento_x > 0:
                    self.rect.right = bloco.left
                    self.vel_recuo_x = 0.0
                    if movimento_patrulha > 0:
                        self.direcao = -1
                elif deslocamento_x < 0:
                    self.rect.left = bloco.right
                    self.vel_recuo_x = 0.0
                    if movimento_patrulha < 0:
                        self.direcao = 1

        bateu_no_escudo = False
        if hitbox_escudo is not None:
            if self.rect.colliderect(hitbox_escudo):
                if self.direcao == 1:
                    self.rect.right = hitbox_escudo.left
                else:
                    self.rect.left = hitbox_escudo.right
                bateu_no_escudo = True
            elif (
                self.hitbox_ataque is not None
                and self.hitbox_ataque.colliderect(hitbox_escudo)
            ):
                self.atacando = False
                self.hitbox_ataque = None
                self.cooldown_ataque = 45
                bateu_no_escudo = True

        if bateu_no_escudo and self.tempo_atordoado <= 0:
            self.aplicar_pulinho_recuo(
                -self.direcao, forca_x=6.5, forca_y=-6.0
            )
            self.tempo_atordoado = 25

        self.vel_y += 0.75
        if self.vel_y > 15:
            self.vel_y = 15

        self.rect.y += int(self.vel_y)
        for bloco in blocos:
            if self.rect.colliderect(bloco):
                if self.vel_y > 0:
                    self.rect.bottom = bloco.top
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = bloco.bottom
                    self.vel_y = 0

    def aplicar_pulinho_recuo(self, direcao_empurrao, forca_x=6.5, forca_y=-6.0):
        self.vel_recuo_x = direcao_empurrao * forca_x
        self.vel_y = forca_y

    def tomar_dano(self, quantidade, direcao_golpe):
        if self.tempo_dano <= 0 and self.esta_vivo:
            self.vida -= quantidade
            self.tempo_dano = 15
            self.atacando = False
            self.timer_preparacao = 0
            self.hitbox_ataque = None
            self.aplicar_pulinho_recuo(
                direcao_golpe, forca_x=7.0, forca_y=-5.5
            )
            if self.vida <= 0:
                self.esta_vivo = False
            return True
        return False

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela):
        if not self.esta_vivo:
            return

        ix = self.rect.x - camera_x
        iy = self.rect.y - camera_y
        if -40 < ix < largura_tela and -40 < iy < altura_tela:
            if not self.quadros:
                pygame.draw.rect(
                    tela, (142, 68, 173),
                    (ix, iy, self.rect.width, self.rect.height),
                    border_radius=3,
                )

                olho_x = ix + 16 if self.direcao == 1 else ix + 4
                pygame.draw.rect(
                    tela, (255, 255, 255), (olho_x, iy + 6, 6, 6)
                )
                olho_pupila_x = olho_x + (2 if self.direcao == 1 else 0)
                pygame.draw.rect(
                    tela, (0, 0, 0), (olho_pupila_x, iy + 8, 3, 3)
                )
            else:
                if self.atacando and self.quadros_ataque:
                    progresso_ataque = (
                        self.DURACAO_ATAQUE - self.timer_ataque
                    )
                    indice_quadro = min(
                        progresso_ataque
                        * len(self.quadros_ataque)
                        // self.DURACAO_ATAQUE,
                        len(self.quadros_ataque) - 1,
                    )
                    quadros = (
                        self.quadros_ataque
                        if self.direcao == 1
                        else self.quadros_ataque_esquerda
                    )
                else:
                    indice_quadro = (
                        pygame.time.get_ticks() // self.DURACAO_QUADRO_MS
                    ) % len(self.quadros)
                    quadros = (
                        self.quadros
                        if self.direcao == 1
                        else self.quadros_esquerda
                    )
                imagem = quadros[indice_quadro]
                posicao_imagem = (
                    ix + (self.rect.width - imagem.get_width()) // 2,
                    iy + self.rect.height - imagem.get_height(),
                )
                tela.blit(imagem, posicao_imagem)

            largura_barra = self.rect.width
            vida_proporcional = max(
                0, int((self.vida / self.vida_maxima) * largura_barra)
            )

