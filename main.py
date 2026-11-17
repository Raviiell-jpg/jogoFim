import random
import pygame
import sys
from pathlib import Path
from codigos.mapa.mapa_prototipo import Mapa
from codigos.outros.saude_ import SistemaSaude
from codigos.outros.combate import SistemaCombate
from codigos.outros.inimigos import Inimigo
from codigos.outros.monstros import (
    carregar_imagens_monstros,
    separar_spritesheet,
)

# 1. Configurações Iniciais
pygame.init()
LARGURA_TELA = 1600
ALTURA_TELA = 900
PASTA_PROJETO = Path(__file__).resolve().parent
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Por uma Gota")
relogio = pygame.time.Clock()
GRADE_SPRITES_MONSTROS = {
    "tatu": (2, 2),
    "rato": (2, 2),
    "lagartixa": (1, 4),
}
imagens_monstros = carregar_imagens_monstros()
nomes_monstros_ausentes = [
    nome for nome in GRADE_SPRITES_MONSTROS if nome not in imagens_monstros
]
if nomes_monstros_ausentes:
    raise FileNotFoundError(
        "Sprites de monstros ausentes: " + ", ".join(nomes_monstros_ausentes)
    )
quadros_monstros = [
    separar_spritesheet(imagens_monstros[nome], linhas, colunas)
    for nome, (linhas, colunas) in GRADE_SPRITES_MONSTROS.items()
]

# Instancia os módulos
mapa = Mapa()
saude = SistemaSaude(vida_maxima=100)
combate = SistemaCombate()


def criar_inimigos():
    return [
        Inimigo(
            x,
            y,
            quadros=random.choice(quadros_monstros),
        )
        for x, y in mapa.inimigos_iniciais
    ]


inimigos = criar_inimigos()

# Fundo
try:
    imagem_fundo = pygame.image.load(
        str(PASTA_PROJETO / "fundos" / "predio.png")
    ).convert()
    tem_imagem_fundo = True
except pygame.error:
    tem_imagem_fundo = False

# Sprites do jogador
PASTA_SPRITES = PASTA_PROJETO / "prites"
TAMANHO_SPRITE = (48, 92)


def carregar_quadros_spritesheet(nome_arquivo, quantidade_quadros, largura_fixa=None):
    folha = pygame.image.load(str(PASTA_SPRITES / nome_arquivo)).convert_alpha()
    largura_folha, altura_folha = folha.get_size()
    quadros = []

    for indice in range(quantidade_quadros):
        inicio_x = indice * largura_folha // quantidade_quadros
        fim_x = (indice + 1) * largura_folha // quantidade_quadros
        quadro = folha.subsurface(
            (inicio_x, 0, fim_x - inicio_x, altura_folha)
        ).copy()
        limites_visiveis = quadro.get_bounding_rect(min_alpha=8)
        if limites_visiveis.width == 0 or limites_visiveis.height == 0:
            raise ValueError(
                f"O quadro {indice + 1} de {nome_arquivo} está vazio."
            )
        quadro = quadro.subsurface(limites_visiveis).copy()

        if largura_fixa is None:
            largura = round(
                quadro.get_width() * TAMANHO_SPRITE[1] / quadro.get_height()
            )
        else:
            largura = largura_fixa
        quadros.append(
            pygame.transform.scale(
                quadro, (max(1, largura), TAMANHO_SPRITE[1])
            )
        )

    return quadros

quadros_pulo = carregar_quadros_spritesheet("pulo.png", 2)
quadros_andando = carregar_quadros_spritesheet("adnar.png", 4, largura_fixa=48)
quadros_ataque = carregar_quadros_spritesheet("luta.png", 3)
quadros_defesa = carregar_quadros_spritesheet("defesa.png", 2)

sprite_parado = quadros_andando[0]

quadros_andando_esquerda = [
    pygame.transform.flip(quadro, True, False) for quadro in quadros_andando
]
quadros_ataque_esquerda = [
    pygame.transform.flip(quadro, True, False) for quadro in quadros_ataque
]
quadros_defesa_esquerda = [
    pygame.transform.flip(quadro, True, False) for quadro in quadros_defesa
]
quadros_pulo_esquerda = [
    pygame.transform.flip(quadro, True, False) for quadro in quadros_pulo
]
sprite_parado_esquerda = pygame.transform.flip(sprite_parado, True, False)

# Jogador e Física
jogador_rect = pygame.Rect(mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1], 24, 30)
vel_x = 0
vel_y = 0
vel_recuo_x = 0.0
velocidade_movimento = 5
gravidade = 0.75
forca_pulo = -15.5
no_chao = False
pulando = False
direcao_jogador = 1

coyote_timer = 0
buffer_pulo_timer = 0
COYOTE_MAX = 7
BUFFER_MAX = 7

def reiniciar_jogo():
    global vel_x, vel_y, vel_recuo_x, no_chao, pulando, inimigos
    jogador_rect.topleft = mapa.pos_inicial_jogador
    saude.reiniciar()
    combate.parar_defesa()
    inimigos = criar_inimigos()
    vel_x = 0
    vel_y = 0
    vel_recuo_x = 0.0
    no_chao = False
    pulando = False

# Loop Principal
executando = True
while executando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        if evento.type == pygame.KEYDOWN:
            if not saude.esta_vivo():
                if evento.key == pygame.K_r:
                    reiniciar_jogo()
            else:
                # Pulo
                if evento.key == pygame.K_SPACE or evento.key == pygame.K_UP:
                    buffer_pulo_timer = BUFFER_MAX
                
                # Ataque (J ou Z)
                if evento.key == pygame.K_j or evento.key == pygame.K_z:
                    combate.tentar_atacar()

                # Defesa (K ou X)
                if evento.key == pygame.K_k or evento.key == pygame.K_x:
                    combate.iniciar_defesa()

        if evento.type == pygame.KEYUP:
            if saude.esta_vivo():
                if (evento.key == pygame.K_SPACE or evento.key == pygame.K_UP) and vel_y < -4:
                    vel_y = -4
                
                # Soltar defesa
                if evento.key == pygame.K_k or evento.key == pygame.K_x:
                    combate.parar_defesa()

    # Atualizações enquanto vivo
    if saude.esta_vivo():
        saude.atualizar()

        teclas = pygame.key.get_pressed()
        vel_x = 0
        
        # Personagem anda mais devagar se estiver defendendo
        vel_atual = velocidade_movimento * 0.4 if combate.defendendo else velocidade_movimento

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            vel_x = -vel_atual
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            vel_x = vel_atual
        if abs(vel_recuo_x) < 1.0:
            combate.atualizar_direcao(vel_x)
        if vel_x < 0:
            direcao_jogador = -1
        elif vel_x > 0:
            direcao_jogador = 1

        # Buffers de salto
        if no_chao:
            coyote_timer = COYOTE_MAX
        elif coyote_timer > 0:
            coyote_timer -= 1

        if buffer_pulo_timer > 0:
            buffer_pulo_timer -= 1

        if buffer_pulo_timer > 0 and coyote_timer > 0:
            vel_y = forca_pulo
            coyote_timer = 0
            buffer_pulo_timer = 0
            no_chao = False
            pulando = True

        # Gravidade
        vel_y += gravidade
        if vel_y > 15:
            vel_y = 15

        if abs(vel_recuo_x) > 0.1:
            vel_recuo_x *= 0.80
        else:
            vel_recuo_x = 0.0

        # Colisão Eixo X
        deslocamento_x = int(vel_x + vel_recuo_x)
        jogador_rect.x += deslocamento_x
        for bloco in mapa.blocos:
            if jogador_rect.colliderect(bloco):
                if deslocamento_x > 0:
                    jogador_rect.right = bloco.left
                    vel_recuo_x = 0.0
                elif deslocamento_x < 0:
                    jogador_rect.left = bloco.right
                    vel_recuo_x = 0.0

        # Colisão Eixo Y
        jogador_rect.y += int(vel_y)
        no_chao = False
        for bloco in mapa.blocos:
            if jogador_rect.colliderect(bloco):
                if vel_y > 0:
                    jogador_rect.bottom = bloco.top
                    vel_y = 0
                    no_chao = True
                elif vel_y < 0:
                    jogador_rect.top = bloco.bottom
                    vel_y = 0

        if no_chao:
            pulando = False

        combate.atualizar(jogador_rect)

        for inimigo in inimigos:
            inimigo.atualizar(
                mapa.blocos, jogador_rect, combate.hitbox_escudo
            )

            if combate.defendendo and combate.hitbox_escudo is not None:
                if combate.hitbox_escudo.colliderect(inimigo.rect):
                    if combate.direcao == 1:
                        inimigo.rect.left = combate.hitbox_escudo.right
                    else:
                        inimigo.rect.right = combate.hitbox_escudo.left
                    if inimigo.tempo_atordoado <= 0:
                        inimigo.aplicar_pulinho_recuo(
                            combate.direcao, forca_x=6.5, forca_y=-6.0
                        )
                        inimigo.tempo_atordoado = 25

            if combate.atacando and combate.hitbox_ataque is not None:
                if combate.hitbox_ataque.colliderect(inimigo.rect):
                    if inimigo.tomar_dano(
                        combate.dano_ataque, combate.direcao
                    ):
                        vel_recuo_x = -combate.direcao * combate.forca_recuo_x
                        vel_y = combate.forca_recuo_y
                        no_chao = False

            if (
                inimigo.esta_vivo
                and inimigo.atacando
                and inimigo.hitbox_ataque is not None
                and inimigo.hitbox_ataque.colliderect(jogador_rect)
            ):
                bloqueado_pela_frente = (
                    combate.defendendo
                    and (
                        (
                            combate.direcao == 1
                            and inimigo.rect.centerx >= jogador_rect.centerx
                        )
                        or (
                            combate.direcao == -1
                            and inimigo.rect.centerx <= jogador_rect.centerx
                        )
                    )
                )
                if not bloqueado_pela_frente and saude.tomar_dano(
                    inimigo.dano_ataque
                ):
                    vel_y = -8
                    direcao_impacto = (
                        -1
                        if inimigo.rect.centerx > jogador_rect.centerx
                        else 1
                    )
                    vel_recuo_x = direcao_impacto * 6.5

            if inimigo.esta_vivo and jogador_rect.colliderect(inimigo.rect):
                bloqueado_pela_frente = (
                    combate.defendendo
                    and (
                        (
                            combate.direcao == 1
                            and inimigo.rect.centerx >= jogador_rect.centerx
                        )
                        or (
                            combate.direcao == -1
                            and inimigo.rect.centerx <= jogador_rect.centerx
                        )
                    )
                )
                if not bloqueado_pela_frente and saude.tomar_dano(15):
                    vel_y = -8
                    direcao_impacto = (
                        -1
                        if inimigo.rect.centerx > jogador_rect.centerx
                        else 1
                    )
                    vel_recuo_x = direcao_impacto * 6.0

        inimigos = [inimigo for inimigo in inimigos if inimigo.esta_vivo]

        # Dano com mitigação pelo escudo
        for espinho in mapa.espinhos:
            if jogador_rect.colliderect(espinho):
                dano_calculado = combate.calcular_dano_recebido(25)
                if saude.tomar_dano(dano_calculado):
                    vel_y = -7  # Pequeno recuo
                break

        # Coleta de kits médicos
        for kit in mapa.kits_medicos[:]:
            if jogador_rect.colliderect(kit):
                if saude.curar(25):
                    mapa.kits_medicos.remove(kit)

        # Coleta de moedas
        for moeda in mapa.moedas[:]:
            if jogador_rect.colliderect(moeda):
                mapa.moedas.remove(moeda)

    # Câmera
    camera_x = jogador_rect.centerx - LARGURA_TELA // 2
    camera_y = jogador_rect.centery - ALTURA_TELA // 2
    camera_x = max(0, min(camera_x, mapa.largura - LARGURA_TELA))
    camera_y = max(0, min(camera_y, mapa.altura - ALTURA_TELA))

    # Renderização de fundo
    if tem_imagem_fundo:
        fx = int(-camera_x * 0.25) % LARGURA_TELA
        fy = int(-camera_y * 0.25) % ALTURA_TELA
        tela.blit(imagem_fundo, (fx - LARGURA_TELA, fy - ALTURA_TELA))
        tela.blit(imagem_fundo, (fx, fy - ALTURA_TELA))
        tela.blit(imagem_fundo, (fx - LARGURA_TELA, fy))
        tela.blit(imagem_fundo, (fx, fy))
    else:
        tela.fill((30, 32, 40))

    # Desenho do mapa
    mapa.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA)

    # Desenho dos inimigos
    for inimigo in inimigos:
        inimigo.desenhar(
            tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA
        )

    # Desenho do Jogador
    if saude.esta_vivo() and saude.deve_desenhar_jogador():
        jt = pygame.Rect(
            jogador_rect.x - camera_x,
            jogador_rect.y - camera_y,
            jogador_rect.width,
            jogador_rect.height,
        )

        if combate.atacando:
            progresso_ataque = combate.duracao_ataque - combate.timer_ataque
            indice_quadro = min(
                progresso_ataque * len(quadros_ataque)
                // combate.duracao_ataque,
                len(quadros_ataque) - 1,
            )
            sprite_atual = (
                quadros_ataque[indice_quadro]
                if direcao_jogador > 0
                else quadros_ataque_esquerda[indice_quadro]
            )
        elif combate.defendendo:
            indice_quadro = (
                pygame.time.get_ticks() // 220
            ) % len(quadros_defesa)
            sprite_atual = (
                quadros_defesa[indice_quadro]
                if direcao_jogador > 0
                else quadros_defesa_esquerda[indice_quadro]
            )
        elif pulando:
            indice_quadro = (pygame.time.get_ticks() // 180) % len(quadros_pulo)
            sprite_atual = (
                quadros_pulo[indice_quadro]
                if direcao_jogador > 0
                else quadros_pulo_esquerda[indice_quadro]
            )
        elif vel_x != 0:
            indice_quadro = (pygame.time.get_ticks() // 120) % len(quadros_andando)
            sprite_atual = (
                quadros_andando[indice_quadro]
                if direcao_jogador > 0
                else quadros_andando_esquerda[indice_quadro]
            )
        else:
            sprite_atual = (
                sprite_parado if direcao_jogador > 0 else sprite_parado_esquerda
            )

        # Posiciona o sprite alinhado aos pés
        sprite_rect = sprite_atual.get_rect(midbottom=(jt.centerx, jt.bottom))
        tela.blit(sprite_atual, sprite_rect)

    # HUD e Game Over
    saude.desenhar_hud(tela)
    if not saude.esta_vivo():
        saude.desenhar_game_over(tela, LARGURA_TELA, ALTURA_TELA)

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()
sys.exit()