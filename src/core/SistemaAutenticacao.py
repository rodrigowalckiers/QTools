from core.ConfiguracaoSistema import ConfiguracaoSistema
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import bcrypt

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