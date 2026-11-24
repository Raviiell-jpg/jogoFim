"""
========================================================================
                      POR UMA GOTA - UM SERTÃO RADIOATIVO
========================================================================
Loop Principal do Jogo (Pygame)
Unifica:
- Resolução 1600x900 com física suave (Coyote time, Jump buffer)
- Animações em spritesheet do jogador (pulo, corrida, ataque e defesa)
- Monstros mutantes animados (tatu, rato, lagartixa) com IA e recuo
- Sistema de portas de segurança com interação [E] e sprites oficiais
- Escadas industriais funcionais com subida/descida vertical
- Armadilhas de teto desabando com partículas de aviso radioativo
- Sistema completo de Speedrun (cronômetro, recordes e salvamento SQLite)
- Ferramentas integradas de Game Master (CTRL+F12, God Mode, Insta-kill, Teleporte)
- Totalmente portátil (sem caminhos absolutos, funciona em qualquer pasta)
"""

import argparse
import math
import random
import subprocess
import sys
import time
from pathlib import Path

import pygame

# Diretório raiz portátil
PASTA_PROJETO = Path(__file__).resolve().parent
if str(PASTA_PROJETO) not in sys.path:
    sys.path.insert(0, str(PASTA_PROJETO))

from banco_dados import BancoDados
from codigos.mapa.mapa_prototipo import Mapa
from codigos.mapa.mapa_chefe import MapaChefe
from codigos.outros.combate import SistemaCombate
from codigos.outros.inimigos import Inimigo, ChefeSapo
from codigos.outros.monstros import (
    carregar_imagens_monstros,
    separar_spritesheet,
)
from codigos.outros.saude_ import SistemaSaude

# ------------------------------------------------------------------------
# 1. PARÂMETROS DE LINHA DE COMANDO E SESSÃO DO USUÁRIO
# ------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Por uma Gota - Um Sertão Radioativo")
parser.add_argument("--modo", choices=["normal", "speedrun"], default="normal", help="Modo de jogo")
parser.add_argument("--usuario", type=str, default="", help="Nome do jogador")
args, _ = parser.parse_known_args()

banco = BancoDados()
sessao_salva = banco.obter_sessao_atual()
usuario_info = None

if args.usuario:
    nome_usuario = args.usuario
    usuario_info = banco.obter_usuario_por_nome(nome_usuario)
    papel_usuario = usuario_info.get("papel", "jogador") if usuario_info else "jogador"
    usuario_id = usuario_info.get("id") if usuario_info else None
elif sessao_salva:
    nome_usuario = sessao_salva.get("usuario", "Sobrevivente")
    papel_usuario = sessao_salva.get("papel", "jogador")
    usuario_id = sessao_salva.get("id")
else:
    nome_usuario = "Visitante"
    papel_usuario = "jogador"
    usuario_id = None

eh_gm = (papel_usuario.lower() == "gm") or bool(usuario_info and usuario_info.get("is_gm")) or bool(sessao_salva and sessao_salva.get("is_gm"))
modo_speedrun = (args.modo == "speedrun")

# ------------------------------------------------------------------------
# 2. INICIALIZAÇÃO DE VÍDEO, ÁUDIO E FONTES
# ------------------------------------------------------------------------
pygame.init()
LARGURA_TELA = 1600
ALTURA_TELA = 900
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Por uma Gota - Um Sertão Radioativo")
relogio = pygame.time.Clock()

# Trilha sonora
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    caminho_musica = PASTA_PROJETO / "musicas" / "sallyFace.mp3"
    if not caminho_musica.is_file():
        caminho_musica = PASTA_PROJETO / "musicas" / "noImNotaHuman.mp3"
    if caminho_musica.is_file():
        pygame.mixer.music.load(str(caminho_musica))
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Aviso de áudio (não crítico): {e}")

# Fonte retrô pixel art (PressStart2P) com fallback robusto
def carregar_fonte(tamanho, negrito=True, preferir_pixel=True):
    if preferir_pixel:
        caminho_pixel = PASTA_PROJETO / "PressStart2P.ttf"
        if caminho_pixel.is_file():
            try:
                fonte_pixel = pygame.font.Font(str(caminho_pixel), tamanho)
                fonte_pixel.set_bold(negrito)
                return fonte_pixel
            except Exception:
                pass
    try:
        return pygame.font.SysFont("segoe ui, consolas, arial", tamanho, bold=negrito)
    except Exception:
        return pygame.font.SysFont("consolas", tamanho + 2, bold=negrito)

fonte_titulo = carregar_fonte(28)
fonte_subtitulo = carregar_fonte(16)
fonte_media = carregar_fonte(13)
fonte_timer = carregar_fonte(16)
fonte_normal = carregar_fonte(11)
fonte_pequena = carregar_fonte(9)
fonte_status = carregar_fonte(8, negrito=False)

# Fontes ampliadas para o Modo GM
fonte_gm_titulo = carregar_fonte(16)
fonte_gm_botao = carregar_fonte(10)
fonte_gm_faixa = carregar_fonte(11)
fonte_gm_dica = carregar_fonte(9)
fonte_toast = carregar_fonte(12)

# ------------------------------------------------------------------------
# 3. CARREGAMENTO DE SPRITES E ANIMAÇÕES
# ------------------------------------------------------------------------
# Fundo com paralaxe
try:
    imagem_fundo_predio = pygame.image.load(str(PASTA_PROJETO / "fundos" / "predio.png")).convert()
    imagem_fundo_predio = pygame.transform.scale(imagem_fundo_predio, (LARGURA_TELA, ALTURA_TELA))
    tem_imagem_fundo_predio = True
except Exception:
    tem_imagem_fundo_predio = False

try:
    imagem_fundo_caverna = pygame.image.load(str(PASTA_PROJETO / "fundos" / "fundo.png")).convert()
    imagem_fundo_caverna = pygame.transform.scale(imagem_fundo_caverna, (LARGURA_TELA, ALTURA_TELA))
    tem_imagem_fundo_caverna = True
except Exception:
    tem_imagem_fundo_caverna = False

# Sprites do Jogador
PASTA_SPRITES = PASTA_PROJETO / "prites"
TAMANHO_SPRITE = (48, 92)

def carregar_quadros_spritesheet(nome_arquivo, quantidade_quadros, largura_fixa=None):
    caminho = PASTA_SPRITES / nome_arquivo
    if not caminho.is_file():
        surf_padrao = pygame.Surface((48, 92), pygame.SRCALPHA)
        surf_padrao.fill((57, 255, 20, 180))
        return [surf_padrao] * quantidade_quadros

    folha = pygame.image.load(str(caminho)).convert_alpha()
    largura_folha, altura_folha = folha.get_size()
    quadros = []

    for indice in range(quantidade_quadros):
        inicio_x = indice * largura_folha // quantidade_quadros
        fim_x = (indice + 1) * largura_folha // quantidade_quadros
        quadro = folha.subsurface((inicio_x, 0, fim_x - inicio_x, altura_folha)).copy()
        limites_visiveis = quadro.get_bounding_rect(min_alpha=8)
        if limites_visiveis.width > 0 and limites_visiveis.height > 0:
            quadro = quadro.subsurface(limites_visiveis).copy()

        largura = largura_fixa if largura_fixa else round(quadro.get_width() * TAMANHO_SPRITE[1] / max(1, quadro.get_height()))
        quadros.append(pygame.transform.scale(quadro, (max(1, largura), TAMANHO_SPRITE[1])))

    return quadros

quadros_pulo = carregar_quadros_spritesheet("pulo.png", 2)
quadros_andando = carregar_quadros_spritesheet("adnar.png", 4, largura_fixa=48)
quadros_ataque = carregar_quadros_spritesheet("luta.png", 3)
quadros_defesa = carregar_quadros_spritesheet("defesa.png", 2)

sprite_parado = quadros_andando[0]

quadros_andando_esq = [pygame.transform.flip(q, True, False) for q in quadros_andando]
quadros_ataque_esq = [pygame.transform.flip(q, True, False) for q in quadros_ataque]
quadros_defesa_esq = [pygame.transform.flip(q, True, False) for q in quadros_defesa]
quadros_pulo_esq = [pygame.transform.flip(q, True, False) for q in quadros_pulo]
sprite_parado_esq = pygame.transform.flip(sprite_parado, True, False)

# Sprites dos Monstros Mutantes
monstros_quadros = {}
try:
    imgs_monstros = carregar_imagens_monstros()
    GRADE_MONSTROS = {"tatu": (2, 2), "rato": (2, 2), "lagartixa": (1, 4)}
    for nome, (lin, col) in GRADE_MONSTROS.items():
        if nome in imgs_monstros:
            q_norm = separar_spritesheet(imgs_monstros[nome], lin, col)
            atk_key = nome + "Ataque"
            q_atk = separar_spritesheet(imgs_monstros[atk_key], lin, col) if atk_key in imgs_monstros else None
            monstros_quadros[nome] = (q_norm, q_atk)
    # Chefe Sapo Mutante:
    # 1. Movimentação (imagens 1, 2 e 3 nessa ordem)
    quadros_chefe_andando = []
    for chave in ["chefe_sapo_1", "chefe_sapo_2", "chefe_sapo_3"]:
        if chave in imgs_monstros:
            quadros_chefe_andando.append(imgs_monstros[chave])
    if not quadros_chefe_andando:
        for chave in ["chefe_and1", "chefe_and2", "chefe_and3"]:
            if chave in imgs_monstros:
                quadros_chefe_andando.append(imgs_monstros[chave])

    # 2. Ataque 1: Investida com pulo horizontal e chifres (chefe_ataque1 a 4)
    quadros_chefe_investida = []
    for chave in ["chefe_ataque1", "chefe_ataque2", "chefe_ataque3", "chefe_ataque4"]:
        if chave in imgs_monstros:
            quadros_chefe_investida.append(imgs_monstros[chave])

    # 3. Ataque 2: Língua comprida com hitbox na ponta (chefe_ataque2-1 a 2-4)
    quadros_chefe_lingua = []
    for chave in ["chefe_ataque2-1", "chefe_ataque2-2", "chefe_ataque2-3", "chefe_ataque2-4"]:
        if chave in imgs_monstros:
            quadros_chefe_lingua.append(imgs_monstros[chave])

    if quadros_chefe_andando:
        monstros_quadros["sapo"] = (quadros_chefe_andando, quadros_chefe_investida)
    elif "sapo_andando" in imgs_monstros:
        q_norm_sapo = separar_spritesheet(imgs_monstros["sapo_andando"], 1, 4)
        q_atk_sapo = separar_spritesheet(imgs_monstros["sapo_ataque1"], 1, 4) if "sapo_ataque1" in imgs_monstros else None
        monstros_quadros["sapo"] = (q_norm_sapo, q_atk_sapo)
except Exception as e:
    print(f"Aviso ao carregar sprites de monstros: {e}")

# ------------------------------------------------------------------------
# 4. INSTANCIAÇÃO DOS MÓDULOS DE JOGO
# ------------------------------------------------------------------------
fase_atual = "predio"  # "predio" ou "chefe"
mapa = Mapa()
saude = SistemaSaude(vida_maxima=100)
combate = SistemaCombate()

total_inimigos_fase = len(mapa.inimigos_iniciais)

def criar_inimigos():
    lista = []
    nomes_disponiveis = [k for k in monstros_quadros.keys() if k != "sapo"] if monstros_quadros else []
    for x, y in mapa.inimigos_iniciais:
        if nomes_disponiveis:
            nome_escolhido = random.choice(nomes_disponiveis)
            q_n, q_a = monstros_quadros[nome_escolhido]
            lista.append(Inimigo(x, y, quadros=q_n, quadros_ataque=q_a))
        else:
            lista.append(Inimigo(x, y))
    return lista

def criar_inimigos_chefe():
    lista = []
    largura_boss = 162
    altura_boss = 174
    for x, y in mapa.inimigos_iniciais:
        pos_y = min(y, 21 * getattr(mapa, "tile_size", 32))
        boss = ChefeSapo(
            x, pos_y,
            largura=largura_boss,
            altura=altura_boss,
            vida=250,
            velocidade=2,
            quadros_movimento=quadros_chefe_andando,
            quadros_investida=quadros_chefe_investida,
            quadros_lingua=quadros_chefe_lingua,
        )
        lista.append(boss)
    return lista

inimigos = criar_inimigos()

# ------------------------------------------------------------------------
# 5. FÍSICA E ESTADOS DO JOGADOR
# ------------------------------------------------------------------------
jogador_rect = pygame.Rect(mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1] - 26, 26, 56)
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

# ------------------------------------------------------------------------
# 6. ESTADOS DE SPEEDRUN E GAME MASTER
# ------------------------------------------------------------------------
# Speedrun
tempo_inicio_ms = pygame.time.get_ticks()
tempo_final_ms = None
corrida_finalizada = False
novo_recorde = False
inimigos_derrotados = 0
recorde_pessoal = banco.obter_recorde_pessoal(usuario_id) if usuario_id else None
dados_tela_final = None

# Game Master
god_mode = False
insta_kill = False
super_velocidade = False
hitbox_debug = False
gm_menu_aberto = False
usou_gm = False
tempo_toast_gm = 0
mensagem_gm_toast = ""
exibir_ranking_tab = False
multiplicador_jogo = 1           # 1 = 60 FPS normal, 2 = 120 FPS Turbo, 3 = 180 FPS Hiperturbo
nivel_velocidade_jogador = 1     # 1 = 5px normal, 2 = 10px rápido, 3 = 16px ultra flash
pulo_infinito = False            # Permite saltar no ar consecutivamente

# Sistema de Pausa (Tecla P)
jogo_pausado = False
momento_pausa_ms = 0
tempo_pausado_acumulado_ms = 0

# Layout Menu de Pausa Padrão (Jogadores)
LARGURA_BOX_PAUSE = 520
ALTURA_BOX_PAUSE = 340
PAUSE_X = (LARGURA_TELA - LARGURA_BOX_PAUSE) // 2
PAUSE_Y = (ALTURA_TELA - ALTURA_BOX_PAUSE) // 2
btn_continuar_rect = pygame.Rect(PAUSE_X + 50, PAUSE_Y + 120, 420, 56)
btn_menu_rect = pygame.Rect(PAUSE_X + 50, PAUSE_Y + 200, 420, 56)

# Layout Menu de Pausa Expandido para Game Master (GM)
LARGURA_BOX_PAUSE_GM = 1060
ALTURA_BOX_PAUSE_GM = 560
PAUSE_GM_X = (LARGURA_TELA - LARGURA_BOX_PAUSE_GM) // 2
PAUSE_GM_Y = (ALTURA_TELA - ALTURA_BOX_PAUSE_GM) // 2
btn_continuar_gm_rect = pygame.Rect(PAUSE_GM_X + 35, PAUSE_GM_Y + 120, 330, 56)
btn_menu_gm_rect = pygame.Rect(PAUSE_GM_X + 35, PAUSE_GM_Y + 195, 330, 56)

# Botões de Cheats do GM no Menu de Pausa (2 colunas, botões largos de 285px)
btn_gm_pause_god = pygame.Rect(PAUSE_GM_X + 425, PAUSE_GM_Y + 80, 285, 52)
btn_gm_pause_fase = pygame.Rect(PAUSE_GM_X + 735, PAUSE_GM_Y + 80, 285, 52)

btn_gm_pause_turbo = pygame.Rect(PAUSE_GM_X + 425, PAUSE_GM_Y + 144, 285, 52)
btn_gm_pause_pulo = pygame.Rect(PAUSE_GM_X + 735, PAUSE_GM_Y + 144, 285, 52)

btn_gm_pause_kill = pygame.Rect(PAUSE_GM_X + 425, PAUSE_GM_Y + 208, 285, 52)
btn_gm_pause_cura = pygame.Rect(PAUSE_GM_X + 735, PAUSE_GM_Y + 208, 285, 52)

btn_gm_pause_vel = pygame.Rect(PAUSE_GM_X + 425, PAUSE_GM_Y + 272, 285, 52)
btn_gm_pause_inicio = pygame.Rect(PAUSE_GM_X + 735, PAUSE_GM_Y + 272, 285, 52)

btn_gm_pause_hitbox = pygame.Rect(PAUSE_GM_X + 425, PAUSE_GM_Y + 336, 285, 52)
btn_gm_pause_admin = pygame.Rect(PAUSE_GM_X + 735, PAUSE_GM_Y + 336, 285, 52)

btn_gm_pause_saida = pygame.Rect(PAUSE_GM_X + 425, PAUSE_GM_Y + 400, 285, 52)
btn_gm_pause_menu_gm = pygame.Rect(PAUSE_GM_X + 735, PAUSE_GM_Y + 400, 285, 52)

def retornar_ao_menu():
    caminho_menu = PASTA_PROJETO / "tela_inicio.py"
    try:
        subprocess.Popen([sys.executable, str(caminho_menu)], cwd=str(PASTA_PROJETO))
    except Exception as e:
        print(f"Erro ao abrir menu principal: {e}")
    pygame.quit()
    sys.exit(0)

def notificar_gm(mensagem):
    global tempo_toast_gm, mensagem_gm_toast
    tempo_toast_gm = 150
    mensagem_gm_toast = mensagem

def registrar_acao_gm(acao, detalhes=""):
    global usou_gm
    usou_gm = True
    banco.registrar_acao_gm(
        usuario_gm=nome_usuario,
        acao=acao,
        detalhes=f"{detalhes} | Speedrun desclassificado" if modo_speedrun else detalhes,
    )
    notificar_gm(f"GM: {acao} | {detalhes}")

def alternar_god_mode():
    global god_mode
    god_mode = not god_mode
    if god_mode:
        saude.vida_atual = saude.vida_maxima
        saude.vida_visual = float(saude.vida_maxima)
    registrar_acao_gm("Modo Deus", "Ativado (Vida Infinita & Imunidade Total)" if god_mode else "Desativado")

def executar_cura_total():
    saude.vida_atual = saude.vida_maxima
    saude.vida_visual = float(saude.vida_maxima)
    saude.tempo_invencivel = 0
    registrar_acao_gm("Cura Total", "Vida e Sede restauradas a 100%")

def executar_insta_kill():
    global inimigos, inimigos_derrotados
    qtd = len(inimigos)
    for ini in inimigos:
        ini.vida = 0
        ini.esta_vivo = False
    inimigos.clear()
    inimigos_derrotados += qtd
    registrar_acao_gm("Insta-Kill", f"{qtd} monstros eliminados instantaneamente")

def executar_teleporte_inicio():
    global vel_x, vel_y, vel_recuo_x
    jogador_rect.size = (26, 56)
    jogador_rect.topleft = (mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1] - 26)
    vel_x = 0
    vel_y = 0
    vel_recuo_x = 0.0
    registrar_acao_gm("Teleporte Início", "Retornado ao ponto de spawn da fase")

def executar_teleporte_saida():
    global vel_x, vel_y, vel_recuo_x
    if mapa.zona_saida:
        jogador_rect.size = (26, 56)
        jogador_rect.topleft = (mapa.zona_saida.x + 10, mapa.zona_saida.bottom - 56)
        vel_x = 0
        vel_y = 0
        vel_recuo_x = 0.0
        registrar_acao_gm("Teleporte Saída", "Movido para a zona de fuga")

def avancar_proxima_fase():
    global fase_atual, mapa, jogador_rect, vel_x, vel_y, vel_recuo_x, inimigos, total_inimigos_fase
    global corrida_finalizada, tempo_final_ms, usou_gm, dados_tela_final, executando, novo_recorde
    if fase_atual == "predio":
        fase_atual = "chefe"
        mapa = MapaChefe()
        jogador_rect.size = (26, 56)
        jogador_rect.topleft = (mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1] - 26)
        vel_x = 0
        vel_y = 0
        vel_recuo_x = 0.0
        combate.bloqueios_chefe = 0
        combate.timer_escudo_quebrado = 0
        inimigos = criar_inimigos_chefe()
        total_inimigos_fase += len(inimigos)
        registrar_acao_gm("Avançar Fase", "Entrou na Fase 2: Caverna do Chefe")
    elif fase_atual == "chefe":
        corrida_finalizada = True
        tempo_final_ms = pygame.time.get_ticks() - tempo_inicio_ms - tempo_pausado_acumulado_ms
        if usuario_id is not None:
            novo_recorde = banco.registrar_speedrun(
                usuario_id=usuario_id,
                tempo_ms=tempo_final_ms,
                inimigos_derrotados=inimigos_derrotados,
                total_inimigos=total_inimigos_fase,
                usou_gm=True,
            )
            recorde_pessoal = banco.obter_recorde_pessoal(usuario_id)
        registrar_acao_gm("Avançar Fase", "Chefe superado -> Fuga Bem-Sucedida (Vitória)!")
        if not modo_speedrun:
            dados_tela_final = {
                "tempo_ms": tempo_final_ms,
                "inimigos_derrotados": inimigos_derrotados,
                "total_inimigos": total_inimigos_fase,
                "novo_recorde": novo_recorde,
                "usou_gm": usou_gm,
            }
            executando = False

def alternar_fase():
    global fase_atual, mapa, jogador_rect, vel_x, vel_y, vel_recuo_x, inimigos, total_inimigos_fase
    if fase_atual == "predio":
        avancar_proxima_fase()
    else:
        fase_atual = "predio"
        mapa = Mapa()
        total_inimigos_fase = len(mapa.inimigos_iniciais)
        jogador_rect.size = (26, 56)
        jogador_rect.topleft = (mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1] - 26)
        vel_x = 0
        vel_y = 0
        vel_recuo_x = 0.0
        combate.bloqueios_chefe = 0
        combate.timer_escudo_quebrado = 0
        inimigos = criar_inimigos()
        registrar_acao_gm("Alternar Fase", "Retornado para Fase 1: Prédio Industrial")

def alternar_pulo_infinito():
    global pulo_infinito
    pulo_infinito = not pulo_infinito
    registrar_acao_gm("Pulo Infinito", "Ativado (Pulos no ar ilimitados)" if pulo_infinito else "Desativado")

def alternar_velocidade_jogo():
    global multiplicador_jogo
    niveis = [1, 2, 3]
    idx = niveis.index(multiplicador_jogo) if multiplicador_jogo in niveis else 0
    multiplicador_jogo = niveis[(idx + 1) % len(niveis)]
    rotulos = {1: "1x Normal (60 FPS)", 2: "2x Turbo (120 FPS)", 3: "3x Hiperturbo (180 FPS)"}
    registrar_acao_gm("Acelerar Jogo", rotulos[multiplicador_jogo])

def alternar_velocidade_jogador():
    global nivel_velocidade_jogador, super_velocidade
    nivel_velocidade_jogador = (nivel_velocidade_jogador % 3) + 1
    super_velocidade = (nivel_velocidade_jogador > 1)
    rotulos = {1: "1x Normal (5px)", 2: "2x Rápido (10px)", 3: "3x Ultra Flash (16px)"}
    registrar_acao_gm("Velocidade Jogador", rotulos[nivel_velocidade_jogador])

def alternar_hitbox_debug():
    global hitbox_debug
    hitbox_debug = not hitbox_debug
    registrar_acao_gm("Hitbox Debug", "Visível" if hitbox_debug else "Oculto")

def abrir_painel_admin_gm():
    from PyQt6.QtWidgets import QApplication
    from interface_usuarios_gm import JanelaPainelGM
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    u_gm = banco.obter_sessao_atual() or {"id": usuario_id, "username": nome_usuario, "is_gm": True}
    janela_gm = JanelaPainelGM(usuario_gm=u_gm)
    janela_gm.exec()
    pygame.event.clear()
    registrar_acao_gm("Painel Administrativo", "Painel aberto e fechado")

def formatar_tempo_ms(ms):
    if ms is None:
        return "--:--.---"
    total_seg = ms / 1000.0
    minutos = int(total_seg // 60)
    segundos = int(total_seg % 60)
    miliseg = int((ms % 1000))
    return f"{minutos:02d}:{segundos:02d}.{miliseg:03d}"

def reiniciar_jogo():
    global vel_x, vel_y, vel_recuo_x, no_chao, pulando, inimigos
    global tempo_inicio_ms, tempo_final_ms, corrida_finalizada, novo_recorde
    global inimigos_derrotados, usou_gm
    global jogo_pausado, momento_pausa_ms, tempo_pausado_acumulado_ms
    global fase_atual, mapa, total_inimigos_fase
    global multiplicador_jogo, nivel_velocidade_jogador, super_velocidade, pulo_infinito, god_mode

    fase_atual = "predio"
    mapa = Mapa()
    total_inimigos_fase = len(mapa.inimigos_iniciais)
    jogador_rect.size = (26, 56)
    jogador_rect.topleft = (mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1] - 26)
    saude.reiniciar()
    combate.parar_defesa()
    combate.bloqueios_chefe = 0
    combate.timer_escudo_quebrado = 0
    inimigos = criar_inimigos()
    vel_x = 0
    vel_y = 0
    vel_recuo_x = 0.0
    no_chao = False
    pulando = False

    multiplicador_jogo = 1
    nivel_velocidade_jogador = 1
    super_velocidade = False
    pulo_infinito = False
    god_mode = False

    tempo_inicio_ms = pygame.time.get_ticks()
    tempo_final_ms = None
    corrida_finalizada = False
    novo_recorde = False
    inimigos_derrotados = 0
    usou_gm = False
    jogo_pausado = False
    momento_pausa_ms = 0
    tempo_pausado_acumulado_ms = 0

# ------------------------------------------------------------------------
# 7. LOOP PRINCIPAL DE EVENTOS E ATUALIZAÇÃO
# ------------------------------------------------------------------------
executando = True

while executando:
    # 7.1 Processamento de Eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        # Cliques do mouse no Menu de Pausa
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if jogo_pausado:
                mx, my = pygame.mouse.get_pos()
                if eh_gm:
                    if btn_continuar_gm_rect.collidepoint((mx, my)):
                        jogo_pausado = False
                        tempo_pausado_acumulado_ms += (pygame.time.get_ticks() - momento_pausa_ms)
                        continue
                    elif btn_menu_gm_rect.collidepoint((mx, my)):
                        retornar_ao_menu()
                        continue
                    elif btn_gm_pause_god.collidepoint((mx, my)):
                        alternar_god_mode()
                        continue
                    elif btn_gm_pause_fase.collidepoint((mx, my)):
                        avancar_proxima_fase()
                        continue
                    elif btn_gm_pause_turbo.collidepoint((mx, my)):
                        alternar_velocidade_jogo()
                        continue
                    elif btn_gm_pause_pulo.collidepoint((mx, my)):
                        alternar_pulo_infinito()
                        continue
                    elif btn_gm_pause_kill.collidepoint((mx, my)):
                        executar_insta_kill()
                        continue
                    elif btn_gm_pause_cura.collidepoint((mx, my)):
                        executar_cura_total()
                        continue
                    elif btn_gm_pause_vel.collidepoint((mx, my)):
                        alternar_velocidade_jogador()
                        continue
                    elif btn_gm_pause_inicio.collidepoint((mx, my)):
                        executar_teleporte_inicio()
                        continue
                    elif btn_gm_pause_hitbox.collidepoint((mx, my)):
                        alternar_hitbox_debug()
                        continue
                    elif btn_gm_pause_admin.collidepoint((mx, my)):
                        abrir_painel_admin_gm()
                        continue
                    elif btn_gm_pause_saida.collidepoint((mx, my)):
                        alternar_fase()
                        continue
                    elif btn_gm_pause_menu_gm.collidepoint((mx, my)):
                        gm_menu_aberto = True
                        jogo_pausado = False
                        tempo_pausado_acumulado_ms += (pygame.time.get_ticks() - momento_pausa_ms)
                        continue
                else:
                    if btn_continuar_rect.collidepoint((mx, my)):
                        jogo_pausado = False
                        tempo_pausado_acumulado_ms += (pygame.time.get_ticks() - momento_pausa_ms)
                        continue
                    elif btn_menu_rect.collidepoint((mx, my)):
                        retornar_ao_menu()
                        continue

        if evento.type == pygame.KEYDOWN:
            # Alternar Pausa (Tecla P ou ESC)
            if evento.key in (pygame.K_p, pygame.K_ESCAPE) and not gm_menu_aberto and saude.esta_vivo() and not corrida_finalizada:
                jogo_pausado = not jogo_pausado
                if jogo_pausado:
                    momento_pausa_ms = pygame.time.get_ticks()
                else:
                    tempo_pausado_acumulado_ms += (pygame.time.get_ticks() - momento_pausa_ms)
                continue

            if jogo_pausado:
                # Comandos rápidos de GM dentro do Menu de Pausa
                if eh_gm:
                    if evento.key in (pygame.K_1, pygame.K_F2):
                        alternar_god_mode()
                        continue
                    elif evento.key in (pygame.K_2, pygame.K_F3):
                        executar_cura_total()
                        continue
                    elif evento.key in (pygame.K_3, pygame.K_F4):
                        executar_insta_kill()
                        continue
                    elif evento.key in (pygame.K_4, pygame.K_F5):
                        executar_teleporte_inicio()
                        continue
                    elif evento.key in (pygame.K_5, pygame.K_F6):
                        avancar_proxima_fase()
                        continue
                    elif evento.key in (pygame.K_6, pygame.K_F7):
                        alternar_pulo_infinito()
                        continue
                    elif evento.key in (pygame.K_7, pygame.K_F8):
                        alternar_velocidade_jogo()
                        continue
                    elif evento.key in (pygame.K_0, pygame.K_F9):
                        alternar_fase()
                        continue
                    elif evento.key in (pygame.K_8, pygame.K_F10):
                        alternar_velocidade_jogador()
                        continue
                    elif evento.key in (pygame.K_9, pygame.K_F11):
                        abrir_painel_admin_gm()
                        continue
                    elif evento.key == pygame.K_h:
                        alternar_hitbox_debug()
                        continue

                if evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_c):
                    jogo_pausado = False
                    tempo_pausado_acumulado_ms += (pygame.time.get_ticks() - momento_pausa_ms)
                elif evento.key in (pygame.K_m, pygame.K_q):
                    retornar_ao_menu()
                continue

            # Menu de Ajuda / Ranking
            if evento.key == pygame.K_TAB:
                exibir_ranking_tab = not exibir_ranking_tab

            # Alternar Menu GM exclusivamente com atalho CTRL+F12
            eh_ctrl = (evento.mod & pygame.KMOD_CTRL) != 0
            if evento.key == pygame.K_F12 and eh_ctrl:
                sessao_atual = banco.obter_sessao_atual()
                if sessao_atual and sessao_atual.get("is_gm"):
                    eh_gm = True
                    nome_usuario = sessao_atual.get("usuario")
                    usuario_id = sessao_atual.get("id")
                    papel_usuario = "gm"
                    gm_menu_aberto = not gm_menu_aberto
                    exibir_ranking_tab = False
                elif eh_gm:
                    gm_menu_aberto = not gm_menu_aberto
                    exibir_ranking_tab = False
                else:
                    # Não é GM: abre a tela de login
                    from PyQt6.QtWidgets import QApplication, QMessageBox
                    from interface_usuarios_gm import DialogLoginCadastro

                    app = QApplication.instance()
                    if not app:
                        app = QApplication(sys.argv)

                    dlg = DialogLoginCadastro()
                    dlg.exec()
                    pygame.event.clear()

                    sessao_atual = banco.obter_sessao_atual()
                    if sessao_atual and sessao_atual.get("is_gm"):
                        eh_gm = True
                        nome_usuario = sessao_atual.get("usuario")
                        usuario_id = sessao_atual.get("id")
                        papel_usuario = "gm"
                        gm_menu_aberto = True
                        exibir_ranking_tab = False
                    else:
                        msg = QMessageBox()
                        msg.setWindowTitle("Acesso Negado")
                        msg.setIcon(QMessageBox.Icon.Warning)
                        msg.setText("Você não tem acesso a essas funções!!\nCaba Safado!!!")
                        msg.setStyleSheet("""
                            QMessageBox {
                                background-color: #101c11;
                                color: #ff5555;
                            }
                            QLabel {
                                color: #ffcccc;
                                font-size: 13px;
                                font-weight: bold;
                            }
                            QPushButton {
                                background-color: #471515;
                                border: 1px solid #ff4444;
                                color: #ffffff;
                                padding: 6px 16px;
                                font-weight: bold;
                            }
                        """)
                        msg.exec()
                        pygame.event.clear()

            # Comandos em tempo real do Game Master (durante gameplay)
            if eh_gm and not gm_menu_aberto:
                if evento.key in (pygame.K_F2, pygame.K_1):
                    alternar_god_mode()
                elif evento.key in (pygame.K_F3, pygame.K_2):
                    executar_cura_total()
                elif evento.key in (pygame.K_F4, pygame.K_3):
                    executar_insta_kill()
                elif evento.key in (pygame.K_F5, pygame.K_4):
                    executar_teleporte_inicio()
                elif evento.key in (pygame.K_F6, pygame.K_5):
                    avancar_proxima_fase()
                elif evento.key in (pygame.K_F7, pygame.K_6):
                    alternar_pulo_infinito()
                elif evento.key in (pygame.K_F8, pygame.K_7):
                    alternar_velocidade_jogo()
                elif evento.key in (pygame.K_F9, pygame.K_0):
                    alternar_fase()
                elif evento.key in (pygame.K_F10, pygame.K_8):
                    alternar_velocidade_jogador()
                elif evento.key in (pygame.K_F11, pygame.K_9):
                    abrir_painel_admin_gm()
                elif evento.key == pygame.K_h:
                    alternar_hitbox_debug()

            # Comandos do Game Master no Menu Aberto (CTRL+F12)
            if gm_menu_aberto:
                if evento.key in (pygame.K_1, pygame.K_F2):
                    alternar_god_mode()
                elif evento.key in (pygame.K_2, pygame.K_F3):
                    executar_cura_total()
                elif evento.key in (pygame.K_3, pygame.K_F4):
                    executar_insta_kill()
                elif evento.key in (pygame.K_4, pygame.K_F5):
                    executar_teleporte_inicio()
                elif evento.key in (pygame.K_5, pygame.K_F6):
                    avancar_proxima_fase()
                elif evento.key in (pygame.K_6, pygame.K_F7):
                    alternar_pulo_infinito()
                elif evento.key in (pygame.K_7, pygame.K_F8):
                    alternar_velocidade_jogo()
                elif evento.key in (pygame.K_8, pygame.K_F10):
                    alternar_velocidade_jogador()
                elif evento.key in (pygame.K_0, pygame.K_F9):
                    alternar_fase()
                elif evento.key in (pygame.K_9, pygame.K_F11):
                    abrir_painel_admin_gm()
                elif evento.key == pygame.K_h:
                    alternar_hitbox_debug()
                elif evento.key == pygame.K_ESCAPE or (evento.key == pygame.K_F12 and eh_ctrl):
                    gm_menu_aberto = False

            # Reiniciar partida
            if evento.key == pygame.K_r and (not saude.esta_vivo() or corrida_finalizada):
                reiniciar_jogo()

            # Ações de Jogo normais
            if saude.esta_vivo() and not corrida_finalizada and not gm_menu_aberto:
                # Pulo
                if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    buffer_pulo_timer = BUFFER_MAX

                # Interação com Portas Blindadas (E)
                if evento.key == pygame.K_e:
                    mapa.interagir_portas(jogador_rect)

                # Ataque (J ou Z)
                if evento.key in (pygame.K_j, pygame.K_z):
                    combate.tentar_atacar()

                # Defesa / Escudo (K ou X)
                if evento.key in (pygame.K_k, pygame.K_x):
                    combate.iniciar_defesa()

        if evento.type == pygame.KEYUP:
            if saude.esta_vivo() and not corrida_finalizada and not jogo_pausado:
                # Cancelar altura de pulo ao soltar a tecla
                if evento.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and vel_y < -4:
                    vel_y = -4

                # Soltar defesa
                if evento.key in (pygame.K_k, pygame.K_x):
                    combate.parar_defesa()

        # Teleporte Livre com Clique Direito do GM
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3 and eh_gm:
            mx, my = pygame.mouse.get_pos()
            cam_x = jogador_rect.centerx - LARGURA_TELA // 2
            cam_y = jogador_rect.centery - ALTURA_TELA // 2
            jogador_rect.center = (mx + cam_x, my + cam_y)
            vel_x = vel_y = 0
            registrar_acao_gm("Teleporte Livre", f"Pos ({jogador_rect.x}, {jogador_rect.y})")

    # 7.2 Atualizações Físicas e de Entidades
    if saude.esta_vivo() and not corrida_finalizada and not jogo_pausado:
        # Modo Deus / Vida Infinita do GM
        if god_mode:
            saude.vida_atual = saude.vida_maxima
            saude.vida_visual = float(saude.vida_maxima)

        saude.atualizar()

        # Armadilhas de Teto Caindo
        blocos_colisao = mapa.obter_blocos_colisao()
        for pedaco in mapa.pedacos_teto:
            pedaco.atualizar(blocos_colisao, jogador_rect, saude, combate, god_mode)

        # Entrada e Movimento
        teclas = pygame.key.get_pressed()
        vel_x = 0

        vels_px = {1: 5, 2: 10, 3: 16}
        vel_base = vels_px.get(nivel_velocidade_jogador, 10 if super_velocidade else velocidade_movimento)
        vel_atual = vel_base * 0.4 if combate.defendendo else vel_base

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

        # Controle de Defesa Contínua
        if (teclas[pygame.K_k] or teclas[pygame.K_x]) and combate.pode_defender() and not combate.atacando:
            combate.defendendo = True
        elif not (teclas[pygame.K_k] or teclas[pygame.K_x]):
            combate.defendendo = False

        if getattr(combate, "acabou_de_recuperar", False):
            combate.acabou_de_recuperar = False
            notificar_gm("🛡️ Escudo Recuperado e Pronto!")

        # Mecânica de Escada Industrial
        na_escada = mapa.esta_na_escada(jogador_rect)
        if na_escada:
            if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                vel_y = -4.5
                pulando = False
            elif teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                vel_y = 4.5
                pulando = False
            else:
                vel_y = 0

            if teclas[pygame.K_SPACE]:
                vel_y = forca_pulo * 0.8
                pulando = True
        else:
            # Buffers de salto (com suporte a pulo infinito do GM)
            if no_chao:
                coyote_timer = COYOTE_MAX
            elif coyote_timer > 0:
                coyote_timer -= 1

            if buffer_pulo_timer > 0:
                buffer_pulo_timer -= 1

            if buffer_pulo_timer > 0 and (coyote_timer > 0 or pulo_infinito):
                vel_y = forca_pulo
                coyote_timer = 0
                buffer_pulo_timer = 0
                no_chao = False
                pulando = True
                coyote_timer = 0
                buffer_pulo_timer = 0
                no_chao = False
                pulando = True

            # Gravidade padrão
            vel_y += gravidade
            if vel_y > 15:
                vel_y = 15

        if abs(vel_recuo_x) > 0.1:
            vel_recuo_x *= 0.80
        else:
            vel_recuo_x = 0.0

        # Colisão Eixo X (Paredes sólidas + Portas fechadas)
        deslocamento_x = int(vel_x + vel_recuo_x)
        jogador_rect.x += deslocamento_x
        for bloco in mapa.colisoes_com_portas:
            if jogador_rect.colliderect(bloco):
                if deslocamento_x > 0:
                    jogador_rect.right = bloco.left
                    vel_recuo_x = 0.0
                elif deslocamento_x < 0:
                    jogador_rect.left = bloco.right
                    vel_recuo_x = 0.0

        # Colisão Eixo Y (Paredes sólidas + Portas fechadas)
        jogador_rect.y += int(vel_y)
        no_chao = False
        for bloco in mapa.colisoes_com_portas:
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

        # Combate e Escudo
        combate.atualizar(jogador_rect)

        # Atualização dos Inimigos
        inimigos_mortos_neste_frame = 0
        for inimigo in inimigos:
            inimigo.atualizar(mapa.colisoes_com_portas, jogador_rect, combate.hitbox_escudo)

            # Escudo empurra inimigo
            if combate.defendendo and combate.hitbox_escudo is not None:
                if combate.hitbox_escudo.colliderect(inimigo.rect):
                    if combate.direcao == 1:
                        inimigo.rect.left = combate.hitbox_escudo.right
                    else:
                        inimigo.rect.right = combate.hitbox_escudo.left
                    if inimigo.tempo_atordoado <= 0:
                        inimigo.aplicar_pulinho_recuo(combate.direcao, forca_x=6.5, forca_y=-6.0)
                        inimigo.tempo_atordoado = 25

            # Ataque do Jogador
            if combate.atacando and combate.hitbox_ataque is not None:
                if combate.hitbox_ataque.colliderect(inimigo.rect):
                    dano_desferido = 9999 if insta_kill else combate.dano_ataque
                    if inimigo.tomar_dano(dano_desferido, combate.direcao):
                        vel_recuo_x = -combate.direcao * combate.forca_recuo_x
                        vel_y = combate.forca_recuo_y
                        no_chao = False

            # Ataque do Inimigo no Jogador
            if not god_mode and inimigo.esta_vivo and inimigo.atacando and inimigo.hitbox_ataque is not None:
                colidiu_jogador = inimigo.hitbox_ataque.colliderect(jogador_rect)
                colidiu_escudo = (
                    combate.defendendo
                    and combate.hitbox_escudo is not None
                    and inimigo.hitbox_ataque.colliderect(combate.hitbox_escudo)
                )

                if colidiu_jogador or colidiu_escudo:
                    if not getattr(inimigo, "golpe_processado", False):
                        inimigo.golpe_processado = True

                        virado_para_inimigo = (
                            (combate.direcao == 1 and inimigo.rect.centerx >= jogador_rect.centerx)
                            or (combate.direcao == -1 and inimigo.rect.centerx <= jogador_rect.centerx)
                        )
                        tentando_bloquear = combate.defendendo and virado_para_inimigo and combate.pode_defender()

                        if isinstance(inimigo, ChefeSapo):
                            if tentando_bloquear:
                                bloqueou = combate.registrar_bloqueio_chefe()
                                if bloqueou:
                                    bloqueios = combate.bloqueios_chefe
                                    if bloqueios == 1:
                                        notificar_gm("🛡️ Golpe do Chefe Bloqueado! [1/2]")
                                    elif bloqueios == 2:
                                        notificar_gm("⚠️ Escudo Sobrecarga! [2/2] - O próximo golpe quebrará a guarda!")
                                    dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                                    vel_recuo_x = dir_imp * 5.0
                                else:
                                    # 3º Golpe consecutivo quebra a guarda! O jogador toma dano integral
                                    notificar_gm("💔 GUARDA QUEBRADA! Escudo desativado temporariamente!")
                                    dano_calc = inimigo.dano_ataque
                                    if saude.tomar_dano(dano_calc):
                                        vel_y = -9
                                        dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                                        vel_recuo_x = dir_imp * 8.5
                            else:
                                dano_calc = combate.calcular_dano_recebido(inimigo.dano_ataque)
                                if saude.tomar_dano(dano_calc):
                                    vel_y = -8
                                    dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                                    vel_recuo_x = dir_imp * 6.5
                        else:
                            # Inimigo comum
                            if tentando_bloquear:
                                inimigo.atacando = False
                                inimigo.hitbox_ataque = None
                                inimigo.cooldown_ataque = 45
                                inimigo.aplicar_pulinho_recuo(combate.direcao, forca_x=6.5, forca_y=-6.0)
                                inimigo.tempo_atordoado = 25
                            else:
                                dano_calc = combate.calcular_dano_recebido(inimigo.dano_ataque)
                                if saude.tomar_dano(dano_calc):
                                    vel_y = -8
                                    dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                                    vel_recuo_x = dir_imp * 6.5

            # Colisão por contato com Inimigo
            if not god_mode and inimigo.esta_vivo and jogador_rect.colliderect(inimigo.rect):
                bloqueado = combate.defendendo and combate.pode_defender() and (
                    (combate.direcao == 1 and inimigo.rect.centerx >= jogador_rect.centerx)
                    or (combate.direcao == -1 and inimigo.rect.centerx <= jogador_rect.centerx)
                )
                if not bloqueado:
                    dano_calc = combate.calcular_dano_recebido(15)
                    if saude.tomar_dano(dano_calc):
                        vel_y = -8
                        dir_imp = -1 if inimigo.rect.centerx > jogador_rect.centerx else 1
                        vel_recuo_x = dir_imp * 6.0

        # Limpar inimigos mortos e somar estatísticas
        qtd_antes = len(inimigos)
        inimigos = [inimigo for inimigo in inimigos if inimigo.esta_vivo]
        inimigos_derrotados += (qtd_antes - len(inimigos))

        # Espinhos
        if not god_mode:
            for espinho in mapa.espinhos:
                if jogador_rect.colliderect(espinho):
                    dano_calc = combate.calcular_dano_recebido(25)
                    if saude.tomar_dano(dano_calc):
                        vel_y = -7
                    break

        # Coleta de Kits Médicos
        for kit in mapa.kits_medicos[:]:
            if jogador_rect.colliderect(kit):
                if saude.curar(25):
                    mapa.kits_medicos.remove(kit)

        # Saída / Transição de Mapa ou Vitória Final
        if mapa.zona_saida and jogador_rect.colliderect(mapa.zona_saida) and not corrida_finalizada:
            if fase_atual == "predio":
                # Transição do Prédio para a Caverna do Chefe!
                fase_atual = "chefe"
                mapa = MapaChefe()
                jogador_rect.size = (26, 56)
                jogador_rect.topleft = (mapa.pos_inicial_jogador[0], mapa.pos_inicial_jogador[1] - 26)
                vel_x = 0
                vel_y = 0
                vel_recuo_x = 0.0
                combate.bloqueios_chefe = 0
                combate.timer_escudo_quebrado = 0
                inimigos = criar_inimigos_chefe()
                total_inimigos_fase += len(inimigos)
                notificar_gm("TRANSIÇÃO: Você adentrou a Caverna do Chefe!")
            else:
                corrida_finalizada = True
                tempo_final_ms = pygame.time.get_ticks() - tempo_inicio_ms - tempo_pausado_acumulado_ms

                # Gravar no SQLite
                if usuario_id is not None:
                    novo_recorde = banco.registrar_speedrun(
                        usuario_id=usuario_id,
                        tempo_ms=tempo_final_ms,
                        inimigos_derrotados=inimigos_derrotados,
                        total_inimigos=total_inimigos_fase,
                        usou_gm=usou_gm,
                    )
                    recorde_pessoal = banco.obter_recorde_pessoal(usuario_id)

                if not modo_speedrun:
                    dados_tela_final = {
                        "tempo_ms": tempo_final_ms,
                        "inimigos_derrotados": inimigos_derrotados,
                        "total_inimigos": total_inimigos_fase,
                        "novo_recorde": novo_recorde,
                        "usou_gm": usou_gm,
                    }
                    executando = False

    # Toast Timer
    if tempo_toast_gm > 0:
        tempo_toast_gm -= 1

    # --------------------------------------------------------------------
    # 8. RENDERIZAÇÃO GRÁFICA (CÂMERA, CENÁRIO E ENTIDADES)
    # --------------------------------------------------------------------
    # Câmera centralizada no jogador
    camera_x = jogador_rect.centerx - LARGURA_TELA // 2
    camera_y = jogador_rect.centery - ALTURA_TELA // 2
    limite_cam_x = max(0, mapa.largura - LARGURA_TELA)
    limite_cam_y = max(0, mapa.altura - ALTURA_TELA)
    camera_x = max(0, min(camera_x, limite_cam_x))
    camera_y = max(0, min(camera_y, limite_cam_y))

    # Fundo com paralaxe (Prédio ou Caverna)
    fundo_atual = imagem_fundo_caverna if (fase_atual == "chefe" and tem_imagem_fundo_caverna) else (imagem_fundo_predio if tem_imagem_fundo_predio else None)
    if fundo_atual:
        fx = int(-camera_x * 0.25) % LARGURA_TELA
        fy = int(-camera_y * 0.25) % ALTURA_TELA
        tela.blit(fundo_atual, (fx - LARGURA_TELA, fy - ALTURA_TELA))
        tela.blit(fundo_atual, (fx, fy - ALTURA_TELA))
        tela.blit(fundo_atual, (fx - LARGURA_TELA, fy))
        tela.blit(fundo_atual, (fx, fy))
    else:
        cor_fundo = (12, 10, 16) if fase_atual == "chefe" else (16, 22, 18)
        tela.fill(cor_fundo)

    # Desenho do Mapa (blocos, escadas, portas, armadilhas, saída)
    mapa.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA, jogador_rect)

    # Desenho dos Inimigos
    for inimigo in inimigos:
        inimigo.desenhar(tela, camera_x, camera_y, LARGURA_TELA, ALTURA_TELA)

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
                progresso_ataque * len(quadros_ataque) // combate.duracao_ataque,
                len(quadros_ataque) - 1,
            )
            sprite_atual = quadros_ataque[indice_quadro] if direcao_jogador > 0 else quadros_ataque_esq[indice_quadro]
        elif combate.defendendo:
            indice_quadro = (pygame.time.get_ticks() // 220) % len(quadros_defesa)
            sprite_atual = quadros_defesa[indice_quadro] if direcao_jogador > 0 else quadros_defesa_esq[indice_quadro]
        elif pulando:
            indice_quadro = (pygame.time.get_ticks() // 180) % len(quadros_pulo)
            sprite_atual = quadros_pulo[indice_quadro] if direcao_jogador > 0 else quadros_pulo_esq[indice_quadro]
        elif vel_x != 0:
            indice_quadro = (pygame.time.get_ticks() // 120) % len(quadros_andando)
            sprite_atual = quadros_andando[indice_quadro] if direcao_jogador > 0 else quadros_andando_esq[indice_quadro]
        else:
            sprite_atual = sprite_parado if direcao_jogador > 0 else sprite_parado_esq

        sprite_rect = sprite_atual.get_rect(midbottom=(jt.centerx, jt.bottom))

        # Aura Dourada Divina de God Mode do GM
        if god_mode:
            pulso = int(4 * abs(math.sin(pygame.time.get_ticks() * 0.006)))
            raio_aura = 26 + pulso
            surf_aura = pygame.Surface((raio_aura * 2, raio_aura * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_aura, (255, 215, 0, 85), (raio_aura, raio_aura), raio_aura, 2)
            pygame.draw.circle(surf_aura, (255, 240, 130, 40), (raio_aura, raio_aura), raio_aura - 3)
            tela.blit(surf_aura, surf_aura.get_rect(center=jt.center))

        tela.blit(sprite_atual, sprite_rect)

        # Desenhar efeitos visuais do combate (hitbox de ataque e escudo)
        combate.desenhar(tela, camera_x, camera_y, jogador_rect)

    # Depurador Completo de Hitboxes do GM
    if hitbox_debug:
        # Jogador (Verde Neon)
        pygame.draw.rect(tela, (57, 255, 20), jogador_rect.move(-camera_x, -camera_y), 2)

        # Inimigos e Ataques (Vermelho para corpo, Magenta para língua, Amarelo para chifres/mordida)
        for ini in inimigos:
            pygame.draw.rect(tela, (255, 40, 40), ini.rect.move(-camera_x, -camera_y), 2)
            if ini.hitbox_ataque:
                cor_golpe = (255, 60, 255) if getattr(ini, "tipo_ataque_atual", "") == "lingua" else (255, 215, 0)
                pygame.draw.rect(tela, cor_golpe, ini.hitbox_ataque.move(-camera_x, -camera_y), 2)

        # Portas (Ciano quando aberta, Laranja quando fechada)
        for porta in mapa.portas:
            cor_p = (0, 255, 255) if porta.aberta else (255, 120, 0)
            pygame.draw.rect(tela, cor_p, porta.rect.move(-camera_x, -camera_y), 1)

        # Ácido e Espinhos (Laranja Avermelhado)
        for esp in mapa.espinhos:
            pygame.draw.rect(tela, (255, 140, 0), esp.move(-camera_x, -camera_y), 1)

        # Armadilhas de Teto (Vermelho vivo)
        for pedaco in mapa.pedacos_teto:
            pygame.draw.rect(tela, (255, 60, 60), pedaco.rect.move(-camera_x, -camera_y), 1)

        # Zona de Saída / Fuga (Dourado)
        if mapa.zona_saida:
            pygame.draw.rect(tela, (255, 215, 0), mapa.zona_saida.move(-camera_x, -camera_y), 2)

    # --------------------------------------------------------------------
    # 9. HUD SUPERIOR, ESTATÍSTICAS E PAINÉIS OVERLAY
    # --------------------------------------------------------------------
    # Barra de Saúde/Sede
    

    saude.desenhar_hud(tela)

    # Rótulo de Usuário Conectado
    badge_u = f"SOBREVIVENTE: {nome_usuario}"
    if eh_gm:
        badge_u += " [GAME MASTER]"
    txt_u = fonte_normal.render(badge_u, True, (210, 255, 210))
    tela.blit(txt_u, (40, 78))

    # Indicador de Fase / Local
    badge_fase = "LOCAL: ARENA DA CAVERNA (CHEFE)" if fase_atual == "chefe" else "LOCAL: PRÉDIO"
    cor_fase = (255, 215, 0) if fase_atual == "chefe" else (160, 230, 180)
    txt_f = fonte_gm_dica.render(badge_fase, True, cor_fase)
    tela.blit(txt_f, (40, 102))

    # Barra de Vida do Chefe
    if fase_atual == "chefe" and inimigos:
        boss = inimigos[0]
        largura_barra_boss = 520
        altura_barra_boss = 28
        bx = (LARGURA_TELA - largura_barra_boss) // 2
        by = 28

        pygame.draw.rect(tela, (18, 12, 18), (bx - 2, by - 2, largura_barra_boss + 4, altura_barra_boss + 4), border_radius=4)
        pygame.draw.rect(tela, (255, 50, 50), (bx - 2, by - 2, largura_barra_boss + 4, altura_barra_boss + 4), 2, border_radius=4)

        pct_boss = max(0.0, min(1.0, boss.vida / 250.0))
        largura_vida_boss = int(largura_barra_boss * pct_boss)
        if largura_vida_boss > 0:
            pygame.draw.rect(tela, (230, 30, 45), (bx, by, largura_vida_boss, altura_barra_boss), border_radius=3)

        txt_boss = fonte_gm_dica.render(f"SAPO MUTANTE ({max(0, boss.vida)}/250 HP)", True, (255, 240, 240))
        tela.blit(txt_boss, txt_boss.get_rect(center=(LARGURA_TELA // 2, by + altura_barra_boss // 2)))



    # Notificação Toast de Ação de GM (Ampla e bem legível)
    if tempo_toast_gm > 0 and mensagem_gm_toast:
        largura_toast = 820
        altura_toast = 46
        tx = (LARGURA_TELA - largura_toast) // 2
        ty = 120
        surf_toast = pygame.Surface((largura_toast, altura_toast), pygame.SRCALPHA)
        surf_toast.fill((10, 18, 12, 240))
        tela.blit(surf_toast, (tx, ty))
        pygame.draw.rect(tela, (255, 215, 0), (tx, ty, largura_toast, altura_toast), 2, border_radius=5)
        lbl_toast = fonte_toast.render(mensagem_gm_toast, True, (255, 235, 120))
        tela.blit(lbl_toast, lbl_toast.get_rect(center=(LARGURA_TELA // 2, ty + altura_toast // 2)))

    # Faixa Informativa de Atalhos de GM no Rodapé da Tela (Ampla e de Alta Visibilidade)

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------
    # 11. MENU OVERLAY DE GAME MASTER (CTRL+F12)
    # --------------------------------------------------------------------
    if gm_menu_aberto:
        largura_gm = 960
        altura_gm = 640
        gm_x = (LARGURA_TELA - largura_gm) // 2
        gm_y = (ALTURA_TELA - altura_gm) // 2

        surf_gm = pygame.Surface((largura_gm, altura_gm), pygame.SRCALPHA)
        surf_gm.fill((10, 20, 14, 245))
        tela.blit(surf_gm, (gm_x, gm_y))
        pygame.draw.rect(tela, (255, 215, 0), (gm_x, gm_y, largura_gm, altura_gm), 3, border_radius=8)

        txt_gm_header = fonte_gm_titulo.render("👑 FERRAMENTAS DO GAME MASTER (GM / ADMIN)", True, (255, 215, 0))
        tela.blit(txt_gm_header, (gm_x + 35, gm_y + 20))

        linhas_comandos_gm = [
            ("[1 ou F2] Modo Deus (God Mode)", f"Status: {'ATIVO (Vida Infinita)' if god_mode else 'DESATIVADO'}"),
            ("[2 ou F3] Restaurar Saúde Completa", "Cura 100% da vida e sede"),
            ("[3 ou F4] Insta-Kill Monstros", f"Elimina {len(inimigos)} monstros instantaneamente"),
            ("[4 ou F5] Teleporte para o Início", "Retornar ao início da fase"),
            ("[5 ou F6] Avançar para Próxima Fase", f"Prédio -> Chefe -> Fim (Atual: {fase_atual.upper()})"),
            ("[6 ou F7] Pulo Infinito (Voar)", f"Status: {'ATIVO (Pular no ar)' if pulo_infinito else 'DESATIVADO'}"),
            ("[7 ou F8] Acelerar Jogo (Turbo)", f"Status: {multiplicador_jogo}x ({60 * multiplicador_jogo} FPS)"),
            ("[8 ou F10] Super Velocidade Jogador", f"Status: {nivel_velocidade_jogador}x ({'16px' if nivel_velocidade_jogador==3 else '10px' if nivel_velocidade_jogador==2 else '5px'})"),
            ("[0 ou F9] Alternar Prédio / Caverna", f"Alternar fase atual ({fase_atual.upper()})"),
            ("[H] Depurador de Hitbox", f"Status: {'VISIVEL' if hitbox_debug else 'OCULTO'}"),
            ("[9 ou F11] Painel Administrativo GM", "Abre painel completo (Usuários, Relatórios e Dados)"),
            ("[Clique Direito]", "Teleporte livre para o cursor do mouse"),
            ("[CTRL+F12 / ESC]", "Fechar este painel de Game Master"),
        ]

        for i, (tecla, desc) in enumerate(linhas_comandos_gm):
            y_item = gm_y + 65 + (i * 42)
            t_tecla = fonte_gm_botao.render(tecla, True, (57, 255, 20))
            t_desc = fonte_gm_botao.render(desc, True, (230, 245, 230))
            tela.blit(t_tecla, (gm_x + 35, y_item))
            tela.blit(t_desc, (gm_x + 390, y_item))

    # --------------------------------------------------------------------
    # 12. OVERLAY DO LEADERBOARD COMPLETO (TAB)
    # --------------------------------------------------------------------
    if exibir_ranking_tab and not gm_menu_aberto:
        largura_rk = 820
        altura_rk = 560
        rk_x = (LARGURA_TELA - largura_rk) // 2
        rk_y = (ALTURA_TELA - altura_rk) // 2

        surf_rk = pygame.Surface((largura_rk, altura_rk), pygame.SRCALPHA)
        surf_rk.fill((8, 18, 12, 245))
        tela.blit(surf_rk, (rk_x, rk_y))
        pygame.draw.rect(tela, (57, 255, 20), (rk_x, rk_y, largura_rk, altura_rk), 3, border_radius=6)

        txt_rk_t = fonte_gm_titulo.render("🏆 RANKING OFICIAL DE SPEEDRUN (SQLITE)", True, (57, 255, 20))
        tela.blit(txt_rk_t, (rk_x + 35, rk_y + 25))

        linhas_lead = banco.obter_ranking(limite=10, apenas_legitimos=True)
        cabecalho_col = f"{'POS':<6} {'SOBREVIVENTE':<24} {'TEMPO':<16} {'ABATES':<8}"
        tela.blit(fonte_normal.render(cabecalho_col, True, (255, 215, 0)), (rk_x + 35, rk_y + 65))
        pygame.draw.line(tela, (40, 80, 45), (rk_x + 35, rk_y + 88), (rk_x + largura_rk - 35, rk_y + 88), 2)

        if not linhas_lead:
            txt_vazio = fonte_normal.render("Nenhum tempo oficial registrado ainda.", True, (180, 180, 180))
            tela.blit(txt_vazio, (rk_x + 35, rk_y + 115))
        else:
            for idx, rk in enumerate(linhas_lead):
                y_pos = rk_y + 105 + (idx * 34)
                linha_t = f"#{rk['posicao']:<5} {rk['username']:<24} {rk['tempo_formatado']:<16} {rk.get('inimigos_derrotados', 0):<8}"
                cor_item = (57, 255, 20) if rk["posicao"] == 1 else (240, 240, 240)
                tela.blit(fonte_normal.render(linha_t, True, cor_item), (rk_x + 35, y_pos))

        txt_fechar_rk = fonte_gm_dica.render("Pressione [TAB] para fechar o Ranking", True, (160, 210, 160))
        tela.blit(txt_fechar_rk, (rk_x + 35, rk_y + altura_rk - 38))

    # --------------------------------------------------------------------
    # 13. MENU DE PAUSA (TECLA P)
    # --------------------------------------------------------------------
    if jogo_pausado:
        # Fundo escurecido semi-transparente cobrindo a tela inteira
        surf_overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        surf_overlay.fill((4, 10, 8, 225))
        tela.blit(surf_overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()

        if eh_gm:
            # Menu de Pausa Expandido para Game Master (Dashboard Dual com Alta Legibilidade)
            surf_box = pygame.Surface((LARGURA_BOX_PAUSE_GM, ALTURA_BOX_PAUSE_GM), pygame.SRCALPHA)
            surf_box.fill((10, 20, 14, 252))
            tela.blit(surf_box, (PAUSE_GM_X, PAUSE_GM_Y))
            pygame.draw.rect(tela, (255, 215, 0), (PAUSE_GM_X, PAUSE_GM_Y, LARGURA_BOX_PAUSE_GM, ALTURA_BOX_PAUSE_GM), 3, border_radius=10)

            # Painel Esquerdo: Menu Tradicional
            txt_pausa = fonte_titulo.render("JOGO PAUSADO", True, (57, 255, 20))
            tela.blit(txt_pausa, (PAUSE_GM_X + 35, PAUSE_GM_Y + 28))

            txt_u_pause = fonte_normal.render(f"👑 CONTA GAME MASTER: {nome_usuario}", True, (255, 215, 0))
            tela.blit(txt_u_pause, (PAUSE_GM_X + 35, PAUSE_GM_Y + 74))

            # Botão Continuar
            hover_cont = btn_continuar_gm_rect.collidepoint((mx, my))
            c_bg_cont = (30, 80, 45) if hover_cont else (18, 48, 26)
            c_bd_cont = (80, 255, 60) if hover_cont else (57, 255, 20)
            pygame.draw.rect(tela, c_bg_cont, btn_continuar_gm_rect, border_radius=6)
            pygame.draw.rect(tela, c_bd_cont, btn_continuar_gm_rect, 2, border_radius=6)
            lbl_cont = fonte_media.render("▶ CONTINUAR [P]", True, (255, 255, 255) if hover_cont else (200, 255, 200))
            tela.blit(lbl_cont, lbl_cont.get_rect(center=btn_continuar_gm_rect.center))

            # Botão Menu Principal
            hover_menu = btn_menu_gm_rect.collidepoint((mx, my))
            c_bg_menu = (80, 25, 25) if hover_menu else (46, 18, 18)
            c_bd_menu = (255, 70, 70) if hover_menu else (200, 50, 50)
            pygame.draw.rect(tela, c_bg_menu, btn_menu_gm_rect, border_radius=6)
            pygame.draw.rect(tela, c_bd_menu, btn_menu_gm_rect, 2, border_radius=6)
            lbl_m = fonte_media.render("⮌ MENU PRINCIPAL [M]", True, (255, 255, 255) if hover_menu else (255, 200, 200))
            tela.blit(lbl_m, lbl_m.get_rect(center=btn_menu_gm_rect.center))

            # Instruções e atalhos rápidos à esquerda
            linhas_dicas = [
                "• [P] ou [ESPAÇO]: Continuar a partida",
                "• [M]: Retornar ao Menu Principal",
                "• [Botão Direito]: Teleporte Livre",
                "• [CTRL+F12]: Painel Geral de GM",
                "",
                "★ Todos os cheats podem ser usados",
                "também durante a partida direta!",
            ]
            for idx_d, d in enumerate(linhas_dicas):
                lbl_d = fonte_gm_dica.render(d, True, (180, 220, 180) if not d.startswith("★") else (255, 220, 120))
                tela.blit(lbl_d, (PAUSE_GM_X + 35, PAUSE_GM_Y + 275 + (idx_d * 26)))

            # Linha Divisória Vertical
            pygame.draw.line(tela, (45, 90, 55), (PAUSE_GM_X + 395, PAUSE_GM_Y + 25), (PAUSE_GM_X + 395, PAUSE_GM_Y + ALTURA_BOX_PAUSE_GM - 25), 2)

            # Painel Direito: Cheats Interativos de Game Master
            txt_cheats_t = fonte_gm_titulo.render("👑 FERRAMENTAS & CHEATS DO GM", True, (255, 215, 0))
            tela.blit(txt_cheats_t, (PAUSE_GM_X + 425, PAUSE_GM_Y + 30))

            # Definição dos Botões Interativos
            botoes_cheats = [
                (btn_gm_pause_god, f"[F2] Modo Deus: {'ATIVO' if god_mode else 'OFF'}", god_mode, (255, 215, 0) if god_mode else None),
                (btn_gm_pause_fase, "[F6] Avançar Fase ➔", False, (100, 220, 255)),
                (btn_gm_pause_turbo, f"[F8] Turbo Jogo: {multiplicador_jogo}x", multiplicador_jogo > 1, (255, 180, 50) if multiplicador_jogo > 1 else None),
                (btn_gm_pause_pulo, f"[F7] Pulo Infinito: {'ON' if pulo_infinito else 'OFF'}", pulo_infinito, (80, 255, 120) if pulo_infinito else None),
                (btn_gm_pause_kill, "[F4] Insta-Kill Monstros", False, (255, 90, 90)),
                (btn_gm_pause_cura, "[F3] Curar 100% Vida", False, (120, 255, 120)),
                (btn_gm_pause_vel, f"[F10] Vel. Jogador: {nivel_velocidade_jogador}x", nivel_velocidade_jogador > 1, (255, 220, 80) if nivel_velocidade_jogador > 1 else None),
                (btn_gm_pause_inicio, "[F5] Teleporte Início", False, (200, 200, 255)),
                (btn_gm_pause_hitbox, f"[H] Hitboxes: {'VISÍVEL' if hitbox_debug else 'OFF'}", hitbox_debug, (57, 255, 20) if hitbox_debug else None),
                (btn_gm_pause_admin, "[F11] Painel Admin (PyQt6)", False, (255, 215, 0)),
                (btn_gm_pause_saida, f"[F9] Alternar: {fase_atual.upper()}", False, (220, 180, 255)),
                (btn_gm_pause_menu_gm, "[CTRL+F12] Menu GM", False, (180, 240, 200)),
            ]

            for r_btn, texto_btn, esta_ativo, cor_destaque in botoes_cheats:
                hover = r_btn.collidepoint((mx, my))
                if esta_ativo:
                    c_bg = (35, 75, 45) if hover else (22, 54, 30)
                    c_bd = (255, 215, 0) if cor_destaque == (255, 215, 0) else (57, 255, 20)
                    c_tx = (255, 255, 255)
                else:
                    c_bg = (26, 44, 32) if hover else (14, 28, 20)
                    c_bd = cor_destaque or ((57, 255, 20) if hover else (45, 90, 55))
                    c_tx = (255, 255, 255) if hover else (210, 230, 215)

                pygame.draw.rect(tela, c_bg, r_btn, border_radius=6)
                pygame.draw.rect(tela, c_bd, r_btn, 2 if (hover or esta_ativo) else 1, border_radius=6)
                lbl_b = fonte_gm_botao.render(texto_btn, True, c_tx)
                tela.blit(lbl_b, lbl_b.get_rect(center=r_btn.center))

            txt_dica_gm = fonte_gm_dica.render("★ Clique nos botões acima ou aperte F2..F11 / H a qualquer momento na partida!", True, (255, 220, 120))
            tela.blit(txt_dica_gm, (PAUSE_GM_X + 425, PAUSE_GM_Y + ALTURA_BOX_PAUSE_GM - 35))

        else:
            # Menu de Pausa Normal (Jogadores Comuns)
            surf_box = pygame.Surface((LARGURA_BOX_PAUSE, ALTURA_BOX_PAUSE), pygame.SRCALPHA)
            surf_box.fill((10, 20, 14, 250))
            tela.blit(surf_box, (PAUSE_X, PAUSE_Y))
            pygame.draw.rect(tela, (57, 255, 20), (PAUSE_X, PAUSE_Y, LARGURA_BOX_PAUSE, ALTURA_BOX_PAUSE), 3, border_radius=8)

            txt_pausa = fonte_titulo.render("JOGO PAUSADO", True, (57, 255, 20))
            tela.blit(txt_pausa, txt_pausa.get_rect(center=(LARGURA_TELA // 2, PAUSE_Y + 50)))

            hover_continuar = btn_continuar_rect.collidepoint((mx, my))
            cor_bg_continuar = (30, 75, 40) if hover_continuar else (18, 42, 24)
            cor_borda_continuar = (80, 255, 60) if hover_continuar else (57, 255, 20)
            cor_txt_continuar = (255, 255, 255) if hover_continuar else (200, 255, 200)

            pygame.draw.rect(tela, cor_bg_continuar, btn_continuar_rect, border_radius=6)
            pygame.draw.rect(tela, cor_borda_continuar, btn_continuar_rect, 2, border_radius=6)
            lbl_continuar = fonte_media.render("▶  CONTINUAR  [P]", True, cor_txt_continuar)
            tela.blit(lbl_continuar, lbl_continuar.get_rect(center=btn_continuar_rect.center))

            hover_menu = btn_menu_rect.collidepoint((mx, my))
            cor_bg_menu = (75, 25, 25) if hover_menu else (42, 18, 18)
            cor_borda_menu = (255, 70, 70) if hover_menu else (200, 50, 50)
            cor_txt_menu = (255, 255, 255) if hover_menu else (255, 200, 200)

            pygame.draw.rect(tela, cor_bg_menu, btn_menu_rect, border_radius=6)
            pygame.draw.rect(tela, cor_borda_menu, btn_menu_rect, 2, border_radius=6)
            lbl_menu = fonte_media.render("⮌  RETORNAR AO MENU  [M]", True, cor_txt_menu)
            tela.blit(lbl_menu, lbl_menu.get_rect(center=btn_menu_rect.center))

    
    
    # Painel de Speedrun no Canto Superior Direito
    if modo_speedrun:
        if corrida_finalizada:
            tempo_atual_ms = tempo_final_ms
        elif jogo_pausado:
            tempo_atual_ms = max(
                0,
                momento_pausa_ms
                - tempo_inicio_ms
                - tempo_pausado_acumulado_ms,
            )
        else:
            tempo_atual_ms = max(
                0,
                pygame.time.get_ticks()
                - tempo_inicio_ms
                - tempo_pausado_acumulado_ms,
            )

        largura_hud_timer = 380
        altura_hud_timer = 104
        timer_x = LARGURA_TELA - largura_hud_timer - 30
        timer_y = 25

        surf_timer = pygame.Surface(
            (largura_hud_timer, altura_hud_timer), pygame.SRCALPHA
        )
        surf_timer.fill((8, 22, 12, 220))
        tela.blit(surf_timer, (timer_x, timer_y))
        cor_borda_timer = (255, 80, 80) if usou_gm else (57, 255, 20)
        pygame.draw.rect(
            tela,
            cor_borda_timer,
            (timer_x, timer_y, largura_hud_timer, altura_hud_timer),
            2,
            border_radius=4,
        )

        tempo_str = formatar_tempo_ms(tempo_atual_ms)
        cor_tempo = (255, 220, 100) if corrida_finalizada else (57, 255, 20)
        txt_cronometro = fonte_timer.render(tempo_str, True, cor_tempo)
        tela.blit(txt_cronometro, (timer_x + 16, timer_y + 10))

        info_stats = (
            f"Inimigos Eliminados: {inimigos_derrotados}/{total_inimigos_fase}"
        )
        txt_stats = fonte_normal.render(info_stats, True, (200, 240, 200))
        tela.blit(txt_stats, (timer_x + 16, timer_y + 44))

        if usou_gm:
            txt_status_sr = fonte_gm_dica.render(
                "⚠️ GM ATIVO: PARTIDA DESCLASSIFICADA", True, (255, 100, 100)
            )
        else:
            rec_txt = (
                recorde_pessoal["tempo_formatado"]
                if recorde_pessoal
                else "--:--.---"
            )
            txt_status_sr = fonte_gm_dica.render(
                f"OFICIAL | Seu Recorde: {rec_txt}", True, (255, 215, 0)
            )
        tela.blit(txt_status_sr, (timer_x + 16, timer_y + 72))

    if not saude.esta_vivo():
        saude.desenhar_game_over(tela, LARGURA_TELA, ALTURA_TELA)

    pygame.display.flip()
    relogio.tick(int(60 * multiplicador_jogo))

pygame.quit()

if dados_tela_final is not None:
    from PyQt6.QtWidgets import QApplication
    from historia.final import CenaHistoria
    from historia.navegacao import mostrar_janela

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    janela = mostrar_janela(CenaHistoria(**dados_tela_final))
    sys.exit(app.exec())

sys.exit()
