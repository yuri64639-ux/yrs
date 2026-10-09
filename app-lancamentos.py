import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

class SistemaVendas:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Automação de Vendas - Restaurante")
        self.root.geometry("700x550")

        # Inicializa a conexão com o banco de dados local
        self.conectar_banco()
        
        self.carrinho = []
        self.total = 0.0

        # Inicia pela tela de login para definir as permissões das abas
        self.criar_tela_login()

    def conectar_banco(self):
        """Cria o arquivo de banco de dados e as tabelas se não existirem."""
        self.conn = sqlite3.connect("vendas.db")
        self.cursor = self.conn.cursor()
        
        # Cria tabela de produtos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                preco REAL NOT NULL
            )
        """)
        
        # Cria tabela de histórico de vendas gravadas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                total_item REAL NOT NULL,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

        # Alimenta o banco com os produtos padrão se estiver vazio
        self.cursor.execute("SELECT COUNT(*) FROM produtos")
        if self.cursor.fetchone() == 0:
            produtos_padrao = [
                ("Camiseta", 49.90),
                ("Calça Jeans", 119.90),
                ("Tênis", 199.90),
                ("Boné", 29.90),
                ("Suco de Laranja", 9.90),
                ("Almoço Comercial", 29.90),
                ("Sobremesa da Casa", 14.90)
            ]
            self.cursor.executemany("INSERT INTO produtos (nome, preco) VALUES (?, ?)", produtos_padrao)
            self.conn.commit()

    def criar_tela_login(self):
        """Gera a interface de login obrigatória do sistema."""
        self.frame_login = tk.Frame(self.root, bd=2, relief="groove", padx=25, pady=25)
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")

        lbl_log = tk.Label(self.frame_login, text="LOGIN DO OPERADOR", font=("Arial", 12, "bold"))
        lbl_log.pack(pady=10)

        tk.Label(self.frame_login, text="Usuário (admin ou garcon):", font=("Arial", 10)).pack(anchor="w")
        self.txt_usuario = tk.Entry(self.frame_login, font=("Arial", 11), width=25)
        self.txt_usuario.pack(pady=5)
        self.txt_usuario.insert(0, "garcon")  # Valor padrão facilitador

        btn_entrar = tk.Button(self.frame_login, text="Entrar no Sistema", command=self.autenticar, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
        btn_entrar.pack(pady=15, fill="x")

    def autenticar(self):
        """Valida o perfil digitado e destroi o frame de login."""
        usuario = self.txt_usuario.get().strip().lower()

        if usuario in ["admin", "gerente", "administrador"]:
            self.frame_login.destroy()
            self.criar_painel_principal(perfil="admin")
        elif usuario in ["garcon", "garçom", "garco", "atendente"]:
            self.frame_login.destroy()
            self.criar_painel_principal(perfil="garcon")
        else:
            messagebox.showerror("Erro de Autenticação", "Usuário inválido! Utilize 'admin' ou 'garcon'.")

    def criar_painel_principal(self, perfil):
        """Monta o Notebook de abas preservando a lógica de restrição do Garçom."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # 1. Aba Operacional de Vendas / Pedidos
        self.aba_vendas = tk.Frame(self.notebook)
        self.notebook.add(self.aba_vendas, text=" Lançamento de Vendas ")
        self.montar_aba_vendas(self.aba_vendas)

        # 2. Aba Restrita de Gerência / Relatórios
        self.aba_gerencia = tk.Frame(self.notebook)
        self.notebook.add(self.aba_gerencia, text=" Painel de Gerência ")
        self.montar_aba_gerencia(self.aba_gerencia)

        # REGRA CRÍTICA: Oculta completamente a aba se logado como garçom
        if perfil == "garcon":
            self.notebook.forget(self.aba_gerencia)
            lbl_user = tk.Label(self.root, text="Operador: Garçom (Aba Gerência Ocultada)", fg="blue", font=("Arial", 9, "italic"))
            lbl_user.pack(anchor="ne", padx=10, pady=2)
        else:
            lbl_user = tk.Label(self.root, text="Operador: Administrador (Acesso Total)", fg="red", font=("Arial", 9, "italic"))
            lbl_user.pack(anchor="ne", padx=10, pady=2)

    def montar_aba_vendas(self, container):
        """Contém todas as lógicas e campos do caixa e carrinho de compras."""
        lbl_titulo = tk.Label(container, text="Painel de Vendas Comercial", font=("Arial", 14, "bold"), fg="#333")
        lbl_titulo.pack(pady=10)

        # Container de Seleção de Produtos
        frame_produto = tk.Frame(container)
        frame_produto.pack(pady=5)

        tk.Label(frame_produto, text="Produto:", font=("Arial", 11)).grid(row=0, column=0, padx=5)
        self.cb_produto = ttk.Combobox(frame_produto, state="readonly", font=("Arial", 11), width=20)
        self.cb_produto.grid(row=0, column=1, padx=5)

        tk.Label(frame_produto, text="Qtd:", font=("Arial", 11)).grid(row=0, column=2, padx=5)
        self.txt_qtd = tk.Entry(frame_produto, width=5, font=("Arial", 11), justify="center")
        self.txt_qtd.insert(0, "1")
        self.txt_qtd.grid(row=0, column=3, padx=5)

        btn_adicionar = tk.Button(frame_produto, text="Adicionar Item", command=self.adicionar_produto, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), relief="groove")
        btn_adicionar.grid(row=0, column=4, padx=10)

        # Listagem do Carrinho (Treeview)
        self.tree = ttk.Treeview(container, columns=("Produto", "Qtd", "Preço Un.", "Total"), show="headings", height=10)
        self.tree.heading("Produto", text="Item")
        self.tree.heading("Qtd", text="Quantidade")
        self.tree.heading("Preço Un.", text="Preço Unitário")
        self.tree.heading("Total", text="Subtotal")
        
        self.tree.column("Produto", width=180, anchor="w")
        self.tree.column("Qtd", width=80, anchor="center")
        self.tree.column("Preço Un.", width=110, anchor="e")
        self.tree.column("Total", width=110, anchor="e")
        self.tree.pack(pady=10, padx=20, fill="x")

        # Rodapé de Fechamento de Vendas
        frame_total = tk.Frame(container)
        frame_total.pack(pady=10, fill="x", padx=20)

        self.lbl_total = tk.Label(frame_total, text="Total: R$ 0,00", font=("Arial", 14, "bold"), fg="#D32F2F")
        self.lbl_total.pack(side="left")

        btn_finalizar = tk.Button(frame_total, text="Concluir e Salvar Venda", command=self.finalizar_venda, bg="#1976D2", fg="white", font=("Arial", 11, "bold"), relief="raised", padx=10)
        btn_finalizar.pack(side="right")

        self.carregar_produtos_do_banco()

    def montar_aba_gerencia(self, container):
        """Painel Administrativo restrito para donos e gerentes."""
        lbl_titulo = tk.Label(container, text="Painel de Controle Gerencial", font=("Arial", 14, "bold"), fg="#D32F2F")
        lbl_titulo.pack(pady=20)
        
        lbl_info = tk.Label(container, text="[ÁREA RESTRITA - CRÍTICA]
Aqui constam relatórios de lucratividade, faturamento consolidado e edição de estoque.", font=("Arial", 11), justify="center")
        lbl_info.pack(pady=20)
        
        btn_config = tk.Button(container, text="Configurar Margens de Lucro", font=("Arial", 10), state="disabled", width=30)
        btn_config.pack(pady=5)
        
        btn_relat = tk.Button(container, text="Exportar Fechamento do Mês (CSV)", font=("Arial", 10), state="disabled", width=30)
        btn_relat.pack(pady=5)

    def carregar_produtos_do_banco(self):
        """Busca os produtos salvos no banco de dados e joga na lista da tela."""
        self.cursor.execute("SELECT nome FROM produtos")
        nomes_produtos = [linha[0] for linha in self.cursor.fetchall()]
        self.cb_produto["values"] = nomes_produtos
        if nomes_produtos:
            self.cb_produto.current(0)

    def obter_preco_do_banco(self, nome_produto):
        """Consulta o preço atual de um produto dentro do banco de dados."""
        self.cursor.execute("SELECT preco FROM produtos WHERE nome = ?", (nome_produto,))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado else 0.0

    def adicionar_produto(self):
        produto = self.cb_produto.get()
        qtd_str = self.txt_qtd.get()

        if not produto:
            messagebox.showerror("Erro", "Por favor, selecione um produto!")
            return

        if not qtd_str.isdigit() or int(qtd_str) <= 0:
            messagebox.showerror("Erro", "Insira uma quantidade válida acima de zero!")
            return

        qtd = int(qtd_str)
        preco_un = self.obter_preco_do_banco(produto)
        preco_total = preco_un * qtd

        self.tree.insert("", "end", values=(produto, qtd, f"R$ {preco_un:.2f}", f"R$ {preco_total:.2f}"))
        self.carrinho.append({"produto": produto, "qtd": qtd, "total": preco_total})
        
        self.total += preco_total
        self.lbl_total.config(text=f"Total: R$ {self.total:.2f}")
        
        self.txt_qtd.delete(0, tk.END)
        self.txt_qtd.insert(0, "1")

    def finalizar_venda(self):
        if not self.carrinho:
            messagebox.showwarning("Aviso", "O carrinho de compras está vazio!")
            return

        # Pergunta de confirmação com Sim ou Não antes de registrar
        confirmar = messagebox.askyesno("Confirmação do Caixa", f"Deseja fechar e salvar esta venda no valor de R$ {self.total:.2f}?")
        if not confirmar:
            return

        # Grava os itens salvos no banco de dados local
        for item in self.carrinho:
            self.cursor.execute(
                "INSERT INTO historico_vendas (produto, quantity, total_item) VALUES (?, ?, ?)" if False else
                "INSERT INTO historico_vendas (produto, quantidade, total_item) VALUES (?, ?, ?)",
                (item["produto"], item["qtd"], item["total"])
            )
        self.conn.commit()
        
        # Limpa o carrinho e reseta os estados da venda
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.carrinho.clear()
        self.total = 0.0
        self.lbl_total.config(text="Total: R$ 0,00")
        messagebox.showinfo("Sucesso", "Venda gravada com sucesso!")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    window = tk.Tk()
    app = SistemaVendas(window)
    window.mainloop()
