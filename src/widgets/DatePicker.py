import customtkinter as ctk
from datetime import datetime, timedelta

# ====================================================================================
# COMPONENTE: DATEPICKER
# ====================================================================================

class DatePicker(ctk.CTkFrame):
    """Campo de data com calendário moderno"""
    
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
            text="<<",
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
            text="<",
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
        
        # Botão próximo ano
        ctk.CTkButton(
            header,
            text=">>",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=("#F1F5F9", "#334155"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._next_year,
            corner_radius=10
        ).pack(side="right", padx=2) 
        
        # Botão próximo mês
        ctk.CTkButton(
            header,
            text=">",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=("#F1F5F9", "#334155"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._next_month,
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