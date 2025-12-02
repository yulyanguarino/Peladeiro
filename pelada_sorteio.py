# pelada_sorteio.py
# Rode com: python pelada_sorteio.py
# Depois pode transformar em .exe com: pyinstaller --onefile --windowed pelada_sorteio.py

import PySimpleGUI as sg
import pandas as pd
import os
import random
import numpy as np
from collections import defaultdict

# Nome do arquivo da planilha que armazena os jogadores.
ARQUIVO = "jogadores.xlsx"

# Cria o arquivo se não existir, apenas com os campos essenciais.
def criar_planilha():
    """Cria o arquivo jogadores.xlsx com as colunas Nome, Idade e Posição."""
    if not os.path.exists(ARQUIVO):
        df = pd.DataFrame(columns=["Nome/Apelido", "Idade", "Posição"])
        df.to_excel(ARQUIVO, index=False)

criar_planilha()

# --- Configuração da Interface (PySimpleGUI) ---
sg.theme('DarkGrey5')

layout_cadastro = [
    [sg.Text("Cadastro de Jogadores para a Pelada - 14/12", font=("Helvetica", 16, "bold"))],
    [sg.Text("Nome ou Apelido"), sg.Input(key="-NOME-", size=(20,1))],
    # Idade e Posição mantidos
    [sg.Text("Idade            "), sg.Input(key="-IDADE-", size=(10,1)), sg.Text("Posição"), sg.Combo(["Goleiro", "Zagueiro", "Lateral", "Meia", "Atacante", "Fixo", "Ala", "Pivô"], key="-POS-", size=(15,1))],
    [sg.Button("Adicionar Jogador"), sg.Button("Abrir Planilha"), sg.Button("Ir para Sorteio")],
    [sg.Text("", key="-TOTAL-", size=(40,1), font=("Helvetica", 12, "bold"))]
]

layout_sorteio = [
    [sg.Text("Configuração do Sorteio", font=("Helvetica", 16, "bold"))],
    [sg.Text("Quantos times?"), sg.Input("2", key="-TIMES-", size=(5,1))],
    [sg.Text("Cores dos coletes (separadas por vírgula):")],
    [sg.Input("Amarelo, Azul, Verde, Vermelho, Branco", key="-CORES-", size=(50,1))],
    [sg.Checkbox("Sorteio 100% aleatório (sem balanceamento)", key="-ALEATORIO-", default=False)],
    # A prioridade de balanceamento agora é baseada em Posição e Idade (experiência)
    [sg.Checkbox("Priorizar equilíbrio de idade e posição", default=True, disabled=True)], 
    [sg.Button("SORTEAR TIMES", size=(30,2), button_color=("white", "green"), font=("Helvetica", 14, "bold"))],
    [sg.Multiline("", key="-RESULTADO-", size=(80, 30), font=("Courier", 10))]
]

layout = [[sg.TabGroup([[sg.Tab("Cadastro", layout_cadastro), sg.Tab("Sorteio", layout_sorteio)]])]]

# Bloco TRY-EXCEPT adicionado para capturar erros na inicialização da janela
try:
    window = sg.Window("Pelada 14/12 - Sorteio de Times", layout, finalize=True)

    # Lógica para evitar erro ao ler uma planilha vazia ou corrompida na inicialização
    try:
        window["-TOTAL-"].update(f"Total de jogadores cadastrados: {len(pd.read_excel(ARQUIVO))}")
    except Exception:
        window["-TOTAL-"].update(f"Total de jogadores cadastrados: 0")


    def salvar_jogador(values):
        """Lê os valores do formulário e adiciona um novo jogador ao arquivo Excel."""
        try:
            # Prepara os dados do novo jogador, incluindo Posição
            novo = pd.DataFrame([{ 
                "Nome/Apelido": values["-NOME-"].strip() or "SemNome",
                "Idade": int(values["-IDADE-"]) if values["-IDADE-"].isdigit() and int(values["-IDADE-"]) > 0 else 25,
                "Posição": values["-POS-"] or "Meia", # Garante que a posição seja salva
            }])
            
            df = pd.read_excel(ARQUIVO)
            df = pd.concat([df, novo], ignore_index=True)
            df.to_excel(ARQUIVO, index=False)
            
            sg.popup("Jogador adicionado com sucesso!", title="Cadastro")
            window["-TOTAL-"].update(f"Total de jogadores cadastrados: {len(df)}")
            
            # Limpa APENAS os campos existentes
            window["-NOME-"].update("")
            window["-IDADE-"].update("")
            # Não precisa limpar a Posição, que é um ComboBox, a menos que você queira
            
        except Exception as e:
            sg.popup(f"Erro ao salvar jogador: {e}. Verifique se a planilha Excel não está aberta.", title="Erro")


    def sortear_times(values):
        """Carrega os jogadores e realiza o sorteio balanceado ou aleatório."""
        try:
            df = pd.read_excel(ARQUIVO)
            # Garante que a coluna 'Idade' é numérica, essencial para o sorteio
            df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce').fillna(25).astype(int) 
        except Exception as e:
            sg.popup(f"Erro ao ler planilha: {e}. Certifique-se de que o arquivo '{ARQUIVO}' existe e está fechado.", title="Erro de Planilha")
            return

        if len(df) < 2:
            sg.popup("Cadastre pelo menos 2 jogadores para o sorteio!", title="Erro")
            return
        
        # 1. Validação do número de times
        try:
            n_times = int(values["-TIMES-"])
            if n_times < 2 or n_times > len(df):
                sg.popup(f"Número de times inválido. Deve ser entre 2 e {len(df)}.", title="Erro de Configuração")
                return
        except:
            sg.popup("Número de times inválido!", title="Erro de Configuração")
            return

        # 2. Configuração das cores
        cores = [c.strip() for c in values["-CORES-"].split(",")]
        while len(cores) < n_times:
            cores.append(f"Cor {len(cores)+1}")

        jogadores = df.to_dict("records")
        
        if values["-ALEATORIO-"]:
            # Sorteio 100% aleatório
            random.shuffle(jogadores)
            times = [jogadores[i::n_times] for i in range(n_times)]
        else:
            # SORTEIO BALANCEADO POR POSIÇÃO E IDADE
            
            # 1. Classifica jogadores por Idade (para distribuir os mais velhos/experientes)
            jogadores.sort(key=lambda x: -x["Idade"]) 
            
            times = [[] for _ in range(n_times)]
            posicoes_times = [defaultdict(int) for _ in range(n_times)]

            for jogador in jogadores:
                melhor_score = float('inf')
                time_escolhido = -1
                
                # Tenta encontrar o time com o menor número de jogadores na mesma posição
                for i, pos_count in enumerate(posicoes_times):
                    posicao_do_jogador = jogador["Posição"]
                    
                    # Prioridade 1: Equilíbrio de Posição
                    score_posicao = pos_count[posicao_do_jogador]
                    
                    # Prioridade 2: Equilíbrio de Idade Média
                    time_atual = times[i]
                    media_idade = sum(p["Idade"] for p in time_atual) / len(time_atual) if time_atual else 0
                    
                    # Score final: prioriza posição (peso alto) e depois a menor idade média
                    score = (score_posicao * 100) + media_idade
                    
                    if score < melhor_score:
                        melhor_score = score
                        time_escolhido = i
                    elif score == melhor_score:
                        # Em caso de empate na Posição/Idade, escolhe aleatoriamente
                        if random.choice([True, False]):
                            time_escolhido = i

                # Adiciona o jogador ao time escolhido
                times[time_escolhido].append(jogador)
                posicoes_times[time_escolhido][jogador["Posição"]] += 1
                
        # Monta resultado bonito
        resultado = f"SORTEIO REALIZADO! Total: {len(jogadores)} jogadores\n"
        resultado += "="*60 + "\n\n"
        
        for i, time in enumerate(times):
            if not time: continue
            
            media_idade = sum(p["Idade"] for p in time) / len(time)
            
            # Contagem de Posições
            contagem_pos = defaultdict(int)
            for p in time:
                contagem_pos[p['Posição']] += 1
                
            resultado += f"Time {cores[i].upper()} (Time {i+1}) - {len(time)} jogadores\n"
            resultado += f"Média idade: {media_idade:.0f} anos\n"
            
            # Exibe a contagem de posições
            pos_str = ", ".join([f"{pos}: {count}" for pos, count in contagem_pos.items()])
            resultado += f"Posições: {pos_str}\n"

            resultado += "Jogadores:\n"
            for p in time:
                # Note que 'Obs' não é mais exibido
                resultado += f"• {p['Nome/Apelido']} ({p['Posição']}, {p['Idade']} anos)\n"
            resultado += "\n" + "-"*50 + "\n\n"
        
        window["-RESULTADO-"].update(resultado)

    # --- Loop de Eventos da Janela (não alterado) ---
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED:
            break
            
        elif event == "Adicionar Jogador":
            salvar_jogador(values)
            
        elif event == "Abrir Planilha":
            try:
                os.startfile(ARQUIVO)
            except Exception as e:
                sg.popup(f"Erro ao abrir o arquivo: {e}. Certifique-se de que ele não está sendo editado.", title="Erro")
                
        elif event == "SORTEAR TIMES":
            sortear_times(values) # Passa 'values' para a função

    window.close()

except Exception as e:
    # Captura qualquer erro que impeça a janela de abrir
    sg.popup_error(f"ERRO CRÍTICO NA INICIALIZAÇÃO:\n\n{e}\n\nO programa será fechado.", title="Erro Fatal")