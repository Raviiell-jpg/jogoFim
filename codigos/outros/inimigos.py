import pygame


# Dados dos inimigos relacionados a duração de cada frame/sprite, vida, dano, tamanho, onde está localizado também cada arquivo de cada monstro(tatu, rato, lagartixa)
class Inimigo:
    DURACAO_QUADRO_MS = 120
    DURACAO_ATAQUE = 30
    ESCALA_SPRITE = 2.4

    def __init__(
        self,
        x,
        y,
        largura=26,
        altura=30,
        vida=140,
        velocidade=2,
        imagem=None,
        quadros=None,
        quadros_ataque=None,
        escala_sprite=None,
    ):
        self.rect = pygame.Rect(x, y, largura, altura)
        if escala_sprite is not None:
            self.ESCALA_SPRITE = escala_sprite
        escala = self.ESCALA_SPRITE
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
            altura_sprite = round(altura * escala)
            largura_minima = round(largura * escala)

            def _escalar_quadro(quadro, aplicar_largura_minima=True):
                largura_prop = round(
                    altura_sprite
                    * quadro.get_width()
                    / max(1, quadro.get_height())
                )
                largura_final = (
                    max(largura_minima, largura_prop)
                    if aplicar_largura_minima
                    else max(1, largura_prop)
                )
                return pygame.transform.scale(
                    quadro, (largura_final, altura_sprite)
                )

            self.quadros = [
                _escalar_quadro(quadro, aplicar_largura_minima=True)
                for quadro in imagens
            ]
            self.quadros_esquerda = [
                pygame.transform.flip(quadro, True, False)
                for quadro in self.quadros
            ]
            self.quadros_ataque = [
                _escalar_quadro(quadro, aplicar_largura_minima=False)
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
        self.alcance_visao = max(42, int(largura * 0.75))
        self.atacando = False
        self.timer_preparacao = 0
        self.timer_ataque = 0
        self.cooldown_ataque = 0
        self.hitbox_ataque = None
        self.dano_ataque = 20
        self.largura_golpe = max(26, int(largura * 0.5))
        self.altura_golpe = max(20, int(altura * 0.5))
        self.forca_recuo_x = 7.0
        self.forca_recuo_y = -5.5
        self.golpe_processado = False

    @staticmethod
    def _tem_chao_a_frente(rect, deslocamento_x, deslocamento_y, blocos):
        if deslocamento_x == 0:
            return True

        rect_previsto = rect.move(deslocamento_x, int(deslocamento_y))
        x_sensor = (
            rect_previsto.right - 1
            if deslocamento_x > 0
            else rect_previsto.left
        )
        sensor = pygame.Rect(x_sensor, rect_previsto.bottom, 1, 1)
        return any(sensor.colliderect(bloco) for bloco in blocos)

    def atualizar(self, blocos, jogador_rect=None, hitbox_escudo=None):
        if not self.esta_vivo:
            return
# Dano, tempo de invulnerabilidade/cooldown de ataques, recuo por golpes levados ou dados.
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
                self.golpe_processado = False
                self.timer_ataque = self.DURACAO_ATAQUE
## Hitbox
        if self.atacando:
            self.timer_ataque -= 1
            largura_golpe = getattr(self, "largura_golpe", 26)
            altura_golpe = getattr(self, "altura_golpe", 20)
            if self.direcao == 1:
                hx = self.rect.right
            else:
                hx = self.rect.left - largura_golpe
            hy = self.rect.bottom - altura_golpe - 6
            self.hitbox_ataque = pygame.Rect(
                hx, hy, largura_golpe, altura_golpe
            )

            if self.timer_ataque <= 0:
                self.atacando = False
                self.golpe_processado = False
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
            dist_y = abs(self.rect.bottom - jogador_rect.bottom)
            dist_x = jogador_rect.centerx - self.rect.centerx
            limite_y = max(32, int(self.rect.height * 0.7))
            if dist_y < limite_y and abs(dist_x) <= self.alcance_visao:
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
        if (
            deslocamento_x != 0
            and self.vel_y >= 0
            and not self._tem_chao_a_frente(
                self.rect, deslocamento_x, self.vel_y, blocos
            )
        ):
            if movimento_patrulha:
                self.direcao *= -1
            self.vel_recuo_x = 0.0
            deslocamento_x = 0

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
# Defesa
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
# Recuo do monstro ao bater no escudo.
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


# método caso jogador tome dano
    def tomar_dano(self, quantidade, direcao_golpe):
        if self.tempo_dano <= 0 and self.esta_vivo:
            self.vida -= quantidade
            self.tempo_dano = 15
            self.atacando = False
            self.timer_preparacao = 0
            self.hitbox_ataque = None
            fx = getattr(self, "forca_recuo_x", 7.0)
            fy = getattr(self, "forca_recuo_y", -5.5)
            self.aplicar_pulinho_recuo(
                direcao_golpe, forca_x=fx, forca_y=fy
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
            y_barra = iy + self.rect.height + 4
            pygame.draw.rect(
                tela,
                (40, 40, 40),
                (ix, y_barra, largura_barra, 8),
            )
            pygame.draw.rect(
                tela,
                (231, 76, 60),
                (ix + 2, y_barra + 2, max(0, vida_proporcional - 4), 4),
            )
            pygame.draw.rect(
                tela,
                (0, 0, 0),
                (ix, y_barra, largura_barra, 8),
                2,
            )


class ChefeSapo2(Inimigo):
    """
    Chefe Sapo Mutante Gigante:
    - Movimentação com animação cíclica dos quadros 1 -> 2 -> 3
    - Ataque 1 (Investida): Pulo horizontal veloz acertando com os chifres (chefe_ataque1 a 4)
    - Ataque 2 (Língua): Disparo de língua comprida com hitbox na ponta da língua (chefe_ataque2-1 a 2-4)
    - IA que alterna taticamente entre os dois ataques
    - Escala colossal proporcional à arena
    """
    DURACAO_QUADRO_MS = 180
    DURACAO_INVESTIDA = 36
    DURACAO_LINGUA = 32
    ESCALA_SPRITE = 2.4

    def __init__(
        self,
        x,
        y,
        largura=162,
        altura=174,
        vida=250,
        velocidade=2,
        quadros_movimento=None,
        quadros_investida=None,
        quadros_lingua=None,
    ):
        super().__init__(
            x, y,
            largura=largura,
            altura=altura,
            vida=vida,
            velocidade=velocidade,
            quadros=quadros_movimento,
        )
        self.alcance_visao = 2000
        self.DISTANCIA_LONGE = 650
        self.alcance_lingua_atual = 350
        self.forca_recuo_x = 2.0
        self.forca_recuo_y = -2.0

        # Fator de escala visual para os sprites de ataque acompanharem o corpo do chefe
        escala = (altura * self.ESCALA_SPRITE) / 540.0

        # Ataque 1: Investida com pulo horizontal (chefe_ataque1 a 4)
        self.quadros_investida = []
        if quadros_investida:
            for q in quadros_investida:
                w_sc = round(q.get_width() * escala)
                h_sc = round(q.get_height() * escala)
                self.quadros_investida.append(pygame.transform.scale(q, (w_sc, h_sc)))
        self.quadros_investida_esquerda = [
            pygame.transform.flip(q, True, False) for q in self.quadros_investida
        ]

        # Ataque 2: Língua comprida (chefe_ataque2-1 a 2-4)
        self.quadros_lingua = []
        if quadros_lingua:
            for q in quadros_lingua:
                w_sc = round(q.get_width() * escala)
                h_sc = round(q.get_height() * escala)
                self.quadros_lingua.append(pygame.transform.scale(q, (w_sc, h_sc)))
        self.quadros_lingua_esquerda = [
            pygame.transform.flip(q, True, False) for q in self.quadros_lingua
        ]

# Parte do sapo/boss final
class ChefeSapo(Inimigo):
    """
    Chefe Sapo Mutante Gigante:
    - Movimentação com animação cíclica dos quadros 1 -> 2 -> 3
    - Ataque 1 (Investida): Pulo horizontal veloz acertando com os chifres (chefe_ataque1 a 4)
    - Ataque 2 (Língua): Disparo de língua comprida com hitbox na ponta da língua (chefe_ataque2-1 a 2-4)
    - IA que alterna taticamente entre os dois ataques
    - Escala colossal proporcional à arena
    """
    DURACAO_QUADRO_MS = 180
    DURACAO_INVESTIDA = 36
    DURACAO_LINGUA = 32
    ESCALA_SPRITE = 2.4

    def __init__(
        self,
        x,
        y,
        largura=162,
        altura=174,
        vida=250,
        velocidade=2,
        quadros_movimento=None,
        quadros_investida=None,
        quadros_lingua=None,
    ):
        super().__init__(
            x, y,
            largura=largura,
            altura=altura,
            vida=vida,
            velocidade=velocidade,
            quadros=quadros_movimento,
        )
        self.alcance_visao = 2000
        self.DISTANCIA_LONGE = 650
        self.alcance_lingua_atual = 350
        self.forca_recuo_x = 2.0
        self.forca_recuo_y = -2.0

        # Fator de escala visual para os sprites de ataque acompanharem o corpo do chefe
        escala = (altura * self.ESCALA_SPRITE) / 540.0

        # Ataque 1: Investida com pulo horizontal (chefe_ataque1 a 4)
        self.quadros_investida = []
        if quadros_investida:
            for q in quadros_investida:
                w_sc = round(q.get_width() * escala)
                h_sc = round(q.get_height() * escala)
                self.quadros_investida.append(pygame.transform.scale(q, (w_sc, h_sc)))
        self.quadros_investida_esquerda = [
            pygame.transform.flip(q, True, False) for q in self.quadros_investida
        ]

        # Ataque 2: Língua comprida (chefe_ataque2-1 a 2-4)
        self.quadros_lingua = []
        if quadros_lingua:
            for q in quadros_lingua:
                w_sc = round(q.get_width() * escala)
                h_sc = round(q.get_height() * escala)
                self.quadros_lingua.append(pygame.transform.scale(q, (w_sc, h_sc)))
        self.quadros_lingua_esquerda = [
            pygame.transform.flip(q, True, False) for q in self.quadros_lingua
        ]

        # Fatias para esticamento dinâmico da língua a longas distâncias
        self.lingua_corpo = None
        self.lingua_haste = None
        self.lingua_ponta = None
        self._surf_lingua_cache = None
        self._surf_lingua_cache_esq = None
        if self.quadros_lingua and len(self.quadros_lingua) > 1:
            q2 = self.quadros_lingua[1]
            h = q2.get_height()
            w = q2.get_width()
            c_x = min(356, int(w * 0.62))
            h_w = min(77, int(w * 0.14))
            p_w = w - c_x - h_w
            if c_x > 0 and h_w > 0 and p_w > 0:
                self.lingua_corpo = q2.subsurface((0, 0, c_x, h))
                self.lingua_haste = q2.subsurface((c_x, 0, h_w, h))
                self.lingua_ponta = q2.subsurface((c_x + h_w, 0, p_w, h))

        self.tipo_ataque_atual = "investida"
        self.ultimo_ataque_usado = "lingua"
        self.cooldown_ataque = 40
        self.pulo_investida_executado = False
        self.golpe_processado = False

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
            self.vel_recuo_x *= 0.88
        else:
            self.vel_recuo_x = 0.0

        # Preparação do golpe
        if self.timer_preparacao > 0:
            self.timer_preparacao -= 1
            if self.timer_preparacao <= 0:
                self.atacando = True
                self.golpe_processado = False
                self.pulo_investida_executado = False
                if self.tipo_ataque_atual == "investida":
                    self.timer_ataque = self.DURACAO_INVESTIDA
                    self.dano_ataque = 35
                else:
                    self.timer_ataque = self.DURACAO_LINGUA
                    self.dano_ataque = 25
                    alcance = getattr(self, "alcance_lingua_atual", 350)
                    if self.lingua_corpo and self.lingua_haste and self.lingua_ponta:
                        c_w, h = self.lingua_corpo.get_size()
                        p_w, _ = self.lingua_ponta.get_size()
                        w_haste = max(self.lingua_haste.get_width(), alcance - 296)
                        surf = pygame.Surface((c_w + w_haste + p_w, h), pygame.SRCALPHA)
                        surf.blit(self.lingua_corpo, (0, 0))
                        surf.blit(pygame.transform.scale(self.lingua_haste, (w_haste, h)), (c_w, 0))
                        surf.blit(self.lingua_ponta, (c_w + w_haste, 0))
                        self._surf_lingua_cache = surf
                        self._surf_lingua_cache_esq = pygame.transform.flip(surf, True, False)
                    else:
                        self._surf_lingua_cache = None
                        self._surf_lingua_cache_esq = None

        # Execução ativa do golpe
        if self.atacando:
            self.timer_ataque -= 1
            if self.tipo_ataque_atual == "investida":
                progresso = self.DURACAO_INVESTIDA - self.timer_ataque
                idx_quadro = min(3, progresso * 4 // self.DURACAO_INVESTIDA)

                # Nos quadros 1 e 2: Salto horizontal veloz acertando os chifres
                if idx_quadro in (1, 2):
                    if not self.pulo_investida_executado:
                        self.vel_recuo_x = self.direcao * 14.0
                        self.vel_y = -6.0
                        self.pulo_investida_executado = True

                    # Hitbox nos chifres à frente do salto cobrindo a altura do jogador
                    largura_chifre = 110
                    altura_chifre = 110
                    if self.direcao == 1:
                        hx = self.rect.right - 10
                    else:
                        hx = self.rect.left + 10 - largura_chifre
                    hy = self.rect.bottom - 130
                    self.hitbox_ataque = pygame.Rect(hx, hy, largura_chifre, altura_chifre)
                else:
                    self.hitbox_ataque = None

                if self.timer_ataque <= 0:
                    self.atacando = False
                    self.golpe_processado = False
                    self.hitbox_ataque = None
                    self.cooldown_ataque = 65
                    self.ultimo_ataque_usado = "investida"

            elif self.tipo_ataque_atual == "lingua":
                progresso = self.DURACAO_LINGUA - self.timer_ataque
                idx_quadro = min(3, progresso * 4 // self.DURACAO_LINGUA)

                # Nos quadros 1 e 2: Língua comprida totalmente esticada, hitbox na ponta tóxica da língua
                if idx_quadro in (1, 2):
                    largura_ponta = 110
                    altura_ponta = 75
                    alcance = getattr(self, "alcance_lingua_atual", 350)
                    if self.direcao == 1:
                        hx = self.rect.right + alcance - largura_ponta
                    else:
                        hx = self.rect.left - alcance
                    hy = self.rect.bottom - 110
                    self.hitbox_ataque = pygame.Rect(hx, hy, largura_ponta, altura_ponta)
                else:
                    self.hitbox_ataque = None

                if self.timer_ataque <= 0:
                    self.atacando = False
                    self.golpe_processado = False
                    self.hitbox_ataque = None
                    self.cooldown_ataque = 55
                    self.ultimo_ataque_usado = "lingua"
        else:
            self.hitbox_ataque = None

        # Tomada de decisão de ataque pela IA
        if (
            jogador_rect is not None
            and self.tempo_atordoado <= 0
            and not self.atacando
            and self.timer_preparacao <= 0
            and self.cooldown_ataque <= 0
        ):
            dist_x = jogador_rect.centerx - self.rect.centerx
            dist_y = abs(self.rect.bottom - jogador_rect.bottom)
            distancia = abs(dist_x)
            if dist_y < 350 and distancia <= self.alcance_visao:
                self.direcao = 1 if dist_x >= 0 else -1

                # REGRA CRÍTICA: Sempre que ficar muito longe do chefe (> metade do mapa), SEMPRE GOLPE DE LÍNGUA!
                if distancia >= self.DISTANCIA_LONGE:
                    self.tipo_ataque_atual = "lingua"
                    self.alcance_lingua_atual = min(distancia + 40, 1600)
                elif distancia > 260:
                    if self.ultimo_ataque_usado != "investida":
                        self.tipo_ataque_atual = "investida"
                    else:
                        self.tipo_ataque_atual = "lingua"
                        self.alcance_lingua_atual = min(distancia + 30, 600)
                else:
                    self.tipo_ataque_atual = "lingua" if self.ultimo_ataque_usado == "investida" else "investida"
                    self.alcance_lingua_atual = 350

                self.timer_preparacao = 20

        # Movimento de patrulha
        movimento_patrulha = 0
        if (
            self.tempo_atordoado <= 0
            and not self.atacando
            and self.timer_preparacao <= 0
            and abs(self.vel_recuo_x) < 1.0
        ):
            movimento_patrulha = self.direcao * self.velocidade

        deslocamento_x = int(movimento_patrulha + self.vel_recuo_x)
        if (
            deslocamento_x != 0
            and self.vel_y >= 0
            and not self._tem_chao_a_frente(
                self.rect, deslocamento_x, self.vel_y, blocos
            )
        ):
            if movimento_patrulha:
                self.direcao *= -1
            self.vel_recuo_x = 0.0
            deslocamento_x = 0

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

        if hitbox_escudo is not None and self.rect.colliderect(hitbox_escudo):
            if self.direcao == 1:
                self.rect.right = hitbox_escudo.left
            else:
                self.rect.left = hitbox_escudo.right

        # Gravidade e física vertical
        self.vel_y += 0.65
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

    def desenhar(self, tela, camera_x, camera_y, largura_tela, altura_tela):
        if not self.esta_vivo:
            return

        ix = self.rect.x - camera_x
        iy = self.rect.y - camera_y

        if -500 < ix < largura_tela + 500 and -500 < iy < altura_tela + 500:
            if self.atacando and self.tipo_ataque_atual == "investida" and self.quadros_investida:
                progresso = self.DURACAO_INVESTIDA - self.timer_ataque
                idx = min(len(self.quadros_investida) - 1, progresso * len(self.quadros_investida) // self.DURACAO_INVESTIDA)
                quadros = self.quadros_investida if self.direcao == 1 else self.quadros_investida_esquerda
                imagem = quadros[idx]
                w_img = imagem.get_width()
                pos_x = ix - 20 if self.direcao == 1 else ix + self.rect.width - w_img + 20
                pos_y = iy + self.rect.height - imagem.get_height()
                tela.blit(imagem, (pos_x, pos_y))

            elif self.atacando and self.tipo_ataque_atual == "lingua" and self.quadros_lingua:
                progresso = self.DURACAO_LINGUA - self.timer_ataque
                idx = min(len(self.quadros_lingua) - 1, progresso * len(self.quadros_lingua) // self.DURACAO_LINGUA)

                if idx in (1, 2) and self._surf_lingua_cache is not None:
                    imagem = self._surf_lingua_cache if self.direcao == 1 else self._surf_lingua_cache_esq
                    w_img = imagem.get_width()
                    pos_x = ix - 20 if self.direcao == 1 else ix + self.rect.width - w_img + 20
                    pos_y = iy + self.rect.height - imagem.get_height()
                    tela.blit(imagem, (pos_x, pos_y))
                else:
                    quadros = self.quadros_lingua if self.direcao == 1 else self.quadros_lingua_esquerda
                    imagem = quadros[idx]
                    w_img = imagem.get_width()
                    pos_x = ix - 20 if self.direcao == 1 else ix + self.rect.width - w_img + 20
                    pos_y = iy + self.rect.height - imagem.get_height()
                    tela.blit(imagem, (pos_x, pos_y))

            elif self.quadros:
                idx = (pygame.time.get_ticks() // self.DURACAO_QUADRO_MS) % len(self.quadros)
                quadros = self.quadros if self.direcao == 1 else self.quadros_esquerda
                imagem = quadros[idx]
                pos_x = ix + (self.rect.width - imagem.get_width()) // 2
                pos_y = iy + self.rect.height - imagem.get_height()
                tela.blit(imagem, (pos_x, pos_y))
            else:
                pygame.draw.rect(tela, (142, 68, 173), (ix, iy, self.rect.width, self.rect.height), border_radius=3)

