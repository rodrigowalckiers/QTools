import customtkinter as ctk
from tkinter import messagebox, filedialog, font

# ====================================================================================
# SISTEMA DE AUTENTICAÇÃO
# ====================================================================================
from core.SistemaAutenticacao import SistemaAutenticacao

# ====================================================================================
# INTERFACE GRÁFICA - TELA DE LOGIN
# ====================================================================================

class LoginView:
    """Tela de login"""
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = SistemaAutenticacao()
        
        self.root.title("QTools - Login")
        self.root.geometry("800x700")
        self.root.minsize(800, 700)
        self.root.resizable(True, True)
        self.centralizar_janela()
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.frame = ctk.CTkFrame(root, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.criar_interface()
    
    def centralizar_janela(self):
        """Centraliza janela"""
        self.root.update_idletasks()
        width, height = 800, 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def criar_interface(self):
        """Cria interface de login"""
        container = ctk.CTkFrame(self.frame, width=460, height=560, fg_color="#1f538d", corner_radius=15)
        container.pack(pady=20, padx=20, fill="both", expand=True)
        container.pack_propagate(False)
        
        ctk.CTkLabel(container, text="🏭", font=ctk.CTkFont(size=80), text_color="white").pack(pady=(40, 10))
        ctk.CTkLabel(container, text="QTools - Sistema de Qualidade e Gestão", 
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="white", justify="center").pack(pady=(0, 40))
        
        form_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        form_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(form_frame, text="👤 Usuário", font=ctk.CTkFont(size=14, weight="bold"), text_color="#333333").pack(pady=(30, 5))
        self.entry_usuario = ctk.CTkEntry(form_frame, width=300, height=45, placeholder_text="Digite seu usuário", font=ctk.CTkFont(size=14), corner_radius=8)
        self.entry_usuario.pack(pady=5)
        self.entry_usuario.focus()
        
        ctk.CTkLabel(form_frame, text="🔒 Senha", font=ctk.CTkFont(size=14, weight="bold"), text_color="#333333").pack(pady=(20, 5))
        self.entry_senha = ctk.CTkEntry(form_frame, width=300, height=45, placeholder_text="Digite sua senha", show="●", font=ctk.CTkFont(size=14), corner_radius=8)
        self.entry_senha.pack(pady=5)
        self.entry_senha.bind('<Return>', lambda e: self.fazer_login())
        
        ctk.CTkButton(form_frame, text="Entrar no Sistema", width=300, height=45, font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.fazer_login, fg_color="#1f538d", text_color="white", hover_color="#164276", corner_radius=8).pack(pady=30)
        
        # ctk.CTkLabel(form_frame, text="Usuário padrão: admin\nSenha: admin", font=ctk.CTkFont(size=12), 
        #              text_color="#666666", justify="center").pack(pady=(10, 20))
        
        ctk.CTkLabel(container, text="QTools - Sistema de Qualidade e Gestão v0.1.5", font=ctk.CTkFont(size=10), text_color="#e0e0e0").pack(pady=10)
    
    def fazer_login(self):
        """Processa login"""
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()
        
        if not usuario or not senha:
            messagebox.showerror("Erro", "Preencha usuário e senha!")
            return
        
        sucesso, info_usuario = self.auth.autenticar(usuario, senha)
        
        if sucesso and info_usuario:
            self.frame.destroy()
            self.on_login_success(usuario, info_usuario)
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")
            self.entry_senha.delete(0, 'end')
            self.entry_senha.focus()