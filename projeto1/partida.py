import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

st.title("Previsão de Jogos da Copa")

selecoes = pd.read_excel(
    "DadosCopaDoMundoQatar2022.xlsx", sheet_name="selecoes", index_col=0
)

# ----------------------------
# carreganndo os dados de pontuação da FIFA
fifa = selecoes["PontosRankingFIFA"]

# criando uma transformação lienar para os valores de escala numérica

a, b = min(fifa), max(fifa)
fa, fb = 0.15, 1
# fazendo uma transformação linear, com 0.15 o menor valor e 1 o maior
# calcula o coef. de inclinação da reta e b0
b1 = (fb - fa) / (b - a)
b0 = fb - b*b1

forca = b1 * fifa + b0

# --------------------------------
def MediaPoisson(selecao1, selecao2) -> list[int, int]:
    forca1 = forca[selecao1]
    forca2 = forca[selecao2]

    # media de gols estimada para toda a Copa baseada nas últimas médias em copas anteriores
    mediaGolsEstimada = 2.75
    lambda1 = mediaGolsEstimada * forca1 / (forca1 + forca2)
    lambda2 = mediaGolsEstimada - lambda1
    
    return [lambda1, lambda2]

def Resultado(gols1, gols2):
    if gols1 > gols2:
        return "V"
    elif gols2 > gols1:
        return "D"
    return "E"


def Pontos(gols1: int, gols2: int) -> list:
    resultado = Resultado(gols1, gols2)
    
    if resultado == "V":
        pontos1, pontos2 = 3, 0
    elif resultado == "D":
        pontos1, pontos2 = 0, 3
    else:
        pontos1, pontos2 = 1, 1
        
    return [pontos1, pontos2, resultado]

def Jogo(selecao1: str, selecao2: str) -> list:
    # usando os dados do ranking FIFA

    # lambda = média
    lambda1, lambda2 = MediaPoisson(selecao1, selecao2)
    # simulando um jogo
    gols1 = int(np.random.poisson(lam=lambda1, size=1))
    gols2 = int(np.random.poisson(lam=lambda2, size=1))

    saldo1 = gols1 - gols2
    saldo2 = -saldo1

    pontos1, pontos2, resultado = Pontos(gols1, gols2)

    placar = f"{gols1}x{gols2}"

    return [gols1, gols2, saldo1, saldo2, pontos1, pontos2, resultado, placar]


# calcula probabilidade de 0-6 gols e 7+
# dá a média de gols e calcula a prbabilidade de cada resultado
def Distribuicao(media: int):
    probs = []
    # placar até 7 gols no máximo
    for i in range(7):
        probs.append(poisson.pmf(i, media))
    # probabilidade para 7 ou mais
    probs.append(1 - sum(probs))

    return pd.Series(probs, index=["0", "1", "2", "3", "4", "5", "6", "7+"])



def ProbabilidadesPartida(selecao1, selecao2) -> list:
    media1, media2 = MediaPoisson(selecao1, selecao2)
    dist1, dist2 = Distribuicao(media1), Distribuicao(media2)
    matriz = np.outer(dist1, dist2)

    # probabilidades
    vitoria = np.tril(matriz).sum() - np.trace(matriz)  # triangular superior - traço
    derrota = np.triu(matriz).sum() - np.trace(matriz)  #  tringular inferior - traço
    empate = 1 - (vitoria + derrota)

    probs = np.around([vitoria, empate, derrota], 3)
    probsp = [f"{100*i:.1f}%" for i in probs]  # %

    nomes = ["0", "1", "2", "3", "4", "5", "6", "7+"]
    matriz = pd.DataFrame(matriz, columns=nomes, index=nomes)
    matriz.index = pd.MultiIndex.from_product([[selecao1], matriz.index])
    matriz.columns = pd.MultiIndex.from_product([[selecao2], matriz.columns])

    output = {
        "selecao1": selecao1,
        "selecao2": selecao2,
        "força1": forca[selecao1],
        "força2": forca[selecao2],
        "media1": media1,
        "media2": media2,
        "probabilidades": probsp,
        "matriz": matriz,
    }

    return output

# -------------------------------
#! APLICATIVO COMEÇA AQUI

listaSelecoes1 = selecoes.index.tolist()
listaSelecoes1.sort()
listaSelecoes2 = listaSelecoes1.copy()

j1, j2 = st.columns(2)

selecao1 = j1.selectbox("Escolha a primeira seleção", listaSelecoes1)
listaSelecoes2.remove(selecao1)

selecao2 = j2.selectbox("Escolha a segunda seleção", listaSelecoes2, index=1)
st.markdown("---")

# simulação do jogo
jogo = ProbabilidadesPartida(selecao1, selecao2)
prob = jogo["probabilidades"]
matriz = jogo["matriz"]

col1, col2, col3, col4, col5 = st.columns(5)
col1.image(selecoes.loc[selecao1, "LinkBandeiraGrande"])
col2.metric(selecao1, prob[0])
col3.metric("Empate", prob[1])
col4.metric(selecao2, prob[2])
col5.image(selecoes.loc[selecao2, "LinkBandeiraGrande"])

# prababilidades placares
st.markdown("---")
st.markdown("## 📊 Probabilidades dos Placares")

st.table(matriz.applymap(lambda x: f"{str(round(100*x,1))}%"))

# probabilidades do jogo
st.markdown("---")
st.markdown("## 🌎 Probabilidaes dos Jogos da Copa")
jogosCopa = pd.read_excel("outputEstimativaJogosCopa.xlsx", index_col=0)
st.table(jogosCopa[["grupo", "seleção1", "seleção2", "Vitória", "Empate", "Derrota"]])