from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================

class ConfiguracaoSistema:
    """Gerencia configurações e estrutura de pastas"""
    
    # BASE_DIR = Path(__file__).parent    
    BASE_DIR = Path("../").parent
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
