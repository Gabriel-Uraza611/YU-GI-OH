from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

# --- Importaciones de dependencias ---
from model.cards.card import Card 
# Importamos solo el alias si la función es necesaria fuera de GameState
# Pero dado que GameState la importa directamente, la quitamos de aquí para evitar confusiones
# La función get_fusion_result está correctamente definida en model.fusions.fusion_recipe

# --- Enumeraciones para mejorar la claridad de la lógica ---

class ActionType(Enum):
    """Define los tipos de acciones posibles en el juego."""
    SUMMON = auto()         # Invocación normal 
    SET = auto()            # Colocar en defensa
    ATTACK = auto()         # Atacar a carta o LP
    CHANGE_POSITION = auto()# Cambiar de modo (ATK <-> DEF)
    FUSION_SUMMON = auto()  # Invocación por fusión
    PASS = auto()           # Pasar de fase o de turno

class Position(Enum):
    """Define las posiciones posibles de una carta en el campo."""
    FACE_UP_ATK = auto()
    FACE_UP_DEF = auto()

@dataclass(frozen=True)
class Move:
    """
    Representa una acción atómica que un jugador puede realizar.
    Es la unidad fundamental de búsqueda del algoritmo MiniMax.
    """
    
    # Tipo de Acción (OBLIGATORIO)
    action_type: ActionType
    
    # ID de la carta principal involucrada (se usa para SUMMON/FUSION)
    card_id: str = field(default="")
    
    # --- Slots y Posiciones ---
    
    # Zonas de Origen y Destino (ej: 'hand', 'field', 'deck', etc.)
    source_zone: str = field(default="") 
    target_zone: str = field(default="") # Usado para PASS: 'main', 'battle', 'end', 'change_turn'
    
    # Índices específicos dentro de la Zona (ej: ranura 2 de la mano o campo)
    source_index: Optional[int] = field(default=None)
    target_index: Optional[int] = field(default=None)
    
    # Posición resultante si es SUMMON/SET/CHANGE_POSITION
    position: Optional[Position] = field(default=None)
    
    # --- Específico para Acciones Complejas ---
    
    # Para Fusiones
    fusion_materials_indices: Tuple[int, ...] = field(default_factory=tuple) # Índices de materiales en la mano
    
    
    def __repr__(self):
        """Representación legible del movimiento para depuración y logs."""
        
        if self.action_type in (ActionType.SUMMON, ActionType.SET):
            action = "SUMMON" if self.action_type == ActionType.SUMMON else "SET"
            pos = self.position.name if self.position else "???"
            
            return f"{action}({self.card_id} from {self.source_zone}[{self.source_index}] to Field[{self.target_index}] in {pos})"
        
        elif self.action_type == ActionType.ATTACK:
            # target_index se refiere al slot del oponente (0-4) o -1 para ataque directo a LP
            target = f"OPPONENT_SLOT[{self.target_index}]" if self.target_index != -1 else "OPPONENT_LP"
            return f"ATTACK (Slot{self.source_index} -> {target})"
        
        elif self.action_type == ActionType.FUSION_SUMMON:
            mats = f"Materials from indices {self.fusion_materials_indices}"
            return f"FUSION_SUMMON({self.card_id} using {mats} to Field[{self.target_index}])"
            
        elif self.action_type == ActionType.PASS:
            return f"PASS to {self.target_zone.upper()} phase/turn"
            
        elif self.action_type == ActionType.CHANGE_POSITION:
            pos = self.position.name if self.position else "???"
            return f"CHANGE_POSITION (Slot{self.source_index} to {pos})"
            
        else:
             return f"MOVE(Type: {self.action_type.name}, Target: {self.target_zone})"