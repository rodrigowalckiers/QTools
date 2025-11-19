"""
Sistema de Controle de Qualidade Industrial
Versão 3.1.1 - Corrigida com Menu Funcional e Date Picker
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import bcrypt
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import csv
import threading
from collections import Counter
from functools import wraps

# ====================================================================================
# VERIFICAÇÃO DE DEPENDÊNCIAS
# ====================================================================================

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog, font
    from tkcalendar import DateEntry
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
    TK_CALENDAR_AVAILABLE = True
except ImportError as e:
    print(f"❌ Erro ao importar dependências: {e}")
    print("⏳ Instalando dependências necessárias...")
    
    # Instalar todas as dependências necessárias
    packages = ["customtkinter", "Pillow", "bcrypt", "matplotlib", "reportlab", "tkcalendar"]
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado com sucesso")
        except subprocess.CalledProcessError:
            if package == "tkcalendar":
                # Tentar importar tkcalendar (será instalado se necessário)
                try:
                    from tkcalendar import DateEntry
                except ImportError:
                    TK_CALENDAR_AVAILABLE = False
                    print("⚠️ tkcalendar não pôde ser instalado. Usando campos de texto para datas.")
            else:
                print(f"⚠️ Erro ao instalar {package}")
    
    print("🔄 Reinicie o programa após a instalação")
    sys.exit(1)

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================

class ConfiguracaoSistema:
    """Gerencia configurações e estrutura de pastas"""
    
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = DATA_DIR / "logs"
    BACKUP_DIR = DATA_DIR / "backups"
    REPORTS_DIR = DATA_DIR / "reports"
    
    ARQUIVO_USUARIOS = DATA_DIR / "usuarios.json"
    ARQUIVO_PECAS = DATA_DIR / "pecas.json"
    ARQUIVO_CAIXAS = DATA_DIR / "caixas.json"
    ARQUIVO_CONFIG = DATA_DIR / "config.json"
    ARQUIVO_AUDITORIA = DATA_DIR / "auditoria.json"
    
    CONFIG_PADRAO = {
        'criterios_qualidade': {
            'peso_min': 95,
            'peso_max': 105,
            'cores_aceitas': ['azul', 'verde'],
            'comprimento_min': 10,
            'comprimento_max': 20
        },
        'capacidade_caixa': 10,
        'auto_backup': True,
        'backup_interval_hours': 24,
        'interface': {
            'tema': 'light',
            'cor_primaria': 'blue'
        },
        'metas': {
            'diaria': 500,
            'taxa_aprovacao_minima': 85
        },
        'alertas': {
            'taxa_reprovacao_alta': 15,
            'som_enabled': True
        },
        'timeout_sessao_minutos': 30
    }
    
    @classmethod
    def criar_estrutura_pastas(cls):
        """Cria estrutura de pastas"""
        try:
            cls.DATA_DIR.mkdir(exist_ok=True)
            cls.LOGS_DIR.mkdir(exist_ok=True)
            cls.BACKUP_DIR.mkdir(exist_ok=True)
            cls.REPORTS_DIR.mkdir(exist_ok=True)
            
            if not cls.ARQUIVO_CONFIG.exists():
                with open(cls.ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
                    json.dump(cls.CONFIG_PADRAO, f, indent=2, ensure_ascii=False)
            
            if not cls.ARQUIVO_AUDITORIA.exists():
                with open(cls.ARQUIVO_AUDITORIA, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
            
            cls.registrar_log("Sistema inicializado", "SISTEMA")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar estrutura: {e}")
            return False
    
    @classmethod
    def carregar_configuracao(cls) -> Dict:
        """Carrega configurações"""
        try:
            if cls.ARQUIVO_CONFIG.exists():
                with open(cls.ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in cls.CONFIG_PADRAO.items():
                        if key not in config:
                            config[key] = value
                    return config
            return cls.CONFIG_PADRAO.copy()
        except:
            return cls.CONFIG_PADRAO.copy()
    
    @classmethod
    def salvar_configuracao(cls, config: Dict):
        """Salva configurações"""
        try:
            with open(cls.ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            cls.registrar_log(f"Erro ao salvar config: {e}", "ERRO")
            return False
    
    @classmethod
    def registrar_log(cls, mensagem: str, tipo: str = "INFO"):
        """Registra log"""
        try:
            log_arquivo = cls.LOGS_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(log_arquivo, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - [{tipo}] {mensagem}\n")
        except:
            pass
    
    @classmethod
    def registrar_auditoria(cls, usuario: str, acao: str, detalhes: str = ""):
        """Registra ação para auditoria"""
        try:
            auditoria = []
            if cls.ARQUIVO_AUDITORIA.exists():
                with open(cls.ARQUIVO_AUDITORIA, 'r', encoding='utf-8') as f:
                    auditoria = json.load(f)
            
            auditoria.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'usuario': usuario,
                'acao': acao,
                'detalhes': detalhes
            })
            
            # Manter apenas últimos 1000 registros
            auditoria = auditoria[-1000:]
            
            with open(cls.ARQUIVO_AUDITORIA, 'w', encoding='utf-8') as f:
                json.dump(auditoria, f, indent=2, ensure_ascii=False)
        except:
            pass

# ====================================================================================
# DECORADOR DE PERMISSÕES
# ====================================================================================

def requer_permissao(nivel_minimo: str):
    """Decorador para verificar permissões"""
    niveis = {'operador': 0, 'supervisor': 1, 'administrador': 2}
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            nivel_usuario = niveis.get(self.info_usuario.get('nivel', 'operador'), 0)
            nivel_requerido = niveis.get(nivel_minimo, 0)
            
            if nivel_usuario >= nivel_requerido:
                return func(self, *args, **kwargs)
            else:
                messagebox.showerror(
                    "Acesso Negado",
                    f"Você precisa ser {nivel_minimo.upper()} para acessar esta função!"
                )
                ConfiguracaoSistema.registrar_auditoria(
                    self.usuario,
                    "ACESSO_NEGADO",
                    f"Tentativa de acessar {func.__name__}"
                )
        return wrapper
    return decorator

# ====================================================================================
# SISTEMA DE AUTENTICAÇÃO
# ====================================================================================

class SistemaAutenticacao:
    """Gerencia autenticação e usuários"""
    
    def __init__(self):
        self.arquivo_usuarios = ConfiguracaoSistema.ARQUIVO_USUARIOS
        self.usuarios = self.carregar_usuarios()
        
        if not self.usuarios:
            self.criar_usuario_padrao()
    
    def carregar_usuarios(self) -> Dict:
        """Carrega usuários"""
        try:
            if self.arquivo_usuarios.exists():
                with open(self.arquivo_usuarios, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def salvar_usuarios(self):
        """Salva usuários"""
        try:
            with open(self.arquivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    def criar_usuario_padrao(self):
        """Cria usuário admin padrão"""
        try:
            senha_hash = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.usuarios['admin'] = {
                'senha': senha_hash,
                'nome_completo': 'Administrador do Sistema',
                'nivel': 'administrador',
                'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ultimo_login': None,
                'ativo': True
            }
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log("Usuário admin criado", "SISTEMA")
        except Exception as e:
            print(f"❌ Erro ao criar admin: {e}")
    
    def autenticar(self, usuario: str, senha: str) -> Tuple[bool, Optional[Dict]]:
        """Autentica usuário"""
        try:
            if usuario in self.usuarios:
                user_data = self.usuarios[usuario]
                
                if not user_data.get('ativo', True):
                    return False, None
                
                senha_hash = user_data['senha']
                if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                    user_data['ultimo_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.salvar_usuarios()
                    ConfiguracaoSistema.registrar_log(f"Login: {usuario}", "AUTH")
                    ConfiguracaoSistema.registrar_auditoria(usuario, "LOGIN", "Login bem-sucedido")
                    return True, user_data
            
            ConfiguracaoSistema.registrar_log(f"Login falhou: {usuario}", "AUTH")
            return False, None
        except:
            return False, None
    
    def criar_usuario(self, usuario: str, senha: str, nome_completo: str, nivel: str) -> Tuple[bool, str]:
        """Cria novo usuário"""
        try:
            if usuario in self.usuarios:
                return False, "Usuário já existe"
            
            if len(senha) < 4:
                return False, "Senha muito curta (mínimo 4 caracteres)"
            
            if nivel not in ['administrador', 'supervisor', 'operador']:
                return False, "Nível inválido"
            
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.usuarios[usuario] = {
                'senha': senha_hash,
                'nome_completo': nome_completo,
                'nivel': nivel,
                'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ultimo_login': None,
                'ativo': True
            }
            self.salvar_usuarios()
            ConfiguracaoSistema.registrar_log(f"Usuário criado: {usuario}", "ADMIN")
            return True, "Usuário criado com sucesso"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def atualizar_usuario(self, usuario: str, dados: Dict) -> Tuple[bool, str]:
        """Atualiza usuário existente"""
        try:
            if usuario not in self.usuarios:
                return False, "Usuário não encontrado"
            
            if 'senha' in dados and dados['senha']:
                if len(dados['senha']) < 4:
                    return False, "Senha muito curta"
                dados['senha'] = bcrypt.hashpw(dados['senha'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            else:
                dados.pop('senha', None)
            
            self.usuarios[usuario].update(dados)
            self.salvar_usuarios()
            return True, "Usuário atualizado"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def deletar_usuario(self, usuario: str) -> Tuple[bool, str]:
        """Deleta usuário"""
        try:
            if usuario == 'admin':
                return False, "Não pode deletar admin"
            
            if usuario in self.usuarios:
                del self.usuarios[usuario]
                self.salvar_usuarios()
                return True, "Usuário deletado"
            return False, "Usuário não encontrado"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def listar_usuarios(self) -> List[Dict]:
        """Lista todos os usuários"""
        usuarios_lista = []
        for username, data in self.usuarios.items():
            usuarios_lista.append({
                'usuario': username,
                'nome_completo': data['nome_completo'],
                'nivel': data['nivel'],
                'data_criacao': data['data_criacao'],
                'ultimo_login': data.get('ultimo_login', 'Nunca'),
                'ativo': data.get('ativo', True)
            })
        return usuarios_lista

# ====================================================================================
# MODELOS DE DADOS
# ====================================================================================

class Peca:
    """Representa uma peça"""
    
    def __init__(self, id_peca: str, peso: float, cor: str, comprimento: float, usuario: str = ""):
        self.id_peca = id_peca.upper().strip()
        self.peso = peso
        self.cor = cor.lower().strip()
        self.comprimento = comprimento
        self.usuario = usuario
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data_inspecao = datetime.now().strftime("%Y-%m-%d")
        self.aprovada = False
        self.motivos_reprovacao = []
        self.turno = self.obter_turno_atual()
        
    def obter_turno_atual(self) -> str:
        """Determina turno"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def validar(self, criterios: Dict) -> bool:
        """Valida peça"""
        self.motivos_reprovacao = []
        
        if not (criterios['peso_min'] <= self.peso <= criterios['peso_max']):
            self.motivos_reprovacao.append(
                f"Peso: {self.peso}g (esperado: {criterios['peso_min']}-{criterios['peso_max']}g)"
            )
        
        if self.cor not in criterios['cores_aceitas']:
            cores = ", ".join(criterios['cores_aceitas'])
            self.motivos_reprovacao.append(f"Cor: {self.cor} (esperado: {cores})")
        
        if not (criterios['comprimento_min'] <= self.comprimento <= criterios['comprimento_max']):
            self.motivos_reprovacao.append(
                f"Comprimento: {self.comprimento}cm (esperado: {criterios['comprimento_min']}-{criterios['comprimento_max']}cm)"
            )
        
        self.aprovada = len(self.motivos_reprovacao) == 0
        return self.aprovada
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id_peca,
            'peso': self.peso,
            'cor': self.cor,
            'comprimento': self.comprimento,
            'usuario': self.usuario,
            'timestamp': self.timestamp,
            'data_inspecao': self.data_inspecao,
            'turno': self.turno,
            'aprovada': self.aprovada,
            'motivos_reprovacao': self.motivos_reprovacao
        }

class Caixa:
    """Representa uma caixa"""
    
    def __init__(self, numero: int, capacidade: int = 10):
        self.numero = numero
        self.capacidade = capacidade
        self.pecas: List[Peca] = []
        self.data_fechamento = None
        self.usuario_fechamento = ""
        self.data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def adicionar_peca(self, peca: Peca) -> bool:
        """Adiciona peça à caixa"""
        if len(self.pecas) < self.capacidade:
            self.pecas.append(peca)
            if len(self.pecas) >= self.capacidade:
                self.fechar(peca.usuario)
            return True
        return False
    
    def fechar(self, usuario: str = ""):
        """Fecha caixa"""
        self.data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.usuario_fechamento = usuario
    
    def esta_cheia(self) -> bool:
        return len(self.pecas) >= self.capacidade
    
    def vagas_disponiveis(self) -> int:
        return max(0, self.capacidade - len(self.pecas))
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'numero': self.numero,
            'capacidade': self.capacidade,
            'pecas': [p.to_dict() for p in self.pecas],
            'data_fechamento': self.data_fechamento,
            'usuario_fechamento': self.usuario_fechamento,
            'data_criacao': self.data_criacao,
            'quantidade_pecas': len(self.pecas),
            'percentual_cheio': (len(self.pecas) / self.capacidade) * 100
        }

# ====================================================================================
# BANCO DE DADOS COM NOVOS FILTROS
# ====================================================================================

class BancoDados:
    """Gerencia dados do sistema"""
    
    def __init__(self):
        self.arquivo_pecas = ConfiguracaoSistema.ARQUIVO_PECAS
        self.arquivo_caixas = ConfiguracaoSistema.ARQUIVO_CAIXAS
        self.config = ConfiguracaoSistema.carregar_configuracao()
        self.pecas_aprovadas: List[Peca] = []
        self.pecas_reprovadas: List[Peca] = []
        self.caixas_fechadas: List[Caixa] = []
        
        capacidade = self.config.get('capacidade_caixa', 10)
        self.caixa_atual: Caixa = Caixa(1, capacidade)
        
        self.carregar_dados()
        self.iniciar_backup_automatico()
    
    def carregar_dados(self):
        """Carrega dados dos arquivos"""
        if self.arquivo_pecas.exists():
            try:
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                self.pecas_aprovadas.clear()
                self.pecas_reprovadas.clear()
                
                for p_dict in dados.get('aprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_aprovadas.append(peca)
                
                for p_dict in dados.get('reprovadas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.motivos_reprovacao = p_dict.get('motivos_reprovacao', [])
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_reprovadas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar peças: {e}", "ERRO")
        
        if self.arquivo_caixas.exists():
            try:
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                self.caixas_fechadas.clear()
                
                for c_dict in dados.get('fechadas', []):
                    capacidade = c_dict.get('capacidade', self.config.get('capacidade_caixa', 10))
                    caixa = Caixa(c_dict['numero'], capacidade)
                    caixa.data_fechamento = c_dict.get('data_fechamento')
                    caixa.usuario_fechamento = c_dict.get('usuario_fechamento', '')
                    caixa.data_criacao = c_dict.get('data_criacao', '')
                    
                    for p_dict in c_dict.get('pecas', []):
                        peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                        peca.aprovada = p_dict['aprovada']
                        peca.timestamp = p_dict.get('timestamp', '')
                        peca.data_inspecao = p_dict.get('data_inspecao', '')
                        peca.turno = p_dict.get('turno', '')
                        caixa.pecas.append(peca)
                    self.caixas_fechadas.append(caixa)
                
                c_atual = dados.get('atual', {})
                capacidade_atual = c_atual.get('capacidade', self.config.get('capacidade_caixa', 10))
                self.caixa_atual = Caixa(c_atual.get('numero', len(self.caixas_fechadas) + 1), capacidade_atual)
                
                for p_dict in c_atual.get('pecas', []):
                    peca = Peca(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.caixa_atual.pecas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar caixas: {e}", "ERRO")
    
    def salvar_dados(self):
        """Salva dados"""
        try:
            self.fazer_backup()
            
            dados_pecas = {
                'aprovadas': [p.to_dict() for p in self.pecas_aprovadas],
                'reprovadas': [p.to_dict() for p in self.pecas_reprovadas],
                'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.arquivo_pecas, 'w', encoding='utf-8') as f:
                json.dump(dados_pecas, f, indent=2, ensure_ascii=False)
            
            dados_caixas = {
                'fechadas': [c.to_dict() for c in self.caixas_fechadas],
                'atual': self.caixa_atual.to_dict(),
                'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.arquivo_caixas, 'w', encoding='utf-8') as f:
                json.dump(dados_caixas, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao salvar: {e}", "ERRO")
            return False
    
    def fazer_backup(self):
        """Faz backup"""
        try:
            if not self.config.get('auto_backup', True):
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.arquivo_pecas.exists():
                backup_pecas = ConfiguracaoSistema.BACKUP_DIR / f"pecas_backup_{timestamp}.json"
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as origem:
                    with open(backup_pecas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
            
            if self.arquivo_caixas.exists():
                backup_caixas = ConfiguracaoSistema.BACKUP_DIR / f"caixas_backup_{timestamp}.json"
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as origem:
                    with open(backup_caixas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
                        
            ConfiguracaoSistema.registrar_log("Backup realizado", "BACKUP")
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro backup: {e}", "ERRO")
    
    def iniciar_backup_automatico(self):
        """Inicia thread de backup automático"""
        def backup_thread():
            while True:
                try:
                    ultimo_backup = getattr(self, '_ultimo_backup', None)
                    intervalo_horas = self.config.get('backup_interval_hours', 24)
                    
                    if not ultimo_backup or (datetime.now() - ultimo_backup) > timedelta(hours=intervalo_horas):
                        self.fazer_backup()
                        self._ultimo_backup = datetime.now()
                    
                    threading.Event().wait(3600)
                except:
                    pass
        
        if self.config.get('auto_backup', True):
            thread = threading.Thread(target=backup_thread, daemon=True)
            thread.start()
    
    def adicionar_peca(self, peca: Peca) -> Tuple[bool, str]:
        """Adiciona peça"""
        try:
            for p in self.pecas_aprovadas + self.pecas_reprovadas:
                if p.id_peca == peca.id_peca:
                    return False, f"ID {peca.id_peca} já existe"
            
            criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
            peca.validar(criterios)
            
            if peca.aprovada:
                self.pecas_aprovadas.append(peca)
                
                if not self.caixa_atual.adicionar_peca(peca):
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
                    self.caixa_atual.adicionar_peca(peca)
                
                if self.caixa_atual.esta_cheia():
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = Caixa(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
            else:
                self.pecas_reprovadas.append(peca)
            
            self.salvar_dados()
            ConfiguracaoSistema.registrar_log(f"Peça {peca.id_peca} {'aprovada' if peca.aprovada else 'reprovada'}", "INSPECAO")
            
            return True, "Peça adicionada"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def editar_peca(self, id_peca: str, novo_peso: float, nova_cor: str, novo_comprimento: float, usuario: str = "") -> Tuple[bool, str]:
        """Edita uma peça existente"""
        try:
            id_peca = id_peca.upper().strip()
            
            # Buscar em peças aprovadas
            for peca in self.pecas_aprovadas:
                if peca.id_peca == id_peca:
                    peca_antiga = peca.to_dict().copy()
                    
                    peca.peso = novo_peso
                    peca.cor = nova_cor.lower()
                    peca.comprimento = novo_comprimento
                    
                    # Revalidar a peça
                    criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
                    estava_aprovada = peca.aprovada
                    peca.validar(criterios)
                    
                    # Se foi reprovada após edição, mover para lista de reprovadas
                    if not peca.aprovada and estava_aprovada:
                        self.pecas_aprovadas.remove(peca)
                        self.pecas_reprovadas.append(peca)
                        # Remover da caixa atual se estiver lá
                        for p_caixa in self.caixa_atual.pecas:
                            if p_caixa.id_peca == id_peca:
                                self.caixa_atual.pecas.remove(p_caixa)
                                break
                    
                    self.salvar_dados()
                    ConfiguracaoSistema.registrar_auditoria(usuario, "EDITAR_PECA", 
                        f"ID: {id_peca} - De: Peso{peca_antiga['peso']}g, Cor{peca_antiga['cor']}, Comp{peca_antiga['comprimento']}cm | Para: Peso{novo_peso}g, Cor{nova_cor}, Comp{novo_comprimento}cm")
                    
                    return True, "Peça editada com sucesso"
            
            # Buscar em peças reprovadas
            for peca in self.pecas_reprovadas:
                if peca.id_peca == id_peca:
                    peca_antiga = peca.to_dict().copy()
                    
                    peca.peso = novo_peso
                    peca.cor = nova_cor.lower()
                    peca.comprimento = novo_comprimento
                    
                    # Revalidar a peça
                    criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
                    estava_aprovada = peca.aprovada
                    peca.validar(criterios)
                    
                    # Se foi aprovada após edição, mover para lista de aprovadas
                    if peca.aprovada and not estava_aprovada:
                        self.pecas_reprovadas.remove(peca)
                        self.pecas_aprovadas.append(peca)
                        # Adicionar à caixa atual
                        self.caixa_atual.adicionar_peca(peca)
                    
                    self.salvar_dados()
                    ConfiguracaoSistema.registrar_auditoria(usuario, "EDITAR_PECA", 
                        f"ID: {id_peca} - De: Peso{peca_antiga['peso']}g, Cor{peca_antiga['cor']}, Comp{peca_antiga['comprimento']}cm | Para: Peso{novo_peso}g, Cor{nova_cor}, Comp{novo_comprimento}cm")
                    
                    return True, "Peça editada com sucesso"
            
            return False, f"Peça {id_peca} não encontrada"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao editar peça: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"
    
    def remover_peca(self, id_peca: str, usuario: str = "", justificativa: str = "") -> Tuple[bool, str]:
        """Remove peça"""
        id_peca = id_peca.upper().strip()
        
        for i, peca in enumerate(self.pecas_aprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_aprovadas[i]
                
                for j, p_caixa in enumerate(self.caixa_atual.pecas):
                    if p_caixa.id_peca == id_peca:
                        del self.caixa_atual.pecas[j]
                        break
                
                self.salvar_dados()
                ConfiguracaoSistema.registrar_auditoria(usuario, "REMOVER_PECA", f"ID: {id_peca} - {justificativa}")
                return True, f"Peça {id_peca} removida"
        
        for i, peca in enumerate(self.pecas_reprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_reprovadas[i]
                self.salvar_dados()
                ConfiguracaoSistema.registrar_auditoria(usuario, "REMOVER_PECA", f"ID: {id_peca} - {justificativa}")
                return True, f"Peça {id_peca} removida"
        
        return False, f"Peça {id_peca} não encontrada"
    
    # ========== NOVOS MÉTODOS DE FILTRO ==========
    def filtrar_pecas_por_data(self, pecas: List[Peca], data_inicio: str = None, data_fim: str = None) -> List[Peca]:
        """Filtra peças por período"""
        if not data_inicio and not data_fim:
            return pecas
        
        pecas_filtradas = []
        for peca in pecas:
            try:
                data_peca = datetime.strptime(peca.timestamp, "%Y-%m-%d %H:%M:%S")
                
                if data_inicio:
                    dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                    if data_peca < data_inicio:
                        continue
                
                if data_fim:
                    dt_fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
                    if data_peca >= data_fim:
                        continue
                
                pecas_filtradas.append(peca)
            except:
                pass
        
        return pecas_filtradas
    
    def buscar_peca_por_id(self, id_peca: str) -> Optional[Peca]:
        """Busca peça específica por ID"""
        id_peca = id_peca.upper().strip()
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.id_peca == id_peca:
                return peca
        return None
    
    def buscar_pecas_por_data(self, data: str) -> List[Peca]:
        """Busca peças por data específica (formato: YYYY-MM-DD)"""
        data = datetime.strftime(data, '%Y-%m-%d')
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.data_inspecao == data:
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def buscar_pecas_por_usuario(self, usuario: str) -> List[Peca]:
        """Busca peças por usuário específico"""
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.usuario.lower() == usuario.lower():
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def buscar_pecas_por_data_e_usuario(self, data: str, usuario: str) -> List[Peca]:
        data = datetime.strftime(data, '%Y-%m-%d')
        """Busca peças por data E usuário"""
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.data_inspecao == data and peca.usuario.lower() == usuario.lower():
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def buscar_pecas_por_periodo(self, data_inicio, data_fim) -> List[Peca]:
        # data_inicio = datetime.strftime(data_inicio, '%Y-%m-%d')
        # data_fim = datetime.strftime(data_fim, '%Y-%m-%d')
        """Busca peças por período"""
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            data_peca = datetime.strptime(peca.data_inspecao, '%Y-%m-%d')
            data_peca = datetime.date(data_peca)
            if data_inicio <= data_peca <= data_fim:
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def gerar_relatorio_diario(self, data: datetime) -> Dict:
        """Gera relatório específico para um dia"""
        pecas_dia = self.buscar_pecas_por_data(data)
        return self._gerar_relatorio_estruturado(pecas_dia, f"Relatório Diário - {data}")
    
    def gerar_relatorio_usuario(self, usuario: str, data_inicio: str = None, data_fim: str = None) -> Dict:
        """Gera relatório específico para um usuário"""
        if data_inicio and data_fim:
            todas_pecas = self.buscar_pecas_por_periodo(data_inicio, data_fim)
            pecas_usuario = [p for p in todas_pecas if p.usuario.lower() == usuario.lower()]
        else:
            pecas_usuario = self.buscar_pecas_por_usuario(usuario)
        
        periodo = f"{data_inicio} a {data_fim}" if data_inicio and data_fim else "Todo o período"
        return self._gerar_relatorio_estruturado(pecas_usuario, f"Relatório do Usuário {usuario} - {periodo}")
    
    def gerar_relatorio_diario_usuario(self, data: str, usuario: str) -> Dict:
        """Gera relatório específico para um dia e usuário"""
        pecas = self.buscar_pecas_por_data_e_usuario(data, usuario)
        return self._gerar_relatorio_estruturado(pecas, f"Relatório Diário - {data} - Usuário: {usuario}")
    
    def _gerar_relatorio_estruturado(self, pecas: List[Peca], titulo: str) -> Dict:
        """Gera estrutura de relatório a partir de uma lista de peças"""
        aprovadas = [p for p in pecas if p.aprovada]
        reprovadas = [p for p in pecas if not p.aprovada]
        
        total_pecas = len(pecas)
        taxa_aprovacao = (len(aprovadas) / total_pecas * 100) if total_pecas > 0 else 0
        
        # Estatísticas por usuário
        estatisticas_usuario = {}
        for peca in pecas:
            usuario = peca.usuario
            if usuario not in estatisticas_usuario:
                estatisticas_usuario[usuario] = {'aprovadas': 0, 'reprovadas': 0, 'total': 0}
            
            if peca.aprovada:
                estatisticas_usuario[usuario]['aprovadas'] += 1
            else:
                estatisticas_usuario[usuario]['reprovadas'] += 1
            estatisticas_usuario[usuario]['total'] += 1
        
        # Estatísticas por turno
        estatisticas_turno = {}
        for peca in pecas:
            turno = peca.turno
            if turno not in estatisticas_turno:
                estatisticas_turno[turno] = {'aprovadas': 0, 'reprovadas': 0, 'total': 0}
            
            if peca.aprovada:
                estatisticas_turno[turno]['aprovadas'] += 1
            else:
                estatisticas_turno[turno]['reprovadas'] += 1
            estatisticas_turno[turno]['total'] += 1
        
        # Análise de motivos de reprovação
        motivos_reprovacao = Counter()
        for peca in reprovadas:
            for motivo in peca.motivos_reprovacao:
                if 'Peso' in motivo:
                    motivos_reprovacao['Peso'] += 1
                elif 'Cor' in motivo:
                    motivos_reprovacao['Cor'] += 1
                elif 'Comprimento' in motivo:
                    motivos_reprovacao['Comprimento'] += 1
        
        return {
            'titulo': titulo,
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_pecas_aprovadas': len(aprovadas),
            'total_pecas_reprovadas': len(reprovadas),
            'total_pecas_inspecionadas': total_pecas,
            'taxa_aprovacao': round(taxa_aprovacao, 2),
            'estatisticas_usuario': estatisticas_usuario,
            'estatisticas_turno': estatisticas_turno,
            'analise_motivos_reprovacao': dict(motivos_reprovacao),
            'pecas_detalhadas': [p.to_dict() for p in pecas]
        }

# ====================================================================================
# GERADOR DE RELATÓRIOS PDF
# ====================================================================================

class GeradorRelatoriosPDF:
    """Gera relatórios em PDF profissional"""
    
    @staticmethod
    def gerar_relatorio_executivo(relatorio: Dict, caminho: str, usuario: str):
        """Gera PDF executivo completo"""
        try:
            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f538d'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("🏭 RELATÓRIO DE CONTROLE DE QUALIDADE", titulo_style))
            story.append(Paragraph(f"Sistema Industrial - Versão 3.1.1", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Informações do relatório
            info_data = [
                ['Data de Geração:', relatorio['data_geracao']],
                ['Relatório:', relatorio['titulo']],
                ['Gerado por:', usuario],
            ]
            
            info_table = Table(info_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 1*cm))
            
            # Resumo Executivo
            resumo_style = ParagraphStyle(
                'ResumoTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1f538d'),
                spaceAfter=15
            )
            
            story.append(Paragraph("📈 RESUMO EXECUTIVO", resumo_style))
            
            resumo_data = [
                ['Métrica', 'Valor', 'Status'],
                ['Total de Peças Inspecionadas', f"{relatorio['total_pecas_inspecionadas']:,}", '✓'],
                ['Peças Aprovadas', f"{relatorio['total_pecas_aprovadas']:,}", '✅'],
                ['Peças Reprovadas', f"{relatorio['total_pecas_reprovadas']:,}", '❌'],
                ['Taxa de Aprovação', f"{relatorio['taxa_aprovacao']:.2f}%", 
                 '🟢' if relatorio['taxa_aprovacao'] >= 85 else '🟡' if relatorio['taxa_aprovacao'] >= 70 else '🔴'],
            ]
            
            resumo_table = Table(resumo_data, colWidths=[7*cm, 5*cm, 3*cm])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f538d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(resumo_table)
            story.append(Spacer(1, 1*cm))
            
            # Estatísticas por Usuário
            if relatorio['estatisticas_usuario']:
                story.append(Paragraph("👤 ANÁLISE POR USUÁRIO", resumo_style))
                
                usuario_data = [['Usuário', 'Aprovadas', 'Reprovadas', 'Total', 'Taxa Aprov.']]
                for usuario, stats in relatorio['estatisticas_usuario'].items():
                    taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    usuario_data.append([
                        usuario,
                        str(stats['aprovadas']),
                        str(stats['reprovadas']),
                        str(stats['total']),
                        f"{taxa:.1f}%"
                    ])
                
                usuario_table = Table(usuario_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
                usuario_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(usuario_table)
                story.append(Spacer(1, 0.8*cm))
            
            # Estatísticas por Turno
            if relatorio['estatisticas_turno']:
                story.append(Paragraph("🕒 ANÁLISE POR TURNO", resumo_style))
                
                turno_data = [['Turno', 'Aprovadas', 'Reprovadas', 'Total', 'Taxa Aprov.']]
                for turno, stats in relatorio['estatisticas_turno'].items():
                    taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    turno_data.append([
                        turno,
                        str(stats['aprovadas']),
                        str(stats['reprovadas']),
                        str(stats['total']),
                        f"{taxa:.1f}%"
                    ])
                
                turno_table = Table(turno_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
                turno_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(turno_table)
                story.append(Spacer(1, 0.8*cm))
            
            # Análise de Reprovações
            if relatorio['analise_motivos_reprovacao']:
                story.append(Paragraph("❌ ANÁLISE DE MOTIVOS DE REPROVAÇÃO", resumo_style))
                
                motivos_data = [['Motivo', 'Quantidade', 'Percentual']]
                total_reprov = sum(relatorio['analise_motivos_reprovacao'].values())
                
                for motivo, qtd in relatorio['analise_motivos_reprovacao'].items():
                    perc = (qtd / total_reprov * 100) if total_reprov > 0 else 0
                    motivos_data.append([motivo, str(qtd), f"{perc:.1f}%"])
                
                motivos_table = Table(motivos_data, colWidths=[6*cm, 4*cm, 5*cm])
                motivos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(motivos_table)
                story.append(Spacer(1, 1*cm))
            
            # Rodapé
            story.append(Spacer(1, 2*cm))
            rodape = Paragraph(
                f"Relatório gerado automaticamente - Sistema de Controle de Qualidade v3.1.1<br/>"
                f"© {datetime.now().year} - Todos os direitos reservados",
                styles['Normal']
            )
            story.append(rodape)
            
            # Gerar PDF
            doc.build(story)
            ConfiguracaoSistema.registrar_log(f"Relatório PDF gerado: {caminho}", "RELATORIO")
            return True, caminho
            
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao gerar PDF: {e}", "ERRO")
            return False, f"Erro: {str(e)}"

# ====================================================================================
# COMPONENTES DE INTERFACE REUTILIZÁVEIS
# ====================================================================================

class DatePicker(ctk.CTkFrame):
    """Campo de data moderno com bordas arredondadas para filtros"""
    
    def __init__(self, master,  width=140, height=32, placeholder="dd/mm/aaaa", **kwargs):
        # Extrair configurações personalizadas
        self.date_format = kwargs.pop('date_format', '%d/%m/%Y')
        self.on_date_selected = kwargs.pop('on_date_selected', None)
        
        # Configurações do frame
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.placeholder = placeholder
        self.selected_date = None
        self.calendar_window = None
        self.width = width
        self.height = height
        # Criar o campo de entrada
        self._create_entry()
    
    def _create_entry(self):
        """Cria o campo de entrada estilizado"""
        # Container com efeito de hover
        self.entry_container = ctk.CTkFrame(self, fg_color="transparent")
        self.entry_container.pack(fill="x")
        
        # Frame interno para o campo
        self.input_frame = ctk.CTkFrame(
            self.entry_container,
            fg_color=("#F1F5F9", "#1E293B"),
            corner_radius=6,
            border_width=2,
            border_color="#979da2"
        )
        self.input_frame.pack(fill="x")
        
        # Entry
        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text=self.placeholder,
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(size=14),
            width=self.width,
            height=self.height
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(12, 0))
        self.entry.configure(state="readonly")
        
        # Botão de calendário
        self.calendar_btn = ctk.CTkButton(
            self.input_frame,
            text="📅",
            width=25,
            height=32,
            fg_color="transparent",
            hover_color=("#DFDFDF", "#DFDFDF"),
            text_color=("#ADADAD", "#ADADAD"),
            font=ctk.CTkFont(size=18),
            command=self._toggle_calendar,
            corner_radius=10
        )
        self.calendar_btn.pack(side="right", padx=4, pady=4)
        
        # Botão de limpar (inicialmente oculto)
        self.clear_btn = ctk.CTkButton(
            self.input_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=("#FEE2E2", "#7F1D1D"),
            text_color=("#EF4444", "#F87171"),
            font=ctk.CTkFont(size=16),
            command=self._clear_date,
            corner_radius=8
        )
        
        # Bind para efeitos de hover
        self.input_frame.bind("<Enter>", self._on_hover)
        self.input_frame.bind("<Leave>", self._on_leave)
        self.entry.bind("<Button-1>", lambda e: self._toggle_calendar())
    
    def _on_hover(self, event):
        """Efeito ao passar o mouse"""
        self.input_frame.configure(border_color="#979da2")
    
    def _on_leave(self, event):
        """Efeito ao sair com o mouse"""
        self.input_frame.configure(border_color="#979da2")
    
    def _toggle_calendar(self):
        """Abre ou fecha o calendário"""
        if self.calendar_window and self.calendar_window.winfo_exists():
            self.calendar_window.destroy()
            self.calendar_window = None
        else:
            self._open_calendar()
    
    def _open_calendar(self):
        """Abre o calendário estilizado"""
        if self.calendar_window and self.calendar_window.winfo_exists():
            return
        
        self.current_date = self.selected_date if self.selected_date else datetime.now()
        
        # Criar janela do calendário
        self.calendar_window = ctk.CTkToplevel(self)
        self.calendar_window.title("")
        self.calendar_window.geometry("360x480")
        self.calendar_window.resizable(False, False)
        self.calendar_window.transient(self)
        
        # Remover decorações da janela
        self.calendar_window.overrideredirect(True)
        
        # Posicionar abaixo do campo
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 5
        self.calendar_window.geometry(f"+{x}+{y}")
        
        # Container principal com sombra
        main_container = ctk.CTkFrame(
            self.calendar_window,
            fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=16,
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        main_container.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Header com navegação
        self._create_calendar_header(main_container)
        
        # Dias da semana
        self._create_weekdays_header(main_container)
        
        # Grid de dias
        self.days_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=16, pady=8)
        
        # Footer com botão Hoje
        self._create_calendar_footer(main_container)
        
        # Atualizar calendário
        self._update_calendar()
        
        # Fechar ao clicar fora
        self.calendar_window.bind("<FocusOut>", lambda e: self.calendar_window.destroy())
    
    def _create_calendar_header(self, parent):
        """Cria o cabeçalho do calendário"""
        header = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        header.pack(fill="x", padx=16, pady=(16, 10))
        header.pack_propagate(False)
        
        # Botão ano anterior
        ctk.CTkButton(
            header,
            text="⟨⟨",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=("#F1F5F9", "#334155"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._previous_year,
            corner_radius=10
        ).pack(side="left", padx=2)
        
        # Botão mês anterior
        ctk.CTkButton(
            header,
            text="⟨",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=("#F1F5F9", "#334155"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._previous_month,
            corner_radius=10
        ).pack(side="left", padx=2)
        
        # Label do mês/ano
        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.month_label.pack(side="left", expand=True)
        
        # Botão próximo mês
        ctk.CTkButton(
            header,
            text="⟩",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=("#F1F5F9", "#334155"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._next_month,
            corner_radius=10
        ).pack(side="right", padx=2)
        
        # Botão próximo ano
        ctk.CTkButton(
            header,
            text="⟩⟩",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=("#F1F5F9", "#334155"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._next_year,
            corner_radius=10
        ).pack(side="right", padx=2)
    
    def _create_weekdays_header(self, parent):
        """Cria o cabeçalho dos dias da semana"""
        weekdays_frame = ctk.CTkFrame(parent, fg_color="transparent")
        weekdays_frame.pack(fill="x", padx=16, pady=(0, 5))
        
        weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        
        for i, day in enumerate(weekdays):
            is_weekend = i == 0 or i == 6
            color = ("#EF4444", "#F87171") if is_weekend else ("#64748B", "#94A3B8")
            
            label = ctk.CTkLabel(
                weekdays_frame,
                text=day,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color,
                width=40
            )
            label.grid(row=0, column=i, padx=2, pady=8)
    
    def _create_calendar_footer(self, parent):
        """Cria o rodapé do calendário"""
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(10, 16))
        
        ctk.CTkButton(
            footer,
            text="Hoje",
            height=36,
            fg_color=("#3B82F6", "#2563EB"),
            hover_color=("#2563EB", "#1D4ED8"),
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10,
            command=self._select_today
        ).pack(fill="x")
    
    def _update_calendar(self):
        """Atualiza o calendário com os dias do mês"""
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        self.month_label.configure(
            text=f"{months[self.current_date.month - 1]} {self.current_date.year}"
        )
        
        # Limpar dias anteriores
        for widget in self.days_frame.winfo_children():
            widget.destroy()
        
        # Calcular dias
        first_day = self.current_date.replace(day=1)
        start_weekday = first_day.weekday()
        start_weekday = (start_weekday + 1) % 7  # Ajustar para domingo = 0
        
        days_in_month = (self.current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        total_days = days_in_month.day
        
        # Configurar grid
        for i in range(7):
            self.days_frame.grid_columnconfigure(i, weight=1, uniform="col")
        for i in range(6):
            self.days_frame.grid_rowconfigure(i, weight=1, uniform="row")
        
        # Criar botões dos dias
        today = datetime.now().date()
        
        row = 0
        col = start_weekday
        
        for day in range(1, total_days + 1):
            current = self.current_date.replace(day=day)
            is_today = current.date() == today
            is_selected = self.selected_date and current.date() == self.selected_date.date()
            is_weekend = col == 0 or col == 6
            
            # Cores
            if is_selected:
                fg_color = ("#3B82F6", "#2563EB")
                hover_color = ("#2563EB", "#1D4ED8")
                text_color = "#FFFFFF"
            elif is_today:
                fg_color = "transparent"
                hover_color = ("#DBEAFE", "#1E3A8A")
                text_color = ("#3B82F6", "#60A5FA")
            else:
                fg_color = "transparent"
                hover_color = ("#F1F5F9", "#334155")
                text_color = ("#EF4444", "#F87171") if is_weekend else ("#64748B", "#94A3B8")
            
            btn = ctk.CTkButton(
                self.days_frame,
                text=str(day),
                width=40,
                height=40,
                fg_color=fg_color,
                hover_color=hover_color,
                text_color=text_color,
                font=ctk.CTkFont(size=14, weight="bold" if is_today or is_selected else "normal"),
                corner_radius=10,
                border_width=2 if is_today and not is_selected else 0,
                border_color=("#3B82F6", "#60A5FA"),
                command=lambda d=current: self._select_date(d)
            )
            
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            col += 1
            if col > 6:
                col = 0
                row += 1
    
    def _previous_month(self):
        """Mês anterior"""
        self.current_date = (self.current_date.replace(day=1) - timedelta(days=1))
        self._update_calendar()
    
    def _next_month(self):
        """Próximo mês"""
        next_month = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = next_month.replace(day=1)
        self._update_calendar()
    
    def _previous_year(self):
        """Ano anterior"""
        self.current_date = self.current_date.replace(year=self.current_date.year - 1)
        self._update_calendar()
    
    def _next_year(self):
        """Próximo ano"""
        self.current_date = self.current_date.replace(year=self.current_date.year + 1)
        self._update_calendar()
    
    def _select_today(self):
        """Seleciona hoje"""
        self._select_date(datetime.now())
    
    def _select_date(self, date):
        """Seleciona uma data"""
        self.selected_date = date
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, date.strftime(self.date_format))
        self.entry.configure(state="readonly")
        
        # Mostrar botão de limpar
        self.clear_btn.pack(side="right", padx=4, pady=4, before=self.calendar_btn)
        
        # Fechar calendário
        if self.calendar_window:
            self.calendar_window.destroy()
            self.calendar_window = None
        
        # Callback
        if self.on_date_selected:
            self.on_date_selected(date)
    
    def _clear_date(self):
        """Limpa a data selecionada"""
        self.selected_date = None
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.configure(state="readonly")
        self.clear_btn.pack_forget()
    
    def get_date(self):
        """Retorna a data selecionada"""
        return self.selected_date
    
    def set_date(self, date):
        """Define a data"""
        if isinstance(date, datetime):
            self._select_date(date)
        """Define a data"""
        if isinstance(date, datetime):
            self._select_date(date)

# ====================================================================================
# INTERFACE GRÁFICA - TELA DE LOGIN
# ====================================================================================

class TelaLogin:
    """Tela de login"""
    
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = SistemaAutenticacao()
        
        self.root.title("Sistema de Controle de Qualidade - Login")
        self.root.geometry("500x600")
        self.root.minsize(500, 600)
        self.root.resizable(False, False)
        self.centralizar_janela()
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.frame = ctk.CTkFrame(root, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.criar_interface()
    
    def centralizar_janela(self):
        """Centraliza janela"""
        self.root.update_idletasks()
        width, height = 500, 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def criar_interface(self):
        """Cria interface de login"""
        container = ctk.CTkFrame(self.frame, width=460, height=560, fg_color="#1f538d", corner_radius=15)
        container.pack(pady=20, padx=20, fill="both", expand=True)
        container.pack_propagate(False)
        
        ctk.CTkLabel(container, text="🏭", font=ctk.CTkFont(size=80), text_color="white").pack(pady=(40, 10))
        ctk.CTkLabel(container, text="Sistema de Controle\nde Qualidade Industrial", 
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
        
        ctk.CTkLabel(form_frame, text="Usuário padrão: admin\nSenha: admin", font=ctk.CTkFont(size=12), 
                     text_color="#666666", justify="center").pack(pady=(10, 20))
        
        ctk.CTkLabel(container, text="v3.1.1 - Menu Corrigido + Date Picker", font=ctk.CTkFont(size=10), text_color="#e0e0e0").pack(pady=10)
    
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

# ====================================================================================
# INTERFACE GRÁFICA - TELA PRINCIPAL (CORRIGIDA)
# ====================================================================================

class TelaPrincipal:
    """Tela principal do sistema - CORRIGIDA COM MENU FUNCIONAL"""
    
    def __init__(self, root, usuario: str, info_usuario: Dict):
        self.root = root
        self.usuario = usuario
        self.info_usuario = info_usuario
        self.db = BancoDados()
        self.auth = SistemaAutenticacao()
        
        self.root.title(f"Sistema de Controle de Qualidade - {info_usuario['nome_completo']}")
        self.root.geometry("1200x800")
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
            TelaLogin(self.root, lambda u, i: TelaPrincipal(self.root, u, i))
    
    def criar_menu_principal(self):
        """Cria menu principal - LAYOUT CORRIGIDO COM SCROLL"""
        self.resetar_timeout()
        self.limpar_tela()
        
        # Header
        header = ctk.CTkFrame(self.frame_principal, fg_color="#1f538d", height=80, corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        titulo_frame = ctk.CTkFrame(header, fg_color="transparent")
        titulo_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(titulo_frame, text="🏭 Sistema de Controle de Qualidade Industrial", 
                     font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(titulo_frame, text="QTools - Versão 3.1.1", 
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
        """Cria menu de opções com scroll - LAYOUT OTIMIZADO"""
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
        """Tela de cadastro de peça - IMPLEMENTADA"""
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
                
                peca = Peca(id_peca, peso, cor, comprimento, self.usuario)
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
        """Tela de listagem com filtros"""
        self.resetar_timeout()
        self.limpar_tela()
        self.criar_header("📋 Listar Peças")
        
        main_frame = ctk.CTkFrame(self.frame_principal)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Filtros
        # filtro_frame = ctk.CTkFrame(main_frame)
        # filtro_frame.pack(fill="x", padx=10, pady=10)
        
        # ctk.CTkLabel(filtro_frame, text="📅 Filtrar por período:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        
        # combo_periodo = ctk.CTkComboBox(filtro_frame, width=140, 
        #                                values=["Todos", "Hoje", "Ontem", "Última Semana", "Último Mês", "Personalizado"])
        # combo_periodo.set("Todos")
        # combo_periodo.pack(side="left", padx=5)
        
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
        
        def aplicar_filtro():
            self.resetar_timeout()
            dt = self.entry_data_min.get_date()
            dt2 = self.entry_data_max.get_date()
            data_inicio = datetime.date(dt)
            data_fim = datetime.date(dt2)
            # periodo = combo_periodo.get()
            atualizar_listas(data_inicio, data_fim)
        
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
    
    def criar_lista_pecas(self, parent, pecas: List[Peca], tipo: str):
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
            
            # Botão remover (apenas admin/supervisor) - rodrigow
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
    
    @requer_permissao('supervisor')
    def tela_remover_peca(self):
        """Tela de remoção de peça - IMPLEMENTADA"""
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
        """Tela de listagem de caixas - IMPLEMENTADA"""
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
    
    @requer_permissao('administrador')
    def tela_gerenciar_pecas(self):
        """NOVA TELA: Gerenciamento CRUD de peças - IMPLEMENTADA"""
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
    
    def mostrar_formulario_edicao(self, peca: Peca, form_frame: ctk.CTkFrame):
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
    
    @requer_permissao('administrador')
    def tela_relatorios_avancados(self):
        """Tela de relatórios avançados com Date Picker - IMPLEMENTADA"""
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
                sucesso, msg = GeradorRelatoriosPDF.gerar_relatorio_executivo(relatorio, caminho, self.usuario)
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
        texto += "Relatório gerado automaticamente - Sistema de Controle de Qualidade v3.1.1\n"
        texto += "="*80 + "\n"
        
        return texto
    
    @requer_permissao('administrador')
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
    
    @requer_permissao('administrador')
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
                self.db.config['capacidade_caixa'] = int(entry_capacidade.get())
                self.db.config['auto_backup'] = var_backup.get()
                self.db.config['backup_interval_hours'] = int(entry_intervalo.get())
                self.db.config['timeout_sessao_minutos'] = int(entry_timeout.get())
                
                ConfiguracaoSistema.salvar_configuracao(self.db.config)
                ConfiguracaoSistema.registrar_auditoria(self.usuario, "ALTERAR_CONFIG", "Sistema")
                
                messagebox.showinfo("Sucesso", "Configurações salvas!")
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
        
        TelaLogin(self.root, self.on_login_success)
    
    def on_login_success(self, usuario: str, info_usuario: Dict):
        """Callback após login"""
        TelaPrincipal(self.root, usuario, info_usuario)
    
    def executar(self):
        """Executa aplicação"""
        self.root.mainloop()

# ====================================================================================
# PONTO DE ENTRADA
# ====================================================================================

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  🏭 Sistema de Controle de Qualidade Industrial v3.1.1")
    print("  📊 Menu Corrigido + Date Picker + Layout Otimizado")
    print("  ✨ Todos os menus funcionais com scroll")
    print("="*70 + "\n")
    
    print("🔧 Correções Implementadas:")
    print("  ✅ Todos os menus agora funcionam")
    print("  ✅ Layout com scroll para muitos botões")
    print("  ✅ Date Picker para seleção de datas")
    print("  ✅ Interface otimizada para caber na tela")
    print("  ✅ Métodos das telas completamente implementados")
    print("\n" + "="*70 + "\n")
    
    try:
        app = Aplicacao()
        app.executar()
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        messagebox.showerror("Erro Fatal", f"Erro crítico:\n\n{str(e)}")
    finally:
        ConfiguracaoSistema.registrar_log("Aplicação encerrada", "SISTEMA")

if __name__ == "__main__":
    main()