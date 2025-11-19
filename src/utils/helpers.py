from core.ConfiguracaoSistema import ConfiguracaoSistema
from tkinter import messagebox
from functools import wraps

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