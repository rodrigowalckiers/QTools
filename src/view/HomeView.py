from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, filedialog, font
from typing import List, Dict, Optional, Tuple
from widgets.DatePicker import DatePicker

# ====================================================================================
# INTERFACE GRÁFICA - TELA DE LOGIN
# ====================================================================================
from view.LoginView import LoginView

# ====================================================================================
# HELPERS: PERMISSÕES E DEMAIS FUNÇÕES AUXILIARES
# ====================================================================================
from utils import helpers

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================
from core.ConfiguracaoSistema import ConfiguracaoSistema

# ====================================================================================
# SISTEMA DE AUTENTICAÇÃO
# ====================================================================================
from core.SistemaAutenticacao import SistemaAutenticacao

# ====================================================================================
# BANCO DE DADOS
# ====================================================================================
from core.BancoDados import BancoDados

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================
from core.Relatorios import Relatorios

# ====================================================================================
# PEÇA CONTROLLER
# ====================================================================================
from controller.PecaController import PecaController

# ====================================================================================
# INTERFACE GRÁFICA - TELA INICIAL
# ====================================================================================

class HomeView:
    """Tela inicial do sistema"""
    
    def __init__(self, root, usuario: str, info_usuario: Dict):
        self.root = root
        self.usuario = usuario
        self.info_usuario = info_usuario
        self.db = BancoDados()
        self.auth = SistemaAutenticacao()
        
        self.root.title(f"QTools Sistema de Qualidade e Gestão - {info_usuario['nome_completo']}")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 700)
        self.root.resizable(True, True)
        self.centralizar_janela()
        
        # Timeout de sessão
        self.ultima_atividade = datetime.now()
        self.verificar_timeout()
        
        self.frame_principal = ctk.CTkFrame(root, fg_color="transparent")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.criar_menu_principal()
    
    def centralizar_janela(self):
        """Centraliza janela"""
        self.root.update_idletasks()
        width, height = 1200, 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def verificar_timeout(self):
        """Verifica timeout de sessão"""
        timeout_minutos = self.db.config.get('timeout_sessao_minutos', 30)
        tempo_inativo = (datetime.now() - self.ultima_atividade).total_seconds() / 60
        
        if tempo_inativo > timeout_minutos:
            messagebox.showwarning("Sessão Expirada", "Sua sessão expirou por inatividade.")
            self.fazer_logout()
        else:
            self.root.after(60000, self.verificar_timeout)
    
    def resetar_timeout(self):
        """Reseta contador de inatividade"""
        self.ultima_atividade = datetime.now()
    
    def fazer_logout(self):
        """Faz logout do usuário"""
        resposta = messagebox.askyesno("Sair", "Deseja realmente sair do sistema?")
        if resposta:
            ConfiguracaoSistema.registrar_auditoria(self.usuario, "LOGOUT", "Logout manual")
            for widget in self.root.winfo_children():
                widget.destroy()
            LoginView(self.root, lambda u, i: HomeView(self.root, u, i))
    
    def criar_menu_principal(self):
        """Cria menu principal"""
        self.resetar_timeout()
        self.limpar_tela()
        
        # Header
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=80, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        titulo_frame = ctk.CTkFrame(header, fg_color="transparent")
        titulo_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(titulo_frame, text="🏭 QTools - Sistema de Qualidade e Gestão", 
                     font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(titulo_frame, text="QTools - Versão 0.1.5", 
                     font=ctk.CTkFont(size=12), text_color="#e0e0e0").pack(anchor="w")
        
        # Botão SAIR
        logout_frame = ctk.CTkFrame(header, fg_color="transparent")
        logout_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkButton(
            logout_frame, 
            text="🚪 Sair", 
            width=100, 
            height=50, 
            command=self.fazer_logout,
            font=ctk.CTkFont(size=14, weight="bold"), 
            fg_color="#c0392b"
        ).pack(side="right", padx=20, pady=10)
        
        # Info usuário 
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkLabel(user_frame, text=f"👤 {self.info_usuario['nome_completo']}", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="white", justify="right").pack(anchor="e")
        ctk.CTkLabel(user_frame, text=f"📋 {self.info_usuario['nivel'].title()} | Turno: {self.obter_turno_atual()}", 
                     font=ctk.CTkFont(size=10), text_color="#e0e0e0", justify="right").pack(anchor="e")
        
        # Dashboard
        self.criar_dashboard()
        
        # Menu de opções com SCROLL
        self.criar_menu_opcoes_scroll()
    
    def obter_turno_atual(self) -> str:
        """Determina turno"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def criar_dashboard(self):
        """Cria dashboard"""
        dash_frame = ctk.CTkFrame(self.frame_principal, height=120)
        dash_frame.pack(fill="x", padx=10, pady=10)
        dash_frame.pack_propagate(False)
        
        total_pecas = len(self.db.pecas_aprovadas) + len(self.db.pecas_reprovadas)
        taxa_aprov = (len(self.db.pecas_aprovadas)/total_pecas*100 if total_pecas > 0 else 0)
        meta = self.db.config.get('metas', {}).get('diaria', 500)
        prog_meta = (len(self.db.pecas_aprovadas)/meta*100 if meta > 0 else 0)
        
        metrics = [
            ("✅ Peças Aprovadas", len(self.db.pecas_aprovadas), "#2ecc71"),
            ("❌ Peças Reprovadas", len(self.db.pecas_reprovadas), "#e74c3c"),
            ("📦 Caixas Completas", len(self.db.caixas_fechadas), "#3498db"),
            ("📊 Taxa de Aprovação", f"{taxa_aprov:.1f}%", "#9b59b6"),
            ("🎯 Meta", f"{prog_meta:.1f}%", "#f39c12"),
            ("🔧 Caixa Atual", f"#{self.db.caixa_atual.numero} ({len(self.db.caixa_atual.pecas)}/{self.db.caixa_atual.capacidade})", "#1abc9c")
        ]
        
        for i, (titulo, valor, cor) in enumerate(metrics):
            card = ctk.CTkFrame(dash_frame, fg_color=cor, height=100, corner_radius=10)
            card.grid(row=0, column=i, padx=5, pady=10, sticky="nsew")
            dash_frame.columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=(15, 5))
            ctk.CTkLabel(card, text=str(valor), font=ctk.CTkFont(size=24, weight="bold"), text_color="white").pack(pady=(5, 15))
    
    def criar_menu_opcoes_scroll(self):
        """Cria menu de opções com scroll"""
        self.resetar_timeout()
        
        # Frame principal com scroll
        main_scroll_frame = ctk.CTkScrollableFrame(self.frame_principal, height=400)
        main_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(main_scroll_frame, text="Menu Principal - Escolha uma operação:", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        nivel = self.info_usuario.get('nivel', 'operador')
        
        # ========== MENU PRINCIPAL - ORDEM EXATA ==========
        
        # Opções para TODOS (Operador+)
        opcoes_todos = [
            ("📝 Cadastrar Nova Peça", self.tela_cadastrar_peca, "#1f538d"),
            ("📋 Listar Peças", self.tela_listar_pecas, "#2980b9"),
        ]
        
        for texto, comando, cor in opcoes_todos:
            btn = ctk.CTkButton(main_scroll_frame, text=texto, width=400, height=45, 
                               font=ctk.CTkFont(size=13, weight="bold"), command=comando, 
                               fg_color=cor, hover_color=self.escurecer_cor(cor), corner_radius=8)
            btn.pack(pady=6)
        
        # Opção Remover Peça (Supervisor+)
        if nivel in ['supervisor', 'administrador']:
            btn_remover = ctk.CTkButton(main_scroll_frame, text="🗑️ Remover Peça", width=400, height=45, 
                                       font=ctk.CTkFont(size=13, weight="bold"), command=self.tela_remover_peca, 
                                       fg_color="#e67e22", hover_color="#d35400", corner_radius=8)
            btn_remover.pack(pady=6)
        
        # Opção Ver Caixas (Todos)
        btn_caixas = ctk.CTkButton(main_scroll_frame, text="📦 Ver Caixas", width=400, height=45, 
                                  font=ctk.CTkFont(size=13, weight="bold"), command=self.tela_listar_caixas, 
                                  fg_color="#27ae60", hover_color="#229954", corner_radius=8)
        btn_caixas.pack(pady=6)
        
        # ========== MENU ADMINISTRATIVO - APENAS ADMIN ==========
        
        if nivel == 'administrador':
            # Separador
            ctk.CTkLabel(main_scroll_frame, text="Relatório e Ferramentas Administrativas", 
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 15))
            
            # NOVA OPÇÃO: Gerenciar Peças (CRUD)
            btn_gerenciar = ctk.CTkButton(main_scroll_frame, text="🔧 Gerenciar Peças (CRUD)", width=400, height=45, 
                                         font=ctk.CTkFont(size=13, weight="bold"), command=self.tela_gerenciar_pecas,
                                         fg_color="#8e44ad", hover_color="#7d3c98", corner_radius=8)
            btn_gerenciar.pack(pady=6)
            
            # Opções administrativas existentes
            opcoes_admin = [
                ("📊 Relatórios Avançados", self.tela_relatorios_avancados, "#8e44ad"),
                ("👥 Gestão de Usuários", self.tela_gestao_usuarios, "#c0392b"),
                ("⚙️ Configurações", self.tela_configuracoes, "#34495e"),
            ]
            
            for texto, comando, cor in opcoes_admin:
                btn = ctk.CTkButton(main_scroll_frame, text=texto, width=400, height=45, 
                                   font=ctk.CTkFont(size=13, weight="bold"), command=comando, 
                                   fg_color=cor, hover_color=self.escurecer_cor(cor), corner_radius=8)
                btn.pack(pady=6)
    
    def escurecer_cor(self, cor: str) -> str:
        """Escurece cor hex"""
        try:
            cor = cor.lstrip('#')
            if len(cor) == 6:
                r, g, b = int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)
                r, g, b = max(0, r-30), max(0, g-30), max(0, b-30)
                return f'#{r:02x}{g:02x}{b:02x}'
        except:
            pass
        return cor
    
    # ========== TELAS IMPLEMENTADAS ==========
    
    def tela_cadastrar_peca(self):
        """Tela de cadastro de peça"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📝 Cadastrar Nova Peça")
        
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="Preencha os dados da peça:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        campos_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        campos_frame.pack(pady=20, padx=50, fill="both", expand=True)
        
        criterios = self.db.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
        
        # ID da Peça
        ctk.CTkLabel(campos_frame, text="🔢 ID da Peça:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_id = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text="Ex: PECA001")
        entry_id.pack(fill="x", pady=5)
        entry_id.focus()
        
        # Peso
        ctk.CTkLabel(campos_frame, text=f"⚖️ Peso (g): {criterios['peso_min']}g a {criterios['peso_max']}g", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_peso = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text=f"Ex: 100.0")
        entry_peso.pack(fill="x", pady=5)
        
        # Cor
        ctk.CTkLabel(campos_frame, text=f"🎨 Cor - Aprovadas: {', '.join(criterios['cores_aceitas'])}", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        combo_cor = ctk.CTkComboBox(campos_frame, width=400, height=45,
                                   values=["azul", "verde", "vermelho", "amarelo", "preto", "branco"])
        combo_cor.set("azul")
        combo_cor.pack(fill="x", pady=5)
        
        # Comprimento
        ctk.CTkLabel(campos_frame, text=f"📏 Comprimento (cm): {criterios['comprimento_min']}cm a {criterios['comprimento_max']}cm", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        entry_comp = ctk.CTkEntry(campos_frame, width=400, height=45, placeholder_text=f"Ex: 15.0")
        entry_comp.pack(fill="x", pady=5)
        
        def cadastrar():
            try:
                id_peca = entry_id.get().strip()
                peso_str = entry_peso.get().strip()
                cor = combo_cor.get().strip()
                comp_str = entry_comp.get().strip()
                
                if not id_peca:
                    messagebox.showerror("Erro", "ID da peça é obrigatório!")
                    return
                
                if not peso_str or not comp_str:
                    messagebox.showerror("Erro", "Peso e comprimento são obrigatórios!")
                    return
                
                peso = float(peso_str.replace(',', '.'))
                comprimento = float(comp_str.replace(',', '.'))
                
                peca = PecaController(id_peca, peso, cor, comprimento, self.usuario)
                sucesso, mensagem = self.db.adicionar_peca(peca)
                
                if sucesso:
                    if peca.aprovada:
                        messagebox.showinfo("✅ Peça Aprovada!", 
                            f"Peça {id_peca} APROVADA!\n\n"
                            f"• Caixa #{self.db.caixa_atual.numero}\n"
                            f"• Vagas: {self.db.caixa_atual.vagas_disponiveis()}\n"
                            f"• Turno: {peca.turno}")
                    else:
                        motivos = "\n".join([f"• {m}" for m in peca.motivos_reprovacao])
                        messagebox.showwarning("❌ Peça Reprovada", 
                            f"Peça {id_peca} REPROVADA!\n\nMotivos:\n{motivos}")
                    
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
                    
            except ValueError:
                messagebox.showerror("Erro", "Peso e comprimento devem ser números!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {str(e)}")
        
        btn_frame = ctk.CTkFrame(campos_frame, fg_color="transparent")
        btn_frame.pack(pady=40)
        
        ctk.CTkButton(btn_frame, text="✅ Cadastrar", width=200, height=50, command=cadastrar,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#2ecc71").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=200, height=50, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=10)
    
    def tela_listar_pecas(self):
        """Tela de listagem"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📋 Listar Peças")
        
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Comprimento
        filtro_frame = ctk.CTkFrame(main_frame, width=500, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=10, pady=10)
        
        comp_col1 = ctk.CTkFrame(filtro_frame, fg_color="transparent")
        comp_col1.pack(fill="both")
        
        ctk.CTkLabel(comp_col1, text="📅 Data Início:").pack(side="left", padx=(0, 10))
        self.entry_data_min = DatePicker(comp_col1, width=140, height=25)
        self.entry_data_min.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(comp_col1, text="📅 Data Fim:").pack(side="left", padx=(0, 10))
        self.entry_data_max = DatePicker(comp_col1, width=140, height=25)
        self.entry_data_max.pack(side="left")
        
        #Em desenvolvimento
        def aplicar_filtro():
            # self.resetar_timeout()
            # dt = self.entry_data_min.get_date()
            # dt2 = self.entry_data_max.get_date()
            # data_inicio = datetime.date(dt)
            # data_fim = datetime.date(dt2)
            # periodo = combo_periodo.get()
            # atualizar_listas(data_inicio, data_fim)
            messagebox.showwarning("EM BREVE", "Recurso em desenvolvimento")
            
        ctk.CTkButton(comp_col1, text="🔍 Filtrar", width=100, command=aplicar_filtro, fg_color="#3498db").pack(side="left", padx=5)
        
        # Tabs
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_aprovadas = tabview.add("✅ Aprovadas")
        tab_reprovadas = tabview.add("❌ Reprovadas")
        
        def atualizar_listas(data_inicio=None, data_fim=None):
            for widget in tab_aprovadas.winfo_children():
                widget.destroy()
            for widget in tab_reprovadas.winfo_children():
                widget.destroy()
            
            aprovadas = self.db.filtrar_pecas_por_data(self.db.pecas_aprovadas, data_inicio, data_fim)
            reprovadas = self.db.filtrar_pecas_por_data(self.db.pecas_reprovadas, data_inicio, data_fim)
            
            self.criar_lista_pecas(tab_aprovadas, aprovadas, "aprovadas")
            self.criar_lista_pecas(tab_reprovadas, reprovadas, "reprovadas")
        
        atualizar_listas()
        
        ctk.CTkButton(main_frame, text="🔙 Voltar", width=200, height=45, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(pady=10)
    
    def criar_lista_pecas(self, parent, pecas: List[PecaController], tipo: str):
        """Cria lista de peças com botão de remoção"""
        self.resetar_timeout()
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        if not pecas:
            ctk.CTkLabel(frame, text=f"Nenhuma peça {tipo}.", font=ctk.CTkFont(size=14), text_color="#666666").pack(pady=50)
            return
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(frame, fg_color="#34495e")
        header_frame.pack(fill="x", pady=(0, 10))
        
        headers = ["ID", "Peso", "Cor", "Comp.", "Turno", "Inspetor", "Data"]
        
        # Adicionar coluna de ação se for admin/supervisor
        if self.info_usuario.get('nivel') in ['administrador', 'supervisor']:
            headers.append("Ação")
        
        for i, header in enumerate(headers):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=12, weight="bold"), text_color="white").grid(
                row=0, column=i, padx=10, pady=8, sticky="w")
            header_frame.columnconfigure(i, weight=1)
        
        # Linhas
        for idx, peca in enumerate(pecas[-100:], 1):
            row_frame = ctk.CTkFrame(frame, fg_color="#f8f9fa" if idx % 2 == 0 else "white")
            row_frame.pack(fill="x", pady=2)
            
            dados = [
                peca.id_peca,
                f"{peca.peso}g",
                peca.cor.title(),
                f"{peca.comprimento}cm",
                peca.turno,
                peca.usuario,
                peca.timestamp[:16]
            ]
            
            for i, dado in enumerate(dados):
                ctk.CTkLabel(row_frame, text=dado, font=ctk.CTkFont(size=11), text_color="#2c3e50").grid(
                    row=0, column=i, padx=10, pady=6, sticky="w")
                row_frame.columnconfigure(i, weight=1)
            
            # Botão remover (apenas admin)
            if self.info_usuario.get('nivel') in ['administrador', 'supervisor']:
                btn_remover = ctk.CTkButton(row_frame, text="❌ Excluir", width=80, height=30, 
                                           command=lambda p=peca: self.remover_peca_rapido(p.id_peca),
                                           fg_color="#e74c3c", hover_color="#c0392b")
                btn_remover.grid(row=0, column=len(dados), padx=10, pady=6)
    
    def remover_peca_rapido(self, id_peca: str):
        """Remove peça com confirmação"""
        self.resetar_timeout()
        
        # Buscar peça
        peca = None
        for p in self.db.pecas_aprovadas + self.db.pecas_reprovadas:
            if p.id_peca == id_peca:
                peca = p
                break
        
        if not peca:
            messagebox.showerror("Erro", "Peça não encontrada!")
            return
        
        # Diálogo de confirmação
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("⚠️ Confirmar Remoção")
        dialog.geometry("1200x800")
        dialog.minsize(1000, 700)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="⚠️ CONFIRMAR REMOÇÃO", font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#e74c3c").pack(pady=20)
        
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_text = f"""
Peça: {peca.id_peca}
Peso: {peca.peso}g | Cor: {peca.cor} | Comprimento: {peca.comprimento}cm
Status: {'APROVADA' if peca.aprovada else 'REPROVADA'}
Inspetor: {peca.usuario}
Data: {peca.timestamp}

⚠️ Esta ação não pode ser desfeita!
        """
        
        ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=12), justify="left").pack(pady=10)
        
        ctk.CTkLabel(dialog, text="Justificativa (opcional):", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20, 5))
        entry_justificativa = ctk.CTkTextbox(dialog, width=450, height=80)
        entry_justificativa.pack(padx=20, pady=5)
        
        def confirmar():
            justificativa = entry_justificativa.get("1.0", "end-1c").strip()
            sucesso, msg = self.db.remover_peca(id_peca, self.usuario, justificativa)
            
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                dialog.destroy()
                self.tela_listar_pecas()
            else:
                messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=150, height=40, command=dialog.destroy,
                     fg_color="#95a5a6", hover_color="#7f8c8d").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ Confirmar", width=150, height=40, command=confirmar,
                     fg_color="#e74c3c", hover_color="#c0392b").pack(side="left", padx=10)
    
    helpers.requer_permissao('supervisor')
    def tela_remover_peca(self):
        """Tela de remoção de peça"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("🗑️ Remover Peça")
        
        form_frame = ctk.CTkFrame(self.frame_principal)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="Digite o ID da peça a ser removida:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=30)
        
        entry_id = ctk.CTkEntry(form_frame, width=400, height=50, placeholder_text="Ex: PECA001")
        entry_id.pack(pady=10)
        entry_id.focus()
        
        ctk.CTkLabel(form_frame, text="Justificativa (opcional):", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5))
        entry_justificativa = ctk.CTkTextbox(form_frame, width=400, height=80)
        entry_justificativa.pack(pady=5)
        
        def remover():
            id_peca = entry_id.get().strip().upper()
            if not id_peca:
                messagebox.showerror("Erro", "Digite um ID!")
                return
            
            justificativa = entry_justificativa.get("1.0", "end-1c").strip()
            justificativa = justificativa or "Remoção manual"
            
            resposta = messagebox.askyesno("Confirmar", f"Remover peça {id_peca}?\n\nEsta ação não pode ser desfeita!")
            
            if resposta:
                sucesso, mensagem = self.db.remover_peca(id_peca, self.usuario, justificativa)
                if sucesso:
                    messagebox.showinfo("Sucesso", mensagem)
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(btn_frame, text="🗑️ Remover", width=200, height=50, command=remover,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#e74c3c").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", width=200, height=50, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=14, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=10)
    
    def tela_listar_caixas(self):
        """Tela de listagem de caixas"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📦 Ver Caixas")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Caixa atual
        ctk.CTkLabel(content_frame, text="📦 Caixa Atual:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        info_frame = ctk.CTkFrame(content_frame, fg_color="#3498db", height=120, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=10)
        info_frame.pack_propagate(False)
        
        ctk.CTkLabel(info_frame, text=f"Caixa #{self.db.caixa_atual.numero}", 
                    font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(pady=5)
        
        progresso = (len(self.db.caixa_atual.pecas) / self.db.caixa_atual.capacidade) * 100
        ctk.CTkLabel(info_frame, text=f"{len(self.db.caixa_atual.pecas)}/{self.db.caixa_atual.capacidade} peças ({progresso:.1f}%)",
                    font=ctk.CTkFont(size=14), text_color="white").pack(pady=2)
        ctk.CTkLabel(info_frame, text=f"Vagas: {self.db.caixa_atual.vagas_disponiveis()}",
                    font=ctk.CTkFont(size=12), text_color="#e0e0e0").pack(pady=2)
        
        # Caixas fechadas
        ctk.CTkLabel(content_frame, text="📦 Caixas Fechadas:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        if not self.db.caixas_fechadas:
            ctk.CTkLabel(content_frame, text="Nenhuma caixa fechada.", 
                        font=ctk.CTkFont(size=14), text_color="#666666").pack(pady=50)
        else:
            scroll_frame = ctk.CTkScrollableFrame(content_frame, height=300)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            for caixa in reversed(self.db.caixas_fechadas[-20:]):
                caixa_frame = ctk.CTkFrame(scroll_frame, fg_color="#ecf0f1")
                caixa_frame.pack(fill="x", pady=5, padx=5)
                
                header_caixa = ctk.CTkFrame(caixa_frame, fg_color="#34495e")
                header_caixa.pack(fill="x", padx=2, pady=2)
                
                ctk.CTkLabel(header_caixa, text=f"📦 Caixa #{caixa.numero} - {len(caixa.pecas)} peças - {caixa.data_fechamento}",
                            font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=8, padx=10, anchor="w")
        
        ctk.CTkButton(content_frame, text="🔙 Voltar", width=200, height=45, 
                     command=self.criar_menu_principal, fg_color="#95a5a6").pack(pady=20)
    
    helpers.requer_permissao('administrador')
    def tela_gerenciar_pecas(self):
        """Gerenciamento CRUD de peças"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("🔧 Gerenciar Peças (CRUD)")
        
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de busca
        busca_frame = ctk.CTkFrame(main_frame)
        busca_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(busca_frame, text="🔍 Buscar Peça por ID:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        
        entry_busca = ctk.CTkEntry(busca_frame, width=200, height=35, placeholder_text="Digite o ID da peça")
        entry_busca.pack(side="left", padx=10)
        entry_busca.focus()
        
        def buscar_peca():
            id_peca = entry_busca.get().strip()
            if not id_peca:
                messagebox.showerror("Erro", "Digite um ID para buscar!")
                return
            
            peca = self.db.buscar_peca_por_id(id_peca)
            if peca:
                self.mostrar_formulario_edicao(peca, form_frame)
            else:
                for widget in form_frame.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(form_frame, text=f"Peça {id_peca} não encontrada!", 
                           font=ctk.CTkFont(size=14), text_color="#e74c3c").pack(pady=50)
        
        btn_buscar = ctk.CTkButton(busca_frame, text="Buscar", width=100, height=35, command=buscar_peca)
        btn_buscar.pack(side="left", padx=10)
        
        # Frame do formulário
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(form_frame, text="Digite um ID de peça para editar ou excluir", 
                     font=ctk.CTkFont(size=14), text_color="#666666").pack(pady=50)
        
        ctk.CTkButton(main_frame, text="🔙 Voltar", width=200, height=45, 
                     command=self.criar_menu_principal, fg_color="#95a5a6").pack(pady=10)
    
    def mostrar_formulario_edicao(self, peca: PecaController, form_frame: ctk.CTkFrame):
        """Mostra formulário para edição de peça"""
        for widget in form_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(form_frame, text=f"Editando Peça: {peca.id_peca}", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        status = "✅ APROVADA" if peca.aprovada else "❌ REPROVADA"
        ctk.CTkLabel(form_frame, text=f"Status: {status}", 
                     font=ctk.CTkFont(size=14), 
                     text_color="#2ecc71" if peca.aprovada else "#e74c3c").pack(pady=5)
        
        campos_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        campos_frame.pack(pady=20, padx=50, fill="both", expand=True)
        
        # Peso
        ctk.CTkLabel(campos_frame, text="Peso (g):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_peso = ctk.CTkEntry(campos_frame, width=300, height=40)
        entry_peso.insert(0, str(peca.peso))
        entry_peso.pack(fill="x", pady=5)
        
        # Cor
        ctk.CTkLabel(campos_frame, text="Cor:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        combo_cor = ctk.CTkComboBox(campos_frame, width=300, height=40,
                                   values=["azul", "verde", "vermelho", "amarelo", "preto", "branco"])
        combo_cor.set(peca.cor)
        combo_cor.pack(fill="x", pady=5)
        
        # Comprimento
        ctk.CTkLabel(campos_frame, text="Comprimento (cm):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        entry_comp = ctk.CTkEntry(campos_frame, width=300, height=40)
        entry_comp.insert(0, str(peca.comprimento))
        entry_comp.pack(fill="x", pady=5)
        
        btn_frame = ctk.CTkFrame(campos_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        def salvar_edicao():
            try:
                novo_peso = float(entry_peso.get().replace(',', '.'))
                nova_cor = combo_cor.get()
                novo_comp = float(entry_comp.get().replace(',', '.'))
                
                sucesso, mensagem = self.db.editar_peca(peca.id_peca, novo_peso, nova_cor, novo_comp, self.usuario)
                
                if sucesso:
                    messagebox.showinfo("Sucesso", mensagem)
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
                    
            except ValueError:
                messagebox.showerror("Erro", "Peso e comprimento devem ser números válidos!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
        
        def excluir_peca():
            resposta = messagebox.askyesno("Confirmar", f"Excluir peça {peca.id_peca}?\n\nEsta ação não pode ser desfeita!")
            
            if resposta:
                sucesso, mensagem = self.db.remover_peca(peca.id_peca, self.usuario, "Excluído via CRUD")
                if sucesso:
                    messagebox.showinfo("Sucesso", mensagem)
                    self.criar_menu_principal()
                else:
                    messagebox.showerror("Erro", mensagem)
        
        ctk.CTkButton(btn_frame, text="💾 Salvar", width=180, height=45, command=salvar_edicao,
                     font=ctk.CTkFont(size=13, weight="bold"), fg_color="#2ecc71").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Excluir", width=180, height=45, command=excluir_peca,
                     font=ctk.CTkFont(size=13, weight="bold"), fg_color="#e74c3c").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔙 Cancelar", width=180, height=45, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=13, weight="bold"), fg_color="#95a5a6").pack(side="left", padx=5)
    
    helpers.requer_permissao('administrador')
    def tela_relatorios_avancados(self):
        """Tela de relatórios avançados"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📊 Relatórios Avançados")
        
        main_frame = ctk.CTkScrollableFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_diario = tabview.add("📅 Diário")
        tab_usuario = tabview.add("👤 Por Usuário")
        tab_combinado = tabview.add("🔗 Combinado")
        
        self.criar_aba_relatorio_diario(tab_diario)
        self.criar_aba_relatorio_usuario(tab_usuario)
        self.criar_aba_relatorio_combinado(tab_combinado)
    
    def criar_aba_relatorio_diario(self, parent):
        def gerar_relatorio():
            data = date_picker.get_date()
            if not data:
                messagebox.showerror("Erro", "Selecione uma data!")
                return
            
            try:
                datetime.date(data)
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido! Use AAAA-MM-DD")
                return
            
            relatorio = self.db.gerar_relatorio_diario(data)
            self.mostrar_relatorio(relatorio, resultado_frame)
            
        """Cria aba de relatório diário com Date Picker"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Relatório Diário de Produção", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        data_frame = ctk.CTkFrame(frame, fg_color="transparent")
        data_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(data_frame, text="Selecione a data:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        
        # Usar DatePicker customizado
        date_picker = DatePicker(data_frame)
        date_picker.pack(anchor="w", pady=10)
        date_picker.set_date(datetime.now())  # Data padrão: hoje
        
        ctk.CTkButton(data_frame, text="📊 Gerar Relatório", width=200, height=45, 
                    command=gerar_relatorio, font=ctk.CTkFont(size=13, weight="bold"),
                    fg_color="#3498db").pack(pady=20)
        
        resultado_frame = ctk.CTkFrame(frame)
        resultado_frame.pack(fill="both", expand=True, pady=20)
    
    def criar_aba_relatorio_usuario(self, parent):
        def gerar_relatorio():
            usuario = combo_usuario.get()
            if not usuario:
                messagebox.showerror("Erro", "Selecione um usuário!")
                return
            
            relatorio = self.db.gerar_relatorio_usuario(usuario)
            self.mostrar_relatorio(relatorio, resultado_frame)
            
        """Cria aba de relatório por usuário"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Relatório por Usuário", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        usuario_frame = ctk.CTkFrame(frame, fg_color="transparent")
        usuario_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(usuario_frame, text="Selecione o usuário:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        
        usuarios = self.auth.listar_usuarios()
        nomes_usuarios = [u['usuario'] for u in usuarios]
        
        combo_usuario = ctk.CTkComboBox(usuario_frame, width=300, height=40, values=nomes_usuarios)
        if nomes_usuarios:
            combo_usuario.set(nomes_usuarios[0])
        combo_usuario.pack(anchor="w", pady=10)
        
        ctk.CTkButton(frame, text="👤 Gerar Relatório", width=200, height=45, 
                     command=gerar_relatorio, font=ctk.CTkFont(size=13, weight="bold"),
                     fg_color="#9b59b6").pack(pady=20)
        
        resultado_frame = ctk.CTkFrame(frame)
        resultado_frame.pack(fill="both", expand=True, pady=25)
    
    def criar_aba_relatorio_combinado(self, parent):
        def gerar_relatorio():
            data = date_picker.get_date()
            usuario = combo_usuario.get()
            
            if not data or not usuario:
                messagebox.showerror("Erro", "Preencha data e usuário!")
                return
            
            try:
                datetime.date(data)
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido! Use AAAA-MM-DD")
                return
            
            relatorio = self.db.gerar_relatorio_diario_usuario(data, usuario)
            self.mostrar_relatorio(relatorio, resultado_frame)
        
        """Cria aba de relatório combinado"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Relatório Dia + Usuário", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,10))
        
        filtros_frame = ctk.CTkFrame(frame, fg_color="transparent")
        filtros_frame.pack(fill="x")
        
        ctk.CTkLabel(filtros_frame, text="Selecione a Data:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", anchor="w", fill="x", padx=(0, 10))
        date_picker = DatePicker(filtros_frame, width=80, height=32)
        date_picker.pack(side="left", fill="x", expand=True, padx=(0, 10))
        date_picker.set_date(datetime.now())  # Data padrão: hoje
                
        ctk.CTkLabel(filtros_frame, text="Usuário:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left",anchor="w", fill="x", padx=(0, 10))
        usuarios = self.auth.listar_usuarios()
        nomes_usuarios = [u['usuario'] for u in usuarios]
        combo_usuario = ctk.CTkComboBox(filtros_frame, width=140, height=40, values=nomes_usuarios)
        if nomes_usuarios:
            combo_usuario.set(nomes_usuarios[0])
        combo_usuario.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(frame, text="🔗 Gerar Relatório", width=200, height=45, 
                     command=gerar_relatorio, font=ctk.CTkFont(size=13, weight="bold"),
                     fg_color="#e67e22").pack(pady=30)
        
        resultado_frame = ctk.CTkFrame(frame)
        resultado_frame.pack(fill="both", expand=True, pady=20)
    
    def mostrar_relatorio(self, relatorio: Dict, parent: ctk.CTkFrame):
        """Mostra relatório na interface"""
        for widget in parent.winfo_children():
            widget.destroy()
        
        text_frame = ctk.CTkFrame(parent)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_relatorio = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(size=11))
        text_relatorio.pack(fill="both", expand=True, padx=10, pady=10)
        
        relatorio_formatado = self.formatar_relatorio(relatorio)
        text_relatorio.insert("1.0", relatorio_formatado)
        text_relatorio.configure(state="disabled")
        
        btn_export_frame = ctk.CTkFrame(parent)
        btn_export_frame.pack(pady=10)
        
        def exportar_pdf():
            caminho = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if caminho:
                sucesso, msg = Relatorios.gerar_relatorio_pdf(relatorio, caminho, self.usuario)
                if sucesso:
                    messagebox.showinfo("Sucesso", f"Relatório PDF gerado:\n{caminho}")
                else:
                    messagebox.showerror("Erro", msg)
        
        ctk.CTkButton(btn_export_frame, text="📄 Exportar PDF", width=150, height=40, command=exportar_pdf,
                     font=ctk.CTkFont(size=12), fg_color="#e74c3c").pack(side="left", padx=5)
    
    def formatar_relatorio(self, relatorio: Dict) -> str:
        """Formata relatório para exibição"""
        texto = "="*80 + "\n"
        texto += f"           {relatorio['titulo']}\n"
        texto += "="*80 + "\n\n"
        
        texto += f"📅 Data de Geração: {relatorio['data_geracao']}\n"
        texto += f"👤 Gerado por: {self.info_usuario['nome_completo']}\n\n"
        
        texto += "📈 RESUMO ESTATÍSTICO\n"
        texto += "-"*80 + "\n"
        texto += f"• Total de Peças Inspecionadas: {relatorio['total_pecas_inspecionadas']:,}\n"
        texto += f"• ✅ Aprovadas: {relatorio['total_pecas_aprovadas']:,}\n"
        texto += f"• ❌ Reprovadas: {relatorio['total_pecas_reprovadas']:,}\n"
        texto += f"• 📊 Taxa de Aprovação: {relatorio['taxa_aprovacao']}%\n\n"
        
        if relatorio['estatisticas_usuario']:
            texto += "👤 DESEMPENHO POR USUÁRIO\n"
            texto += "-"*80 + "\n"
            for usuario, stats in relatorio['estatisticas_usuario'].items():
                taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                texto += f"• {usuario}: {stats['aprovadas']} aprov., {stats['reprovadas']} reprov. ({taxa:.1f}%)\n"
            texto += "\n"
        
        texto += "="*80 + "\n"
        texto += "Relatório gerado automaticamente | QTools - Sistema de Qualidade e Gestão v0.1.5\n"
        texto += "="*80 + "\n"
        
        return texto
    
    helpers.requer_permissao('administrador')
    def tela_gestao_usuarios(self):
        """Tela de gestão de usuários"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("👥 Gestão de Usuários")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Barra de ações
        acao_frame = ctk.CTkFrame(content_frame)
        acao_frame.pack(fill="x", padx=10, pady=10)
        
        combo_filtro = ctk.CTkComboBox(acao_frame, width=150, 
                                      values=["Todos", "Ativos", "Inativos", "Administradores", "Supervisores", "Operadores"])
        combo_filtro.set("Todos")
        combo_filtro.pack(side="left", padx=5)
        
        def atualizar_lista():
            self.resetar_timeout()
            for widget in lista_frame.winfo_children():
                widget.destroy()
            
            filtro = combo_filtro.get()
            usuarios_filtrados = {}
            
            for user, data in self.auth.usuarios.items():
                if filtro == "Ativos" and not data.get('ativo', True):
                    continue
                if filtro == "Inativos" and data.get('ativo', True):
                    continue
                if filtro == "Administradores" and data.get('nivel') != 'administrador':
                    continue
                if filtro == "Supervisores" and data.get('nivel') != 'supervisor':
                    continue
                if filtro == "Operadores" and data.get('nivel') != 'operador':
                    continue
                usuarios_filtrados[user] = data
            
            if not usuarios_filtrados:
                ctk.CTkLabel(lista_frame, text="Nenhum usuário encontrado.", 
                           font=ctk.CTkFont(size=14), text_color="#666666").pack(pady=50)
                return
            
            # Cabeçalho
            header = ctk.CTkFrame(lista_frame, fg_color="#34495e")
            header.pack(fill="x", pady=(0, 10))
            
            headers = ["Username", "Nome", "Nível", "Status", "Último Login", "Ações"]
            for i, h in enumerate(headers):
                ctk.CTkLabel(header, text=h, font=ctk.CTkFont(size=12, weight="bold"), 
                           text_color="white").grid(row=0, column=i, padx=10, pady=8, sticky="w")
                header.columnconfigure(i, weight=1)
            
            # Usuários
            for idx, (user, data) in enumerate(usuarios_filtrados.items(), 1):
                row = ctk.CTkFrame(lista_frame, fg_color="#f8f9fa" if idx % 2 == 0 else "white")
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=user, font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=10, pady=6, sticky="w")
                ctk.CTkLabel(row, text=data['nome_completo'], font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=10, pady=6, sticky="w")
                ctk.CTkLabel(row, text=data['nivel'].title(), font=ctk.CTkFont(size=11)).grid(row=0, column=2, padx=10, pady=6, sticky="w")
                
                status = "✅ Ativo" if data.get('ativo', True) else "❌ Inativo"
                ctk.CTkLabel(row, text=status, font=ctk.CTkFont(size=11)).grid(row=0, column=3, padx=10, pady=6, sticky="w")
                
                ultimo_login = data.get('ultimo_login', 'Nunca')[:16] if data.get('ultimo_login') else 'Nunca'
                ctk.CTkLabel(row, text=ultimo_login, font=ctk.CTkFont(size=11)).grid(row=0, column=4, padx=10, pady=6, sticky="w")
                
                # Botões de ação
                acao_btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                acao_btn_frame.grid(row=0, column=5, padx=10, pady=6)
                
                ctk.CTkButton(acao_btn_frame, text="📝 Editar", width=60, height=30, 
                                command=lambda u=user: self.dialog_editar_usuario(u),
                                fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=2)
                
                if user != 'admin':  # Não pode deletar admin
                    ctk.CTkButton(acao_btn_frame, text="❌ Excluir", width=80, height=30, 
                                  command=lambda u=user: self.deletar_usuario(u),
                                  fg_color="#e74c3c", hover_color="#c0392b").pack(side="left", padx=2)

                
                for i in range(6):
                    row.columnconfigure(i, weight=1)
        
        ctk.CTkButton(acao_frame, text="🔍 Filtrar", width=100, height=40, 
                     command=atualizar_lista, fg_color="#3498db").pack(side="left", padx=5)
        
        # Lista de usuários
        lista_frame = ctk.CTkScrollableFrame(content_frame)
        lista_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        atualizar_lista()
        
        ctk.CTkButton(content_frame, text="➕ Novo Usuário", width=200, height=45, 
                      command=self.dialog_novo_usuario, fg_color="#27ae60").pack(pady=10)
    
    def dialog_novo_usuario(self):
        """Diálogo para criar novo usuário"""
        self.resetar_timeout()
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("➕ Novo Usuário")
        dialog.geometry("1200x800")
        dialog.minsize(1000, 700)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="➕ CRIAR NOVO USUÁRIO", 
                    font=ctk.CTkFont(size=18, weight="bold"), text_color="#27ae60").pack(pady=20)
        
        form = ctk.CTkFrame(dialog)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(form, text="Username:", font=ctk.CTkFont(size=12, weight="bold"), width=450).pack(pady=(10, 5))
        entry_user = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Ex: joao.silva")
        entry_user.pack(pady=5)
        entry_user.focus()
        
        ctk.CTkLabel(form, text="Nome Completo:", font=ctk.CTkFont(size=12, weight="bold"), width=450).pack(pady=(10, 5))
        entry_nome = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Ex: João Silva")
        entry_nome.pack(pady=5)
        
        ctk.CTkLabel(form, text="Senha:", font=ctk.CTkFont(size=12, weight="bold"), width=450).pack(pady=(10, 5))
        entry_senha = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Mínimo 4 caracteres", show="●")
        entry_senha.pack(pady=5)
        
        ctk.CTkLabel(form, text="Confirmar Senha:", font=ctk.CTkFont(size=12, weight="bold"), width=450).pack(pady=(10, 5))
        entry_senha2 = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Digite novamente", show="●")
        entry_senha2.pack(pady=5)
        
        ctk.CTkLabel(form, text="Nível de Acesso:", font=ctk.CTkFont(size=12, weight="bold"), width=450).pack(pady=(10, 5))
        combo_nivel = ctk.CTkComboBox(form, width=450, height=40, 
                                     values=["operador", "supervisor", "administrador"])
        combo_nivel.set("operador")
        combo_nivel.pack(pady=5)
        
        def criar():
            self.resetar_timeout()
            user = entry_user.get().strip()
            nome = entry_nome.get().strip()
            senha = entry_senha.get()
            senha2 = entry_senha2.get()
            nivel = combo_nivel.get()
            
            if not user or not nome or not senha:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            if senha != senha2:
                messagebox.showerror("Erro", "As senhas não coincidem!")
                return
            
            sucesso, msg = self.auth.criar_usuario(user, senha, nome, nivel)
            
            if sucesso:
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "CRIAR_USUARIO", f"Criou usuário: {user}")
                messagebox.showinfo("Sucesso", msg)
                dialog.destroy()
                self.tela_gestao_usuarios()
            else:
                messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=150, height=40, command=dialog.destroy,
                     fg_color="#95a5a6").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="✅ Criar", width=150, height=40, command=criar,
                     fg_color="#27ae60", hover_color="#229954").pack(side="left", padx=10)
    
    def dialog_editar_usuario(self, username: str):
        """Diálogo para editar usuário"""
        self.resetar_timeout()
        
        user_data = self.auth.usuarios.get(username)
        if not user_data:
            messagebox.showerror("Erro", "Usuário não encontrado!")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("✏️ Editar Usuário")
        dialog.geometry("1200x800")
        dialog.minsize(1000, 700)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"✏️ EDITAR: {username}", 
                    font=ctk.CTkFont(size=18, weight="bold"), text_color="#3498db").pack(pady=20)
        
        form = ctk.CTkFrame(dialog)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(form, text="Nome Completo:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        entry_nome = ctk.CTkEntry(form, width=450, height=40)
        entry_nome.insert(0, user_data['nome_completo'])
        entry_nome.pack(pady=5)
        
        ctk.CTkLabel(form, text="Nova Senha (deixe vazio para não alterar):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        entry_senha = ctk.CTkEntry(form, width=450, height=40, placeholder_text="Nova senha (opcional)", show="●")
        entry_senha.pack(pady=5)
        
        ctk.CTkLabel(form, text="Nível de Acesso:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        combo_nivel = ctk.CTkComboBox(form, width=450, height=40, 
                                     values=["operador", "supervisor", "administrador"])
        combo_nivel.set(user_data['nivel'])
        combo_nivel.pack(pady=5)
        
        var_ativo = ctk.BooleanVar(value=user_data.get('ativo', True))
        ctk.CTkSwitch(form, text="Usuário Ativo", variable=var_ativo, 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)
        
        def salvar():
            self.resetar_timeout()
            dados = {
                'nome_completo': entry_nome.get().strip(),
                'nivel': combo_nivel.get(),
                'ativo': var_ativo.get()
            }
            
            senha = entry_senha.get()
            if senha:
                dados['senha'] = senha
            
            sucesso, msg = self.auth.atualizar_usuario(username, dados)
            
            if sucesso:
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "EDITAR_USUARIO", f"Editou usuário: {username}")
                messagebox.showinfo("Sucesso", msg)
                dialog.destroy()
                self.tela_gestao_usuarios()
            else:
                messagebox.showerror("Erro", msg)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=150, height=40, command=dialog.destroy,
                     fg_color="#95a5a6").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="💾 Salvar", width=150, height=40, command=salvar,
                     fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=10)
    
    def deletar_usuario(self, username: str):
        """Deleta usuário"""
        self.resetar_timeout()
        
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja deletar o usuário '{username}'?\n\n⚠️ Esta ação não pode ser desfeita!"
        )
        
        if resposta:
            sucesso, msg = self.auth.deletar_usuario(username)
            if sucesso:
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "DELETAR_USUARIO", f"Deletou usuário: {username}")
                messagebox.showinfo("Sucesso", msg)
                self.tela_gestao_usuarios()
            else:
                messagebox.showerror("Erro", msg)
    
    helpers.requer_permissao('administrador')
    def tela_configuracoes(self):
        """Tela de configurações"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("⚙️ Configurações do Sistema")
        
        content_frame = ctk.CTkFrame(self.frame_principal)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tabview = ctk.CTkTabview(content_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_criterios = tabview.add("🎯 Critérios")
        tab_sistema = tabview.add("⚙️ Sistema")
        tab_metas = tabview.add("📊 Metas")
        
        self.criar_config_criterios(tab_criterios)
        self.criar_config_sistema(tab_sistema)
        self.criar_config_metas(tab_metas)
        
        ctk.CTkButton(content_frame, text="🔙 Voltar", width=200, height=45, 
                     command=self.criar_menu_principal, fg_color="#95a5a6").pack(pady=10)
    def criar_config_criterios(self, parent):
        """Configuração de critérios de qualidade"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        criterios = self.db.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
        
        ctk.CTkLabel(frame, text="Configurar Critérios de Qualidade:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Peso
        ctk.CTkLabel(frame, text="Peso (g):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        peso_frame = ctk.CTkFrame(frame, width=200, fg_color="transparent")
        peso_frame.pack(pady=5)
        
        peso_col1 = ctk.CTkFrame(peso_frame, fg_color="transparent")
        peso_col1.pack(fill="both")
        
        ctk.CTkLabel(peso_col1, text="Mínimo:").pack(side="left", padx=(0, 10))
        entry_peso_min = ctk.CTkEntry(peso_col1, width=90)
        entry_peso_min.insert(0, str(criterios['peso_min']))
        entry_peso_min.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(peso_col1, text="Máximo:").pack(side="left", padx=(0, 10))
        entry_peso_max = ctk.CTkEntry(peso_col1, width=90)
        entry_peso_max.insert(0, str(criterios['peso_max']))
        entry_peso_max.pack(side="left")
        
        # Comprimento
        ctk.CTkLabel(frame, text="Comprimento (cm):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        comp_frame = ctk.CTkFrame(frame, width=200, fg_color="transparent")
        comp_frame.pack(pady=5)
        
        comp_col1 = ctk.CTkFrame(comp_frame, fg_color="transparent")
        comp_col1.pack(fill="both")
        
        ctk.CTkLabel(comp_col1, text="Mínimo:").pack(side="left", padx=(0, 10))
        entry_comp_min = ctk.CTkEntry(comp_col1, width=90)
        entry_comp_min.insert(0, str(criterios['comprimento_min']))
        entry_comp_min.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(comp_col1, text="Máximo:").pack(side="left", padx=(0, 10))
        entry_comp_max = ctk.CTkEntry(comp_col1, width=90)
        entry_comp_max.insert(0, str(criterios['comprimento_max']))
        entry_comp_max.pack(side="left")
        
        # Cores
        ctk.CTkLabel(frame, text="Cores Aprovadas (separadas por vírgula):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_cores = ctk.CTkEntry(frame, width=400)
        entry_cores.insert(0, ", ".join(criterios['cores_aceitas']))
        entry_cores.pack(anchor="center", pady=5)
        
        def salvar_criterios():
            self.resetar_timeout()
            try:
                novos_criterios = {
                    'peso_min': float(entry_peso_min.get()),
                    'peso_max': float(entry_peso_max.get()),
                    'comprimento_min': float(entry_comp_min.get()),
                    'comprimento_max': float(entry_comp_max.get()),
                    'cores_aceitas': [cor.strip().lower() for cor in entry_cores.get().split(',')]
                }
                
                self.db.config['criterios_qualidade'] = novos_criterios
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Critérios de qualidade")
                
                messagebox.showinfo("Sucesso", "Critérios atualizados!")
            except ValueError:
                messagebox.showerror("Erro", "Valores numéricos inválidos!")
        
        ctk.CTkButton(frame, text="💾 Salvar Critérios", width=200, height=45, command=salvar_criterios,
                     fg_color="#27ae60", hover_color="#229954").pack(pady=30)

    def criar_config_sistema(self, parent):
        """Configuração do sistema"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Configurações do Sistema:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Capacidade da caixa
        ctk.CTkLabel(frame, text="Capacidade de Peças por Caixa:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_capacidade = ctk.CTkEntry(frame, width=100)
        entry_capacidade.insert(0, str(self.db.config.get('capacidade_caixa', 10)))
        entry_capacidade.pack(anchor="center", pady=5)
        
        # Backup automático
        var_backup = ctk.BooleanVar(value=self.db.config.get('auto_backup', True))
        ctk.CTkSwitch(frame, text="Backup Automático", variable=var_backup, 
                     font=ctk.CTkFont(size=14)).pack(anchor="center", pady=10)
        
        # Intervalo de backup
        ctk.CTkLabel(frame, text="Intervalo de Backup (horas):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_intervalo = ctk.CTkEntry(frame, width=100)
        entry_intervalo.insert(0, str(self.db.config.get('backup_interval_hours', 24)))
        entry_intervalo.pack(anchor="center", pady=5)
        
        # Timeout de sessão
        ctk.CTkLabel(frame, text="Timeout de Sessão (minutos):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_timeout = ctk.CTkEntry(frame, width=100)
        entry_timeout.insert(0, str(self.db.config.get('timeout_sessao_minutos', 30)))
        entry_timeout.pack(anchor="center", pady=5)
        
        def salvar_sistema():
            self.resetar_timeout()
            try:
                # self.db.config['capacidade_caixa'] = int(entry_capacidade.get())
                # self.db.config['auto_backup'] = var_backup.get()
                # self.db.config['backup_interval_hours'] = int(entry_intervalo.get())
                # self.db.config['timeout_sessao_minutos'] = int(entry_timeout.get())
                
                # ConfiguracaoSistema.salvar_configuracao(self.db.config)
                # ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Sistema")
                
                #messagebox.showinfo("Sucesso", "Configurações salvas!") 
                messagebox.showwarning("EM BREVE", "Recurso em desenvolvimento")
            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos!")
        
        ctk.CTkButton(frame, text="💾 Salvar Configurações", width=200, height=45, command=salvar_sistema,
                     fg_color="#3498db", hover_color="#2980b9").pack(pady=30)
    
    def criar_config_metas(self, parent):
        """Configuração de metas"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Configurar Metas de Produção:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        metas = self.db.config.get('metas', ConfiguracaoSistema.CONFIG_PADRAO['metas'])
        
        ctk.CTkLabel(frame, text="Meta Diária (peças aprovadas):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_meta = ctk.CTkEntry(frame, width=100)
        entry_meta.insert(0, str(metas.get('diaria', 500)))
        entry_meta.pack(anchor="center", pady=5)
        
        ctk.CTkLabel(frame, text="Taxa de Aprovação Mínima (%):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_taxa = ctk.CTkEntry(frame, width=100)
        entry_taxa.insert(0, str(metas.get('taxa_aprovacao_minima', 85)))
        entry_taxa.pack(anchor="center", pady=5)
        
        alertas = self.db.config.get('alertas', ConfiguracaoSistema.CONFIG_PADRAO['alertas'])
        
        ctk.CTkLabel(frame, text="Alerta de Taxa de Reprovação Alta (%):", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="center", pady=(20, 5))
        entry_alerta = ctk.CTkEntry(frame, width=100)
        entry_alerta.insert(0, str(alertas.get('taxa_reprovacao_alta', 15)))
        entry_alerta.pack(anchor="center", pady=5)
        
        def salvar_metas():
            self.resetar_timeout()
            try:
                self.db.config['metas'] = {
                    'diaria': int(entry_meta.get()),
                    'taxa_aprovacao_minima': float(entry_taxa.get())
                }
                self.db.config['alertas'] = {
                    'taxa_reprovacao_alta': float(entry_alerta.get()),
                    'som_enabled': True
                }
                
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Metas")
                
                messagebox.showinfo("Sucesso", "Metas atualizadas!")
            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos!")
        
        ctk.CTkButton(frame, text="💾 Salvar Metas", width=200, height=45, command=salvar_metas,
                     fg_color="#f39c12", hover_color="#e67e22").pack(pady=30)
    
    def criar_header(self, titulo: str):
        """Cria header padrão"""
        self.resetar_timeout()
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=70, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text=titulo, font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color="white").pack(side="left", padx=20, pady=15)
        
        ctk.CTkButton(header, text="🔙 Voltar", width=100, height=35, command=self.criar_menu_principal,
                     font=ctk.CTkFont(size=12, weight="bold"), fg_color="white", text_color="#1f538d",
                     hover_color="#e0e0e0").pack(side="right", padx=20, pady=15)
    
    def limpar_tela(self):
        """Limpa tela"""
        for widget in self.frame_principal.winfo_children():
            widget.destroy()