import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import time


class Processo:
    def __init__(self, nome):
        self.nome = nome
        self.alocados = {}  # {recurso: quantidade}
        self.requisitados = set()


class Recurso:
    def __init__(self, nome, quantidade):
        self.nome = nome
        self.quantidade = quantidade
        self.disponivel = quantidade


# Globais
processos = {}
recursos = {}
cores_por_processo = {}
passos_simulacao = []

root = tk.Tk()
root.title("Analisador Estático de Deadlock")

frame_principal = ttk.Frame(root, padding=10)
frame_principal.pack(fill=tk.BOTH, expand=True)

# Entrada de processos
entrada_proc = ttk.Entry(frame_principal, width=15)
entrada_proc.grid(row=0, column=1)
ttk.Label(frame_principal, text="Processo:").grid(row=0, column=0, sticky="w")
ttk.Button(
    frame_principal, text="Adicionar Processo", command=lambda: adicionar_processo(entrada_proc.get())
).grid(row=0, column=2)

# Entrada de recursos
entrada_rec = ttk.Entry(frame_principal, width=15)
entrada_rec.grid(row=1, column=1)
ttk.Label(frame_principal, text="Recurso:").grid(row=1, column=0, sticky="w")
entrada_qtd = ttk.Entry(frame_principal, width=5)
entrada_qtd.grid(row=1, column=2)
ttk.Label(frame_principal, text="Qtd:").grid(row=1, column=2, sticky="e")
ttk.Button(
    frame_principal,
    text="Adicionar Recurso",
    command=lambda: adicionar_recurso(entrada_rec.get(), entrada_qtd.get()),
).grid(row=1, column=3)

# Menus suspensos
var_proc = tk.StringVar()
var_rec = tk.StringVar()
menu_proc = ttk.OptionMenu(frame_principal, var_proc, "")
menu_rec = ttk.OptionMenu(frame_principal, var_rec, "")
menu_proc.grid(row=2, column=1)
menu_rec.grid(row=2, column=3)
ttk.Label(frame_principal, text="Processo:").grid(row=2, column=0)
ttk.Label(frame_principal, text="Recurso:").grid(row=2, column=2)

# Botões de relacionamento
frame_botoes = ttk.Frame(frame_principal)
frame_botoes.grid(row=3, column=0, columnspan=4, pady=5)
ttk.Button(
    frame_botoes, text="Alocar", command=lambda: alocar(var_proc.get(), var_rec.get())
).pack(side=tk.LEFT, padx=5)
ttk.Button(
    frame_botoes,
    text="Requisitar",
    command=lambda: requisitar(var_proc.get(), var_rec.get()),
).pack(side=tk.LEFT, padx=5)
ttk.Button(
    frame_botoes, text="Analisar Deadlock", command=lambda: analisar_deadlock()
).pack(side=tk.LEFT, padx=5)
ttk.Button(
    frame_botoes, text="Visualizar Resolução", command=lambda: mostrar_popup_resolucao()
).pack(side=tk.LEFT, padx=5)
ttk.Button(
    frame_botoes,
    text="Desfazer (Undo)",
    command=lambda: desfazer(var_proc.get(), var_rec.get()),
).pack(side=tk.LEFT, padx=5)
ttk.Button(frame_botoes, text="Apagar Tudo", command=lambda: limpar_tudo()).pack(
    side=tk.LEFT, padx=5
)

# Status
area_status = tk.Text(frame_principal, height=10, width=70)
area_status.grid(row=4, column=0, columnspan=5, pady=5)

# Gráfico principal
fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def adicionar_processo(nome):
    if nome and nome not in processos:
        processos[nome] = Processo(nome)
        cores_por_processo[nome] = f"#{random.randint(0, 0xFFFFFF):06x}"
        atualizar_menus()
        area_status.insert(tk.END, f"Processo '{nome}' adicionado.\n")
        area_status.see(tk.END)
        desenhar_grafo()


def adicionar_recurso(nome, qtd):
    try:
        q = int(qtd)
    except ValueError:
        messagebox.showerror("Erro", "Quantidade inválida.")
        return
    if nome and nome not in recursos:
        recursos[nome] = Recurso(nome, q)
        atualizar_menus()
        area_status.insert(tk.END, f"Recurso '{nome}' adicionado com quantidade {q}.\n")
        area_status.see(tk.END)
        desenhar_grafo()


def alocar(proc, rec):
    if proc in processos and rec in recursos:
        recurso = recursos[rec]
        if recurso.disponivel > 0:
            processos[proc].alocados[rec] = processos[proc].alocados.get(rec, 0) + 1
            recurso.disponivel -= 1
            area_status.insert(
                tk.END,
                f"{proc} agora possui {rec} (total: {processos[proc].alocados[rec]}).\n",
            )
        else:
            area_status.insert(tk.END, f"Não há {rec} disponível para {proc}.\n")
        area_status.see(tk.END)
        desenhar_grafo()


def requisitar(proc, rec):
    if proc in processos and rec in recursos:
        processos[proc].requisitados.add(rec)
        area_status.insert(tk.END, f"{proc} deseja {rec}.\n")
        area_status.see(tk.END)
        desenhar_grafo()


def desfazer(proc, rec):
    if proc in processos and rec in recursos:
        if rec in processos[proc].alocados and processos[proc].alocados[rec] > 0:
            processos[proc].alocados[rec] -= 1
            recursos[rec].disponivel += 1
            if processos[proc].alocados[rec] == 0:
                del processos[proc].alocados[rec]
            area_status.insert(tk.END, f"{proc} liberou uma unidade de {rec}.\n")
        elif rec in processos[proc].requisitados:
            processos[proc].requisitados.remove(rec)
            area_status.insert(tk.END, f"{proc} cancelou requisição de {rec}.\n")
        else:
            area_status.insert(
                tk.END, f"{proc} não possui vínculo com {rec} para desfazer.\n"
            )
        area_status.see(tk.END)
        desenhar_grafo()


def atualizar_menus():
    menu_proc["menu"].delete(0, "end")
    menu_rec["menu"].delete(0, "end")
    for p in processos:
        menu_proc["menu"].add_command(label=p, command=tk._setit(var_proc, p))
    for r in recursos:
        menu_rec["menu"].add_command(label=r, command=tk._setit(var_rec, r))
    if processos:
        var_proc.set(list(processos.keys())[0])
    if recursos:
        var_rec.set(list(recursos.keys())[0])


def desenhar_grafo():
    G = nx.DiGraph()
    ax.clear()

    # Calcular alocação por recurso (somando quantidades alocadas)
    contagem_alocados = {r: 0 for r in recursos}
    for p in processos.values():
        for rec, qtd in p.alocados.items():
            contagem_alocados[rec] += qtd

    # Adicionar nós de recursos com label corrigido para evitar negativos
    for r_nome in recursos:
        rec_obj = recursos[r_nome]
        alocado = contagem_alocados[r_nome]
        disponivel_agora = max(0, rec_obj.quantidade - alocado)
        rotulo = f"{r_nome} ({disponivel_agora}/{rec_obj.quantidade})"
        G.add_node(r_nome, shape="circle", label=rotulo)

    # Adicionar nós de processos e arestas (alocação e requisição)
    for p_nome in processos:
        G.add_node(p_nome, shape="box", label=p_nome)
        cor = cores_por_processo[p_nome]

        # Arestas de alocação com labels de quantidade
        for rec, qtd in processos[p_nome].alocados.items():
            G.add_edge(rec, p_nome, color=cor, style="solid", kind="alloc", label=str(qtd))

        # Arestas de requisição
        for rec in processos[p_nome].requisitados:
            G.add_edge(p_nome, rec, color=cor, style="dashed", kind="req")

    # Definir posições dos nós
    pos = {}
    y_proc = 1
    y_rec = 0

    for i, r in enumerate(sorted(recursos)):
        pos[r] = (i * 2, y_rec)

    for i, p in enumerate(sorted(processos)):
        pos[p] = (i * 2, y_proc)

    # Separar nós por tipo
    nos_processo = [n for n in G.nodes if G.nodes[n]["shape"] == "box"]
    nos_recurso = [n for n in G.nodes if G.nodes[n]["shape"] == "circle"]

    # Desenhar recursos como círculos
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=nos_recurso,
        node_shape="o",
        node_color="lightgreen",
        ax=ax,
    )

    # Desenhar processos como quadrados
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=nos_processo,
        node_shape="s",
        node_color="lightblue",
        ax=ax,
    )

    # Desenhar arestas com estilos e cores
    for u, v, data in G.edges(data=True):
        estilo = data.get("style", "solid")
        cor = data.get("color", "black")
        nx.draw_networkx_edges(
            G,
            pos,
            ax=ax,
            edgelist=[(u, v)],
            edge_color=cor,
            style=estilo,
            connectionstyle="arc3,rad=0.2",
            arrows=True,
            arrowstyle="->",
            arrowsize=20,
        )

    # Desenhar rótulos dos nós
    rotulos = {n: G.nodes[n].get("label", n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=rotulos, ax=ax)

    canvas.draw()


def desenhar_estado_grafo(eixo_alvo, processos_atuais, recursos_atuais, processos_em_deadlock=None):
    G = nx.DiGraph()
    eixo_alvo.clear()

    # Calcular alocação por recurso (somando quantidades alocadas)
    contagem_alocados = {r: 0 for r in recursos_atuais}
    for p in processos_atuais.values():
        for rec, qtd in p.alocados.items():
            contagem_alocados[rec] += qtd

    # Adicionar nós de recursos com label
    for r_nome, r_obj in recursos_atuais.items():
        alocado = contagem_alocados[r_nome]
        disponivel_agora = max(0, r_obj.quantidade - alocado)
        rotulo = f"{r_nome} ({disponivel_agora}/{r_obj.quantidade})"
        G.add_node(r_nome, shape="circle", label=rotulo)

    # Adicionar nós de processos e arestas (alocação e requisição)
    for p_nome, p_obj in processos_atuais.items():
        # Definir cor do nó do processo: normal, em deadlock, ou terminado?
        cor_no = "lightblue"
        if processos_em_deadlock and p_nome in processos_em_deadlock:
            cor_no = "red"
        # Se o processo não tem alocações nem requisições, talvez esteja "terminado"
        elif not p_obj.alocados and not p_obj.requisitados:
            cor_no = "lightgray"

        G.add_node(p_nome, shape="box", label=p_nome, node_color=cor_no)
        cor = cores_por_processo.get(p_nome, "#000000")

        # Arestas de alocação
        for rec, qtd in p_obj.alocados.items():
            G.add_edge(
                rec, p_nome, color=cor, style="solid", kind="alloc", label=str(qtd)
            )

        # Arestas de requisição
        for rec in p_obj.requisitados:
            G.add_edge(p_nome, rec, color=cor, style="dashed", kind="req")

    # Definir posições dos nós (mesma lógica da função desenhar_grafo)
    pos = {}
    y_proc = 1
    y_rec = 0

    # Ordenar para consistência
    recursos_ordenados = sorted(recursos_atuais.keys())
    processos_ordenados = sorted(processos_atuais.keys())

    for i, r in enumerate(recursos_ordenados):
        pos[r] = (i * 2, y_rec)

    for i, p in enumerate(processos_ordenados):
        pos[p] = (i * 2, y_proc)

    # Separar nós por tipo
    nos_processo = [n for n in G.nodes if G.nodes[n]["shape"] == "box"]
    nos_recurso = [n for n in G.nodes if G.nodes[n]["shape"] == "circle"]

    # Desenhar nós de recursos
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=nos_recurso,
        node_shape="o",
        node_color="lightgreen",
        ax=eixo_alvo,
    )

    # Desenhar nós de processos (com cores especiais se necessário)
    for no in nos_processo:
        cor_no = G.nodes[no].get("node_color", "lightblue")
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=[no],
            node_shape="s",
            node_color=cor_no,
            ax=eixo_alvo,
        )

    # Desenhar arestas
    for u, v, data in G.edges(data=True):
        estilo = data.get("style", "solid")
        cor = data.get("color", "black")
        nx.draw_networkx_edges(
            G,
            pos,
            ax=eixo_alvo,
            edgelist=[(u, v)],
            edge_color=cor,
            style=estilo,
            connectionstyle="arc3,rad=0.2",
            arrows=True,
            arrowstyle="->",
            arrowsize=20,
        )

    # Desenhar rótulos dos nós
    rotulos = {n: G.nodes[n].get("label", n) for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=rotulos, ax=eixo_alvo)

    # Ajustar a visualização
    eixo_alvo.set_title("Grafo de Alocação e Requisição")
    eixo_alvo.axis("off")


def analisar_deadlock():
    trabalho = {
        r: rec.quantidade - sum(p.alocados.get(r, 0) for p in processos.values())
        for r, rec in recursos.items()
    }
    finalizado = {nome_proc: False for nome_proc in processos}
    explicacao = []

    mudou = True
    while mudou:
        mudou = False
        for nome_proc, proc in processos.items():
            if finalizado[nome_proc]:
                continue
            # Verifica se todas as requisições podem ser atendidas
            pode_prosseguir = True
            nao_atendido = []
            for r in proc.requisitados:
                if not trabalho[r]:
                    pode_prosseguir = False
                    nao_atendido.append(r)
            if pode_prosseguir:
                explicacao.append(
                    f"[OK] {nome_proc} pôde prosseguir (requisitou {[r for r in proc.requisitados]}), liberando recursos {proc.alocados}."
                )
                for r, qtd in proc.alocados.items():
                    trabalho[r] += qtd
                finalizado[nome_proc] = True
                mudou = True
            else:
                if nao_atendido:
                    explicacao.append(
                        f"[ESPERA] {nome_proc} não pôde prosseguir: esperando recurso(s) {nao_atendido}."
                    )

    em_deadlock = [p for p, status in finalizado.items() if not status]
    area_status.insert(tk.END, "\n--- Análise de Deadlock ---\n")
    for linha in explicacao:
        area_status.insert(tk.END, linha + "\n")

    if em_deadlock:
        area_status.insert(
            tk.END, f"\n[DEADLOCK] Detectado entre: {', '.join(em_deadlock)}\n"
        )
        messagebox.showwarning(
            "Deadlock", f"Deadlock detectado entre: {', '.join(em_deadlock)}"
        )
    else:
        area_status.insert(
            tk.END,
            "\n[SOLUÇÃO] Todos os processos puderam prosseguir. Nenhum deadlock.\n",
        )

    area_status.see(tk.END)


def analisar_simulacao_deadlock():
    # Criar cópias dos estados atuais
    processos_temp = {nome: Processo(p.nome) for nome, p in processos.items()}
    for nome, obj_p in processos.items():
        processos_temp[nome].alocados = obj_p.alocados.copy()
        processos_temp[nome].requisitados = obj_p.requisitados.copy()

    recursos_temp = {nome: Recurso(r.nome, r.quantidade) for nome, r in recursos.items()}
    for nome, obj_r in recursos.items():
        recursos_temp[nome].disponivel = obj_r.disponivel

    # Calcular recursos inicialmente disponíveis
    trabalho = {
        r: recursos_temp[r].quantidade
        - sum(p.alocados.get(r, 0) for p in processos_temp.values())
        for r, rec in recursos_temp.items()
    }

    finalizado = {nome_proc: False for nome_proc in processos_temp}

    passos_simulacao_atuais = []

    # Snapshot inicial
    processos_inicial = {nome: Processo(p.nome) for nome, p in processos_temp.items()}
    for nome, obj_p in processos_temp.items():
        processos_inicial[nome].alocados = obj_p.alocados.copy()
        processos_inicial[nome].requisitados = obj_p.requisitados.copy()

    recursos_inicial = {nome: Recurso(r.nome, r.quantidade) for nome, r in recursos_temp.items()}
    for nome, obj_r in recursos_temp.items():
        recursos_inicial[nome].disponivel = obj_r.disponivel

    passos_simulacao_atuais.append(
        {
            "processos": processos_inicial,
            "recursos": recursos_inicial,
            "desc": "Estado Inicial do Sistema",
            "deadlocked": [],
        }
    )

    mudou = True
    contador_iteracoes = 0
    max_iteracoes = len(processos_temp) * 2

    while mudou and contador_iteracoes < max_iteracoes:
        mudou = False
        contador_iteracoes += 1

        for nome_proc, proc in processos_temp.items():
            if finalizado[nome_proc]:
                continue

            pode_prosseguir = True
            nao_atendido = []
            for r in proc.requisitados:
                if not trabalho[r]:
                    pode_prosseguir = False
                    nao_atendido.append(r)

            if pode_prosseguir:
                # Processo pode prosseguir
                descricao = f"[OK] {nome_proc} pôde prosseguir."

                # Libera recursos alocados pelo processo
                for r_nome, qtd in proc.alocados.items():
                    trabalho[r_nome] += qtd
                    if r_nome in recursos_temp:
                        recursos_temp[r_nome].disponivel += qtd

                # Marca o processo como terminado
                finalizado[nome_proc] = True
                proc.alocados.clear()
                proc.requisitados.clear()

                mudou = True

                # Salva snapshot após execução do processo
                snapshot_processos = {nome: Processo(p.nome) for nome, p in processos_temp.items()}
                for nome, obj_p in processos_temp.items():
                    snapshot_processos[nome].alocados = obj_p.alocados.copy()
                    snapshot_processos[nome].requisitados = obj_p.requisitados.copy()

                snapshot_recursos = {nome: Recurso(r.nome, r.quantidade) for nome, r in recursos_temp.items()}
                for nome, obj_r in recursos_temp.items():
                    snapshot_recursos[nome].disponivel = obj_r.disponivel

                passos_simulacao_atuais.append(
                    {
                        "processos": snapshot_processos,
                        "recursos": snapshot_recursos,
                        "desc": descricao,
                        "deadlocked": [],
                    }
                )

    # Estado final
    em_deadlock_final = [p for p, feito in finalizado.items() if not feito]

    processos_final = {nome: Processo(p.nome) for nome, p in processos_temp.items()}
    for nome, obj_p in processos_temp.items():
        processos_final[nome].alocados = obj_p.alocados.copy()
        processos_final[nome].requisitados = obj_p.requisitados.copy()

    recursos_final = {
        nome: Recurso(r.nome, r.quantidade) for nome, r in recursos_temp.items()
    }
    for nome, obj_r in recursos_temp.items():
        recursos_final[nome].disponivel = obj_r.disponivel

    descricao_final = (
        f"[DEADLOCK] Detectado entre: {', '.join(em_deadlock_final)}"
        if em_deadlock_final
        else "[SOLUÇÃO] Todos os processos puderam prosseguir. Nenhum deadlock."
    )

    passos_simulacao_atuais.append(
        {
            "processos": processos_final,
            "recursos": recursos_final,
            "desc": descricao_final,
            "deadlocked": em_deadlock_final,
        }
    )

    return passos_simulacao_atuais


def mostrar_popup_resolucao():
    global passos_simulacao
    passos_simulacao = analisar_simulacao_deadlock()

    if not passos_simulacao:
        messagebox.showinfo("Simulação", "Não há processos ou recursos para simular.")
        return

    janela_popup = Toplevel(root)
    janela_popup.title("Resolução Visual de Deadlock")
    janela_popup.geometry("800x600")

    # Frame para o grafo e a descrição
    frame_grafo = ttk.Frame(janela_popup)
    frame_grafo.pack(fill=tk.BOTH, expand=True)

    fig_popup, ax_popup = plt.subplots(figsize=(7, 5))
    canvas_popup = FigureCanvasTkAgg(fig_popup, master=frame_grafo)
    widget_canvas_popup = canvas_popup.get_tk_widget()
    widget_canvas_popup.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    rotulo_desc = ttk.Label(janela_popup, text="", wraplength=750, justify=tk.LEFT)
    rotulo_desc.pack(side=tk.TOP, pady=5)

    indice_passo_atual = 0

    def mostrar_proximo_passo():
        nonlocal indice_passo_atual
        if indice_passo_atual < len(passos_simulacao):
            dados_passo = passos_simulacao[indice_passo_atual]

            # Limpa o eixo antes de desenhar o novo estado
            ax_popup.clear()
            desenhar_estado_grafo(
                ax_popup,
                dados_passo["processos"],
                dados_passo["recursos"],
                dados_passo["deadlocked"],
            )

            rotulo_desc.config(
                text=f"Passo {indice_passo_atual + 1}/{len(passos_simulacao)}: {dados_passo['desc']}"
            )
            canvas_popup.draw()

            indice_passo_atual += 1
            if indice_passo_atual == len(passos_simulacao):
                botao_proximo.config(text="Fim da Simulação", state=tk.DISABLED)
        else:
            botao_proximo.config(text="Fim da Simulação", state=tk.DISABLED)

    botao_proximo = ttk.Button(janela_popup, text="Próximo Passo", command=mostrar_proximo_passo)
    botao_proximo.pack(side=tk.BOTTOM, pady=10)

    # Exibe o primeiro passo ao abrir o pop-up
    mostrar_proximo_passo()


def limpar_tudo():
    processos.clear()
    recursos.clear()
    cores_por_processo.clear()
    global passos_simulacao
    passos_simulacao = []
    var_proc.set("")
    var_rec.set("")
    atualizar_menus()
    area_status.delete(1.0, tk.END)
    ax.clear()
    canvas.draw()


if __name__ == '__main__':
    root.mainloop()