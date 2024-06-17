import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from cryptography.fernet import Fernet
import random
import string
import os
import pyperclip

def gerar_chave():
    chave = Fernet.generate_key()
    with open('chave.key', 'wb') as chave_file:
        chave_file.write(chave)
    return chave

def carregar_chave():
    return open('chave.key', 'rb').read()

def gerar_senha(comprimento):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    senha = ''.join(random.choice(caracteres) for _ in range(comprimento))
    return senha

def criptografar_senha(senha, chave):
    f = Fernet(chave)
    senha_encriptada = f.encrypt(senha.encode())
    return senha_encriptada

def descriptografar_senha(senha_criptografada, chave):
    f = Fernet(chave)
    senha_descriptografada = f.decrypt(senha_criptografada).decode()
    return senha_descriptografada

def salvar_senha(senha_criptografada, descricao, arquivo):
    with open(arquivo, 'ab') as file:
        file.write(senha_criptografada + b' ' + descricao.encode() + b'\n')

def ler_senhas_criptografadas(arquivo):
    if not os.path.exists(arquivo):
        return []
    with open(arquivo, 'rb') as file:
        senhas_criptografadas = file.readlines()
    return senhas_criptografadas

def deletar_senha(linha, arquivo):
    with open(arquivo, 'rb') as file:
        linhas = file.readlines()
    with open(arquivo, 'wb') as file:
        for i, l in enumerate(linhas):
            if i != linha:
                file.write(l)

def editar_senha(linha, nova_senha_criptografada, nova_descricao, arquivo):
    with open(arquivo, 'rb') as file:
        linhas = file.readlines()
    with open(arquivo, 'wb') as file:
        for i, l in enumerate(linhas):
            if i == linha:
                file.write(nova_senha_criptografada + b' ' + nova_descricao.encode() + b'\n')
            else:
                file.write(l)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Senhas")
        self.geometry("600x400")

        self.tabControl = ttk.Notebook(self)
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab1, text='Gerar Senhas')
        self.tabControl.add(self.tab2, text='Senhas Salvas')

        self.tabControl.pack(expand=1, fill="both")

        self.create_widgets_tab1()

        self.inicializar_chave()

        self.create_widgets_tab2()
        
    def inicializar_chave(self):
        try:
            self.chave = carregar_chave()
        except FileNotFoundError:
            self.chave = gerar_chave()

    def create_widgets_tab1(self):
        self.label = tk.Label(self.tab1, text="Comprimento da Senha (2-128):")
        self.label.pack(pady=10)
        self.entry = tk.Entry(self.tab1)
        self.entry.pack(pady=10)
        self.entry.insert(0, "12")

        self.generate_button = tk.Button(self.tab1, text="Gerar Senha", command=self.gerar_senha_interface)
        self.generate_button.pack(pady=10)

        self.senha_text = tk.Text(self.tab1, height=5, width=50)
        self.senha_text.pack(pady=10)

    def create_widgets_tab2(self):
        self.tree = ttk.Treeview(self.tab2, columns=("Senha", "Descrição"), show='headings')
        self.tree.heading("Senha", text="Senha")
        self.tree.heading("Descrição", text="Descrição")
        self.tree.pack(expand=True, fill='both')

        self.refresh_button = tk.Button(self.tab2, text="Atualizar", command=self.atualizar_lista)
        self.refresh_button.pack(pady=10)

        self.copy_button = tk.Button(self.tab2, text="Copiar Senha", command=self.copiar_senha)
        self.copy_button.pack(pady=10)

        self.delete_button = tk.Button(self.tab2, text="Excluir", command=self.excluir_senha)
        self.delete_button.pack(pady=10)

        self.edit_button = tk.Button(self.tab2, text="Editar", command=self.editar_senha_interface)
        self.edit_button.pack(pady=10)

        self.atualizar_lista()

    def gerar_senha_interface(self):
        try:
            comprimento = int(self.entry.get())
            if comprimento < 2 or comprimento > 128:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor válido entre 2 e 128.")
            return

        senha = gerar_senha(comprimento)
        senha_criptografada = criptografar_senha(senha, self.chave)
        descricao = simpledialog.askstring("Descrição", "Insira a descrição da senha:")

        if descricao:
            salvar_senha(senha_criptografada, descricao, 'senhas_criptografadas.txt')
            self.senha_text.delete(1.0, tk.END)
            self.senha_text.insert(tk.END, f"Senha: {senha}\nDescrição: {descricao}")
            self.atualizar_lista()

    def atualizar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        senhas_criptografadas = ler_senhas_criptografadas('senhas_criptografadas.txt')
        for i, linha in enumerate(senhas_criptografadas):
            partes = linha.strip().split(b' ', 1)
            senha_criptografada = partes[0]
            descricao = partes[1].decode() if len(partes) > 1 else ""
            senha_descriptografada = descriptografar_senha(senha_criptografada, self.chave)
            self.tree.insert("", "end", iid=i, values=(senha_descriptografada, descricao))

    def copiar_senha(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showerror("Erro", "Por favor, selecione uma senha para copiar.")
            return

        item = selecionado[0]
        senha = self.tree.item(item, "values")[0]
        pyperclip.copy(senha)
        messagebox.showinfo("Sucesso", "Senha copiada para a área de transferência.")

    def excluir_senha(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showerror("Erro", "Por favor, selecione uma senha para excluir.")
            return

        for item in selecionado:
            linha = int(item)
            deletar_senha(linha, 'senhas_criptografadas.txt')

        self.atualizar_lista()

    def editar_senha_interface(self):
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showerror("Erro", "Por favor, selecione uma senha para editar.")
            return

        item = selecionado[0]
        linha = int(item)

        nova_senha = simpledialog.askstring("Nova Senha", "Insira a nova senha:")
        nova_descricao = simpledialog.askstring("Nova Descrição", "Insira a nova descrição:")

        if nova_senha and nova_descricao:
            nova_senha_criptografada = criptografar_senha(nova_senha, self.chave)
            editar_senha(linha, nova_senha_criptografada, nova_descricao, 'senhas_criptografadas.txt')
            self.atualizar_lista()

if __name__ == "__main__":
    app = App()
    app.mainloop()
