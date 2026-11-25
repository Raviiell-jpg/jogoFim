import math
import pygame


class SistemaCombate:
    """
    Sistema avançado de combate e defesa do jogador.
    - Hitbox de ataque com altura e alcance ampliados para cobrir todo o arco frontal.
    - Hitbox de escudo com altura completa cobrindo da cabeça aos pés.
    - Mecânica de Quebra de Guarda contra o Chefe:
      * O jogador consegue bloquear até 2 golpes do Chefe.
      * No 3º golpe consecutivo, a guarda quebra: o jogador toma dano integral.
      * O escudo fica desativado temporariamente (cooldown de recuperação).
      * Após o cooldown, o escudo se restaura automaticamente e volta a funcionar.
    """
    def __init__(self):
        # Direção: 1 = Direita, -1 = Esquerda
        self.direcao = 1

        # Estados
        self.atacando = False
        self.defendendo = False

        # Temporizadores de Ataque (em frames a 60 FPS)
        self.duracao_ataque = 12       # Tempo que a hitbox de ataque fica ativa (0.2s)
        self.cooldown_ataque = 25      # Intervalo mínimo entre ataques
        self.timer_ataque = 0
        self.timer_cooldown = 0

        # Dimensões da Hitbox de ataque (Expandidas para cobrir toda a altura do personagem)
        self.alcance_ataque = 44       # Alcance frontal de 44px
        self.altura_ataque = 50        # Altura de 50px (cobre da cabeça aos pés durante o golpe)
        self.hitbox_ataque = None
        self.hitbox_escudo = None

        # Dimensões do Escudo
        self.largura_escudo = 12       # Barreira de 12px de espessura

        # Dano e Física
        self.dano_ataque = 35
        self.forca_recuo_x = 7.5
        self.forca_recuo_y = -6.5
        self.reducao_defesa = 0.8      # 80% de redução de dano ao defender ataques menores

        # Sistema de Quebra de Guarda do Chefe
        self.bloqueios_chefe = 0               # Quantidade de golpes do chefe bloqueados
        self.limite_bloqueios_chefe = 2        # Suporta exatamente 2 golpes antes de quebrar no 3º
        self.timer_escudo_quebrado = 0         # Temporizador de escudo inoperante (frames)
        self.duracao_quebra_guarda = 120       # 2 segundos (120 frames a 60 FPS)
        self.timer_recuperacao_golpe = 0       # Tempo sem tomar golpe do chefe para zerar contador
        self.tempo_alerta_quebra = 0           # Efeito visual de quebra
        self.acabou_de_recuperar = False       # Flag para sinalizar notificação de retorno

    def atualizar_direcao(self, vel_x):
        """Atualiza o lado para onde o personagem está virado."""
        if vel_x > 0:
            self.direcao = 1
        elif vel_x < 0:
            self.direcao = -1

    def pode_defender(self):
        """Verifica se o escudo está disponível (não quebrado)."""
        return self.timer_escudo_quebrado <= 0

    def tentar_atacar(self):
        """Dispara o ataque se não estiver em cooldown nem defendendo."""
        if self.timer_cooldown <= 0 and not self.defendendo:
            self.atacando = True
            self.timer_ataque = self.duracao_ataque
            self.timer_cooldown = self.cooldown_ataque
            return True
        return False

    def iniciar_defesa(self):
        """Ativa o escudo caso não esteja atacando e o escudo não esteja quebrado."""
        if not self.atacando and self.pode_defender():
            self.defendendo = True

    def parar_defesa(self):
        """Desativa o escudo."""
        self.defendendo = False
        self.hitbox_escudo = None

    def registrar_bloqueio_chefe(self):
        """
        Registra um golpe do Chefe contra o escudo.
        Retorna:
          - True: golpe absorvido com sucesso (1º ou 2º golpe).
          - False: quebra de guarda (3º golpe em diante) -> o jogador leva dano integral!
        """
        if not self.defendendo or not self.pode_defender():
            return False

        self.bloqueios_chefe += 1
        self.timer_recuperacao_golpe = 300  # 5 segundos sem golpes do chefe para zerar

        if self.bloqueios_chefe > self.limite_bloqueios_chefe:
            # 3º Golpe: Guarda Quebrada!
            self.quebrar_guarda()
            return False

        return True

    def quebrar_guarda(self, duracao=None):
        """Força a quebra do escudo, desativando a defesa e iniciando o cooldown."""
        self.timer_escudo_quebrado = duracao if duracao is not None else self.duracao_quebra_guarda
        self.bloqueios_chefe = 0
        self.defendendo = False
        self.hitbox_escudo = None
        self.tempo_alerta_quebra = 40

    def atualizar(self, jogador_rect):
        """Atualiza hitboxes, temporizadores de ataque, defesa e recuperação do escudo."""
        # Recuperação do Escudo Quebrado
        if self.timer_escudo_quebrado > 0:
            self.timer_escudo_quebrado -= 1
            self.defendendo = False
            self.hitbox_escudo = None
            if self.timer_escudo_quebrado == 0:
                self.bloqueios_chefe = 0
                self.acabou_de_recuperar = True

        # Janela de alívio sem golpes do chefe
        if self.timer_recuperacao_golpe > 0:
            self.timer_recuperacao_golpe -= 1
            if self.timer_recuperacao_golpe <= 0:
                self.bloqueios_chefe = 0

        if self.tempo_alerta_quebra > 0:
            self.tempo_alerta_quebra -= 1

        # Temporizadores de Ataque
        if self.timer_ataque > 0:
            self.timer_ataque -= 1
            if self.timer_ataque <= 0:
                self.atacando = False
                self.hitbox_ataque = None

        if self.timer_cooldown > 0:
            self.timer_cooldown -= 1

        # Hitbox de Ataque ampliada à frente do jogador
        if self.atacando:
            if self.direcao == 1:
                x = jogador_rect.right
            else:
                x = jogador_rect.left - self.alcance_ataque

            # Centralizado verticalmente com boa cobertura superior e inferior
            y = jogador_rect.centery - (self.altura_ataque // 2)
            self.hitbox_ataque = pygame.Rect(x, y, self.alcance_ataque, self.altura_ataque)
        else:
            self.hitbox_ataque = None

        # Hitbox de Escudo abrangendo do chão até acima da cabeça
        if self.defendendo and self.pode_defender():
            altura_escudo = jogador_rect.height + 4
            largura_escudo = self.largura_escudo
            if self.direcao == 1:
                x_escudo = jogador_rect.right
            else:
                x_escudo = jogador_rect.left - largura_escudo

            y_escudo = jogador_rect.bottom - altura_escudo
            self.hitbox_escudo = pygame.Rect(
                x_escudo, y_escudo, largura_escudo, altura_escudo
            )
        else:
            self.hitbox_escudo = None

    def calcular_dano_recebido(self, dano_base):
        """Calcula o dano final considerando se está com o escudo levantado."""
        if self.defendendo and self.pode_defender():
            dano_final = dano_base * (1.0 - self.reducao_defesa)
            return int(round(dano_final, 8))
        return dano_base

    def desenhar(self, tela, camera_x, camera_y, jogador_rect):
        """Renderiza visualmente o efeito de ataque, escudo dinâmico e aviso de guarda quebrada."""
        # Efeito visual do Escudo com alerta de carga
        if self.defendendo and self.hitbox_escudo is not None:
            escudo_rect = self.hitbox_escudo.move(-camera_x, -camera_y)

            # Determina cor e pulso conforme a integridade da guarda
            if self.bloqueios_chefe == 0:
                cor_fundo = (0, 191, 255)      # Azul ciano resistente
                cor_borda = (255, 255, 255)
            elif self.bloqueios_chefe == 1:
                cor_fundo = (255, 195, 30)      # Amarelo/âmbar de advertência
                cor_borda = (255, 250, 180)
            else:
                # 2 golpes: prestes a quebrar no próximo! Efeito pulsante vermelho
                pulso = int(40 * math.sin(pygame.time.get_ticks() * 0.02))
                cor_fundo = (min(255, 230 + pulso), 50, 40)
                cor_borda = (255, 220, 220)

            pygame.draw.rect(tela, cor_fundo, escudo_rect, border_radius=3)
            pygame.draw.rect(tela, cor_borda, escudo_rect, 2, border_radius=3)

            # Indicadores visuais de integridade da guarda (2 pips flutuantes)
            px = escudo_rect.centerx - 10
            py = escudo_rect.top - 12
            for i in range(2):
                pip_rect = pygame.Rect(px + i * 11, py, 9, 6)
                if i < (2 - self.bloqueios_chefe):
                    pip_cor = (0, 240, 255) if self.bloqueios_chefe == 0 else (255, 210, 40)
                    pygame.draw.rect(tela, pip_cor, pip_rect, border_radius=1)
                else:
                    pygame.draw.rect(tela, (240, 40, 40), pip_rect, border_radius=1)
                pygame.draw.rect(tela, (255, 255, 255), pip_rect, 1, border_radius=1)

        # 3. Efeito visual de Guarda Quebrada (cooldown de recuperação)
        if self.timer_escudo_quebrado > 0:
            jx = jogador_rect.centerx - camera_x
            jy = jogador_rect.top - camera_y - 20

            # Barra de recuperação do escudo
            largura_barra = 40
            altura_barra = 6
            progresso = 1.0 - (self.timer_escudo_quebrado / self.duracao_quebra_guarda)
            comp_preenchido = int(largura_barra * progresso)

            bx = jx - largura_barra // 2
            by = jy

            # Fundo e barra de progresso de recuperação
            pygame.draw.rect(tela, (40, 40, 40, 180), (bx - 2, by - 2, largura_barra + 4, altura_barra + 4), border_radius=2)
            pygame.draw.rect(tela, (180, 40, 40), (bx, by, largura_barra, altura_barra), border_radius=2)
            if comp_preenchido > 0:
                pygame.draw.rect(tela, (0, 220, 120), (bx, by, comp_preenchido, altura_barra), border_radius=2)
            pygame.draw.rect(tela, (255, 255, 255), (bx, by, largura_barra, altura_barra), 1, border_radius=2)
