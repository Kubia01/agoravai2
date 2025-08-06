import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class EditorTheme:
    """Configurações de tema do editor"""
    primary_color: str = "#3b82f6"
    secondary_color: str = "#10b981"
    error_color: str = "#ef4444"
    warning_color: str = "#f59e0b"
    background_color: str = "#f8fafc"
    canvas_background: str = "#ffffff"
    grid_color: str = "#e5e7eb"
    selection_color: str = "#3b82f6"
    selection_multiple_color: str = "#ef4444"
    text_color: str = "#1f2937"
    text_muted_color: str = "#6b7280"

@dataclass
class GridSettings:
    """Configurações da grade"""
    enabled: bool = True
    size: int = 20
    snap_to_grid: bool = True
    show_grid: bool = True
    color: str = "#f0f0f0"
    major_line_interval: int = 5
    major_line_color: str = "#d1d5db"

@dataclass
class CanvasSettings:
    """Configurações do canvas"""
    scale: float = 0.8
    page_width: int = 595  # A4
    page_height: int = 842  # A4
    margin_left: int = 72
    margin_right: int = 72
    margin_top: int = 72
    margin_bottom: int = 72
    show_margins: bool = True
    margin_color: str = "#fca5a5"

@dataclass
class ElementDefaults:
    """Configurações padrão para elementos"""
    text_font_family: str = "Arial"
    text_font_size: int = 12
    text_color: str = "#000000"
    text_bold: bool = False
    text_italic: bool = False
    text_align: str = "left"
    
    image_width: int = 100
    image_height: int = 100
    
    table_rows: int = 3
    table_cols: int = 3
    table_header_bg: str = "#e5e7eb"
    table_cell_bg: str = "#ffffff"
    table_border_color: str = "#374151"
    
    line_length: int = 100
    line_thickness: int = 1
    line_color: str = "#000000"
    
    rectangle_width: int = 100
    rectangle_height: int = 50
    rectangle_fill_color: str = ""
    rectangle_border_color: str = "#000000"
    rectangle_border_width: int = 1

@dataclass
class AutoSaveSettings:
    """Configurações de salvamento automático"""
    enabled: bool = True
    interval_minutes: int = 5
    max_backups: int = 10
    backup_directory: str = "data/auto_backups"

@dataclass
class ValidationSettings:
    """Configurações de validação"""
    warn_empty_pages: bool = True
    warn_overlapping_elements: bool = True
    warn_elements_outside_margins: bool = True
    warn_missing_dynamic_data: bool = True
    auto_fix_positions: bool = False

@dataclass
class PerformanceSettings:
    """Configurações de performance"""
    max_undo_steps: int = 50
    render_quality: str = "medium"  # low, medium, high
    lazy_loading: bool = True
    cache_previews: bool = True
    preview_update_delay_ms: int = 1500

@dataclass
class EditorConfig:
    """Configuração completa do editor"""
    theme: EditorTheme
    grid: GridSettings
    canvas: CanvasSettings
    element_defaults: ElementDefaults
    auto_save: AutoSaveSettings
    validation: ValidationSettings
    performance: PerformanceSettings
    
    # Configurações gerais
    user_id: Optional[int] = None
    language: str = "pt_BR"
    show_tooltips: bool = True
    confirm_destructive_actions: bool = True
    recent_templates_count: int = 10
    
    # Configurações avançadas
    developer_mode: bool = False
    debug_mode: bool = False
    experimental_features: bool = False

class EditorConfigManager:
    """Gerenciador de configurações do editor"""
    
    def __init__(self, config_file: str = "data/editor_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
        # Criar diretório de configuração se não existir
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    def load_config(self) -> EditorConfig:
        """Carregar configurações do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Converter para objetos dataclass
                theme = EditorTheme(**data.get('theme', {}))
                grid = GridSettings(**data.get('grid', {}))
                canvas = CanvasSettings(**data.get('canvas', {}))
                element_defaults = ElementDefaults(**data.get('element_defaults', {}))
                auto_save = AutoSaveSettings(**data.get('auto_save', {}))
                validation = ValidationSettings(**data.get('validation', {}))
                performance = PerformanceSettings(**data.get('performance', {}))
                
                # Configurações gerais
                general = data.get('general', {})
                
                config = EditorConfig(
                    theme=theme,
                    grid=grid,
                    canvas=canvas,
                    element_defaults=element_defaults,
                    auto_save=auto_save,
                    validation=validation,
                    performance=performance,
                    user_id=general.get('user_id'),
                    language=general.get('language', 'pt_BR'),
                    show_tooltips=general.get('show_tooltips', True),
                    confirm_destructive_actions=general.get('confirm_destructive_actions', True),
                    recent_templates_count=general.get('recent_templates_count', 10),
                    developer_mode=general.get('developer_mode', False),
                    debug_mode=general.get('debug_mode', False),
                    experimental_features=general.get('experimental_features', False)
                )
                
                return config
            else:
                # Criar configuração padrão
                return self.create_default_config()
                
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return self.create_default_config()
    
    def create_default_config(self) -> EditorConfig:
        """Criar configuração padrão"""
        return EditorConfig(
            theme=EditorTheme(),
            grid=GridSettings(),
            canvas=CanvasSettings(),
            element_defaults=ElementDefaults(),
            auto_save=AutoSaveSettings(),
            validation=ValidationSettings(),
            performance=PerformanceSettings()
        )
    
    def save_config(self) -> bool:
        """Salvar configurações no arquivo"""
        try:
            # Converter para dicionário
            config_dict = {
                'theme': asdict(self.config.theme),
                'grid': asdict(self.config.grid),
                'canvas': asdict(self.config.canvas),
                'element_defaults': asdict(self.config.element_defaults),
                'auto_save': asdict(self.config.auto_save),
                'validation': asdict(self.config.validation),
                'performance': asdict(self.config.performance),
                'general': {
                    'user_id': self.config.user_id,
                    'language': self.config.language,
                    'show_tooltips': self.config.show_tooltips,
                    'confirm_destructive_actions': self.config.confirm_destructive_actions,
                    'recent_templates_count': self.config.recent_templates_count,
                    'developer_mode': self.config.developer_mode,
                    'debug_mode': self.config.debug_mode,
                    'experimental_features': self.config.experimental_features
                },
                'meta': {
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'config_manager_version': '1.0'
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Configurações salvas: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """Atualizar configurações específicas"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                elif '.' in key:
                    # Suporte para notação de ponto (ex: theme.primary_color)
                    parts = key.split('.')
                    obj = self.config
                    for part in parts[:-1]:
                        obj = getattr(obj, part)
                    setattr(obj, parts[-1], value)
            
            return self.save_config()
            
        except Exception as e:
            print(f"Erro ao atualizar configurações: {e}")
            return False
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Obter cores do tema atual"""
        return asdict(self.config.theme)
    
    def get_grid_settings(self) -> Dict[str, Any]:
        """Obter configurações da grade"""
        return asdict(self.config.grid)
    
    def get_canvas_settings(self) -> Dict[str, Any]:
        """Obter configurações do canvas"""
        return asdict(self.config.canvas)
    
    def get_element_defaults(self, element_type: str) -> Dict[str, Any]:
        """Obter configurações padrão para um tipo de elemento"""
        defaults = asdict(self.config.element_defaults)
        
        # Filtrar por tipo de elemento
        if element_type == 'text':
            return {k: v for k, v in defaults.items() if k.startswith('text_')}
        elif element_type == 'image':
            return {k: v for k, v in defaults.items() if k.startswith('image_')}
        elif element_type == 'table':
            return {k: v for k, v in defaults.items() if k.startswith('table_')}
        elif element_type == 'line':
            return {k: v for k, v in defaults.items() if k.startswith('line_')}
        elif element_type == 'rectangle':
            return {k: v for k, v in defaults.items() if k.startswith('rectangle_')}
        
        return defaults
    
    def create_user_config(self, user_id: int) -> bool:
        """Criar configuração específica para um usuário"""
        try:
            user_config_file = f"data/user_configs/user_{user_id}_config.json"
            
            # Criar cópia da configuração padrão
            user_config = self.create_default_config()
            user_config.user_id = user_id
            
            # Salvar configuração do usuário
            temp_config_file = self.config_file
            self.config_file = user_config_file
            self.config = user_config
            
            os.makedirs(os.path.dirname(user_config_file), exist_ok=True)
            result = self.save_config()
            
            # Restaurar configuração original
            self.config_file = temp_config_file
            
            return result
            
        except Exception as e:
            print(f"Erro ao criar configuração do usuário: {e}")
            return False
    
    def load_user_config(self, user_id: int) -> bool:
        """Carregar configuração específica de um usuário"""
        try:
            user_config_file = f"data/user_configs/user_{user_id}_config.json"
            
            if os.path.exists(user_config_file):
                temp_config_file = self.config_file
                self.config_file = user_config_file
                self.config = self.load_config()
                self.config_file = temp_config_file
                return True
            else:
                # Criar configuração para o usuário se não existir
                return self.create_user_config(user_id)
                
        except Exception as e:
            print(f"Erro ao carregar configuração do usuário: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Resetar para configurações padrão"""
        try:
            self.config = self.create_default_config()
            return self.save_config()
        except Exception as e:
            print(f"Erro ao resetar configurações: {e}")
            return False
    
    def export_config(self, filepath: str) -> bool:
        """Exportar configurações para arquivo"""
        try:
            temp_config_file = self.config_file
            self.config_file = filepath
            result = self.save_config()
            self.config_file = temp_config_file
            return result
        except Exception as e:
            print(f"Erro ao exportar configurações: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """Importar configurações de arquivo"""
        try:
            if os.path.exists(filepath):
                temp_config_file = self.config_file
                self.config_file = filepath
                self.config = self.load_config()
                self.config_file = temp_config_file
                return self.save_config()
            return False
        except Exception as e:
            print(f"Erro ao importar configurações: {e}")
            return False
    
    def get_validation_rules(self) -> List[str]:
        """Obter regras de validação ativas"""
        rules = []
        validation = self.config.validation
        
        if validation.warn_empty_pages:
            rules.append("warn_empty_pages")
        if validation.warn_overlapping_elements:
            rules.append("warn_overlapping_elements")
        if validation.warn_elements_outside_margins:
            rules.append("warn_elements_outside_margins")
        if validation.warn_missing_dynamic_data:
            rules.append("warn_missing_dynamic_data")
        
        return rules
    
    def should_auto_save(self) -> bool:
        """Verificar se auto-save está habilitado"""
        return self.config.auto_save.enabled
    
    def get_auto_save_interval(self) -> int:
        """Obter intervalo de auto-save em minutos"""
        return self.config.auto_save.interval_minutes
    
    def is_developer_mode(self) -> bool:
        """Verificar se modo desenvolvedor está ativo"""
        return self.config.developer_mode
    
    def is_debug_mode(self) -> bool:
        """Verificar se modo debug está ativo"""
        return self.config.debug_mode
    
    def has_experimental_features(self) -> bool:
        """Verificar se funcionalidades experimentais estão habilitadas"""
        return self.config.experimental_features

# Instância global do gerenciador de configurações
_config_manager = None

def get_config_manager() -> EditorConfigManager:
    """Obter instância global do gerenciador de configurações"""
    global _config_manager
    if _config_manager is None:
        _config_manager = EditorConfigManager()
    return _config_manager

def get_config() -> EditorConfig:
    """Obter configuração atual"""
    return get_config_manager().config

def update_config(**kwargs) -> bool:
    """Atualizar configurações"""
    return get_config_manager().update_config(**kwargs)

def save_config() -> bool:
    """Salvar configurações"""
    return get_config_manager().save_config()

def reset_config() -> bool:
    """Resetar configurações para padrão"""
    return get_config_manager().reset_to_defaults()

# Configurações pré-definidas para diferentes temas
THEMES = {
    'default': EditorTheme(),
    'dark': EditorTheme(
        primary_color="#60a5fa",
        secondary_color="#34d399",
        background_color="#1f2937",
        canvas_background="#374151",
        text_color="#f9fafb",
        text_muted_color="#9ca3af"
    ),
    'high_contrast': EditorTheme(
        primary_color="#000000",
        secondary_color="#ffffff",
        background_color="#ffffff",
        canvas_background="#ffffff",
        text_color="#000000",
        selection_color="#000000"
    ),
    'colorful': EditorTheme(
        primary_color="#8b5cf6",
        secondary_color="#f59e0b",
        error_color="#ec4899",
        warning_color="#06b6d4",
        background_color="#fef3c7"
    )
}

def apply_theme(theme_name: str) -> bool:
    """Aplicar tema pré-definido"""
    if theme_name in THEMES:
        return update_config(theme=THEMES[theme_name])
    return False