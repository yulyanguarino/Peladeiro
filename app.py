import streamlit as st
import pandas as pd
import os
import random

# ---------------------------------------
# CONFIGURAÇÃO INICIAL
# ---------------------------------------
st.set_page_config(page_title="Sorteio de Times – Pelada", layout="wide")

ARQUIVO = "jogadores.xlsx"
COLUNAS = ["Nome", "Idade", "Posição"]
POSICOES = ["Goleiro", "Zagueiro", "Lateral", "Meio", "Atacante"]

# ---------------------------------------
# FUNÇÃO: CRIAR PLANILHA SE NÃO EXISTIR
# ---------------------------------------
def criar_arquivo_se_nao_existir():
    if not os.path.exists(ARQUIVO):
        df = pd.DataFrame(columns=COLUNAS)
        df.to_excel(ARQUIVO, index=False)

# ---------------------------------------
# FUNÇÃO: CARREGAR PLANILHA
# ---------------------------------------
def carregar_jogadores():
    criar_arquivo_se_nao_existir()
    return pd.read_excel(ARQUIVO)

# ---------------------------------------
# FUNÇÃO: SALVAR PLANILHA
# ---------------------------------------
def salvar_jogadores(df):
    df.to_excel(ARQUIVO, index=False)

# ---------------------------------------
# FUNÇÃO: SORTEIO EQUILIBRADO COM 1 GOLEIRO POR TIME
# ---------------------------------------
def sortear_times(df, num_times, cores):
    """
    Sorteia times balanceando por idade e posição,
    garantindo que cada time tenha no máximo 1 goleiro.
    """
    # Separar goleiros e outros jogadores
    goleiros = df[df["Posição"] == "Goleiro"].sample(frac=1).reset_index(drop=True)
    outros = df[df["Posição"] != "Goleiro"].sample(frac=1).reset_index(drop=True)

    total_jogadores = len(df)
    base = total_jogadores // num_times
    sobra = total_jogadores % num_times

    times = {i: [] for i in range(num_times)}
    limites = [base + 1 if i < sobra else base for i in range(num_times)]

    # Distribuir goleiros primeiro, 1 por time
    for i in range(len(goleiros)):
        times[i % num_times].append(goleiros.iloc[i])

    # Distribuir os outros jogadores
    idx_time = 0
    for i in range(len(outros)):
        while len(times[idx_time]) >= limites[idx_time]:
            idx_time += 1
        times[idx_time].append(outros.iloc[i])

    # Ordenar jogadores de cada time por idade (exceto goleiros que já estão fixos)
    for i in range(num_times):
        goleiro = [j for j in times[i] if j["Posição"] == "Goleiro"]
        demais = [j for j in times[i] if j["Posição"] != "Goleiro"]
        demais_sorted = sorted(demais, key=lambda x: x["Idade"])
        times[i] = goleiro + demais_sorted

    return times

# ============================================================
# 🟦 INTERFACE PRINCIPAL
# ============================================================
st.title("⚽ Sistema de Cadastro e Sorteio de Times – Pelada Final de Ano")

menu = st.sidebar.selectbox("Menu", ["Cadastro de Jogadores", "Configurar Sorteio"])

# ============================================================
# 🟩 ABA 1 – CADASTRO
# ============================================================
if menu == "Cadastro de Jogadores":
    st.header("📋 Cadastro de Jogadores")

    df = carregar_jogadores()
    st.subheader(f"Total de jogadores cadastrados: **{len(df)}**")

    # Campos iniciais
    if "nome" not in st.session_state:
        st.session_state.nome = ""
    if "idade" not in st.session_state:
        st.session_state.idade = 18
    if "posicao" not in st.session_state:
        st.session_state.posicao = POSICOES[0]

    # Formulário de cadastro
    with st.form("cadastro"):
        nome = st.text_input("Nome do jogador", value=st.session_state.nome, key="nome")
        idade = st.number_input("Idade", min_value=10, max_value=70, step=1, value=st.session_state.idade, key="idade")
        posicao = st.selectbox("Posição", POSICOES, index=POSICOES.index(st.session_state.posicao), key="posicao")

        enviar = st.form_submit_button("Adicionar jogador")

        if enviar:
            if nome.strip() == "":
                st.error("O nome é obrigatório!")
            else:
                novo = pd.DataFrame([[nome, idade, posicao]], columns=COLUNAS)
                df = pd.concat([df, novo], ignore_index=True)
                salvar_jogadores(df)
                st.success("Jogador cadastrado com sucesso!")
                # Limpar campos
                st.session_state.nome = ""
                st.session_state.idade = 18
                st.session_state.posicao = POSICOES[0]

    # Editar / Remover
    st.subheader("🔧 Editar / Remover Jogadores")
    if len(df) > 0:
        jogador_sel = st.selectbox("Selecione o jogador", df["Nome"].tolist())
        jogador_dados = df[df["Nome"] == jogador_sel].iloc[0]

        novo_nome = st.text_input("Nome", jogador_dados["Nome"])
        nova_idade = st.number_input("Idade", value=int(jogador_dados["Idade"]), min_value=10, max_value=70)
        nova_pos = st.selectbox("Posição", POSICOES, index=POSICOES.index(jogador_dados["Posição"]))

        col1, col2 = st.columns(2)
        if col1.button("Salvar alterações"):
            df.loc[df["Nome"] == jogador_sel, "Nome"] = novo_nome
            df.loc[df["Nome"] == jogador_sel, "Idade"] = nova_idade
            df.loc[df["Nome"] == jogador_sel, "Posição"] = nova_pos
            salvar_jogadores(df)
            st.success("Alterações salvas!")
        if col2.button("Remover jogador"):
            df = df[df["Nome"] != jogador_sel]
            salvar_jogadores(df)
            st.warning("Jogador removido!")

    st.markdown("---")
    if st.button("📂 Abrir planilha de jogadores"):
        os.system(f'start excel "{ARQUIVO}"')

# ============================================================
# 🟥 ABA 2 – CONFIGURAÇÃO DO SORTEIO
# ============================================================
elif menu == "Configurar Sorteio":
    st.header("🎲 Configuração do Sorteio")
    df = carregar_jogadores()

    if len(df) == 0:
        st.warning("Nenhum jogador cadastrado ainda.")
        st.stop()

    num_times = st.number_input("Número de times", min_value=2, max_value=20, step=1)

    # Cores para cada time
    cores = []
    for i in range(num_times):
        cor = st.text_input(f"Cor do time {i+1}", value=f"Time {i+1}")
        cores.append(cor)

    if st.button("🔵 SORTEAR TIMES", use_container_width=True):
        with st.spinner("Sorteando times..."):
            times = sortear_times(df, num_times, cores)

        st.success("Sorteio realizado com sucesso!")
        st.markdown("---")

        # Mostrar resultados
        for i in range(num_times):
            st.subheader(f"🏆 {cores[i]} — {len(times[i])} jogadores")
            for jog in times[i]:
                st.write(f"• **{jog['Nome']}** — {jog['Posição']}")
            st.markdown("---")
