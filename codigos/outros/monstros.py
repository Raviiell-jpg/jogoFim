from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pygame


PASTA_IMAGENS_MONSTROS = (
    Path(__file__).resolve().parents[2] / "prites" / "mosntros"
)
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp"}
GRADE_MONSTROS = {"tatu": (2, 2), "rato": (2, 2), "lagartixa": (1, 4)}
GRADE_ATAQUE_MONSTROS = {
    "tatu": (1, 3),
    "rato": (1, 3),
    "lagartixa": (1, 3),
}


def carregar_imagens_monstros(
    pasta: Optional[Union[str, Path]] = None,
) -> Dict[str, pygame.Surface]:
    """Carrega as imagens de monstros e retorna um dicionário pelo nome do arquivo."""
    pasta_imagens = Path(pasta) if pasta is not None else PASTA_IMAGENS_MONSTROS
    if not pasta_imagens.is_dir():
        raise FileNotFoundError(f"Pasta de imagens dos monstros não encontrada: {pasta_imagens}")

    arquivos = sorted(
        arquivo
        for arquivo in pasta_imagens.iterdir()
        if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_IMAGEM
    )
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhuma imagem de monstro encontrada em: {pasta_imagens}"
        )

    imagens = {}
    for arquivo in arquivos:
        if arquivo.stem in imagens:
            raise ValueError(f"Mais de uma imagem encontrada para o monstro: {arquivo.stem}")
        imagens[arquivo.stem] = pygame.image.load(str(arquivo))

    return imagens


def separar_spritesheet(
    imagem: pygame.Surface,
    linhas: int = 2,
    colunas: int = 2,
    min_alpha: int = 1,
) -> List[pygame.Surface]:
    if linhas <= 0 or colunas <= 0:
        raise ValueError("A quantidade de linhas e colunas deve ser positiva.")

    largura, altura = imagem.get_size()
    if largura < colunas or altura < linhas:
        raise ValueError("A imagem é pequena demais para a divisão solicitada.")

    quadros = []
    for linha in range(linhas):
        topo = linha * altura // linhas
        base = (linha + 1) * altura // linhas
        for coluna in range(colunas):
            esquerda = coluna * largura // colunas
            direita = (coluna + 1) * largura // colunas
            quadro = imagem.subsurface(
                (esquerda, topo, direita - esquerda, base - topo)
            ).copy()
            quadros.append(_cortar_quadro(quadro, min_alpha))

    return quadros


def _cortar_quadro(
    imagem: pygame.Surface, min_alpha: int = 1
) -> pygame.Surface:
    limites = imagem.get_bounding_rect(min_alpha=min_alpha)
    if limites.width == 0 or limites.height == 0:
        raise ValueError("A imagem contém um quadro vazio.")
    return imagem.subsurface(limites).copy()


def carregar_quadros_sapo(
    imagens: Dict[str, pygame.Surface],
) -> Tuple[List[pygame.Surface], List[List[pygame.Surface]]]:
    quadros_normais = separar_spritesheet(
        imagens["sapoAndando"], linhas=1, colunas=4, min_alpha=16
    )
    pasta_ataques = PASTA_IMAGENS_MONSTROS / "sapoAtaque"
    animacoes_ataque = []
    for nome_arquivo in ("spAtaque.png", "spAtaque2.png"):
        caminho = pasta_ataques / nome_arquivo
        if not caminho.is_file():
            raise FileNotFoundError(f"Spritesheet de ataque do sapo não encontrada: {caminho}")
        imagem = pygame.image.load(str(caminho))
        animacoes_ataque.append(
            separar_spritesheet(imagem, linhas=1, colunas=4, min_alpha=16)
        )
    return quadros_normais, animacoes_ataque