from tkinter import messagebox, filedialog, font
from typing import List, Dict, Optional, Tuple
import customtkinter as ctk

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================
from core.ConfiguracaoSistema import ConfiguracaoSistema

# ====================================================================================
# INTERFACE GRÁFICA - TELA DE LOGIN
# ====================================================================================
from view.LoginView import LoginView

# ====================================================================================
# INTERFACE GRÁFICA - TELA INICIAL
# ====================================================================================
from view.HomeView import HomeView

# ====================================================================================
# APLICAÇÃO PRINCIPAL
# ====================================================================================

class Aplicacao:
    """Aplicação principal"""
    
    def __init__(self):
        if not ConfiguracaoSistema.criar_estrutura_pastas():
            messagebox.showerror("Erro", "Não foi possível criar estrutura de pastas!")
            return
        
        self.root = ctk.CTk()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        LoginView(self.root, self.on_login_success)
    
    def on_login_success(self, usuario: str, info_usuario: Dict):
        """Callback após login"""
        HomeView(self.root, usuario, info_usuario)
    
    def executar(self):
        """Executa aplicação"""
        self.root.mainloop()