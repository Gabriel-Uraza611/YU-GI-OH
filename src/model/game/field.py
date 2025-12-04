from typing import List, Optional, Tuple
from cards.card import Card
from game.move import Position
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Field:
    """
    Representa la zona de monstruos de un jugador de manera inmutable.
    Contiene la carta y su posición en el slot.
    """
    
    MONSTER_SLOTS: int = 5

    # Cada slot guarda una tupla (Card, Position) o None
    monsters: Tuple[Optional[Tuple[Card, Position]], ...] = (None,) * MONSTER_SLOTS

    def get_card_at(self, index: int) -> Optional[Card]:
        """Devuelve la carta en un índice dado si existe."""
        if 0 <= index < self.MONSTER_SLOTS and self.monsters[index]:
            return self.monsters[index][0]
        return None

    def get_position_at(self, index: int) -> Optional[Position]:
        """Devuelve la posición de la carta en un índice dado."""
        if 0 <= index < self.MONSTER_SLOTS and self.monsters[index]:
            return self.monsters[index][1]
        return None

    def get_empty_slot_index(self) -> Optional[int]:
        """Devuelve el índice del primer slot de monstruo vacío."""
        try:
            return self.monsters.index(None)
        except ValueError:
            return None

    def place_monster(self, card: Card, index: int, position: Position) -> 'Field':
        """
        Retorna un nuevo Field con la carta colocada.
        """
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is None):
            raise ValueError("Slot de monstruo inválido o ya ocupado.")

        new_monsters_list = list(self.monsters)
        new_monsters_list[index] = (card, position)
        
        return replace(self, monsters=tuple(new_monsters_list))

    def remove_monster(self, index: int) -> Tuple['Field', Card]:
        """
        Retorna un nuevo Field con la carta eliminada y la carta retirada.
        """
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is not None):
            raise ValueError("Slot de monstruo inválido o vacío.")

        card_removed = self.monsters[index][0]
        new_monsters_list = list(self.monsters)
        new_monsters_list[index] = None
        
        return replace(self, monsters=tuple(new_monsters_list)), card_removed

    def change_monster_position(self, index: int, new_position: Position) -> 'Field':
        """
        Retorna un nuevo Field con la posición de la carta cambiada.
        """
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is not None):
            raise ValueError("Slot de monstruo inválido o vacío.")
            
        card, current_pos = self.monsters[index]
        
        new_monsters_list = list(self.monsters)
        new_monsters_list[index] = (card, new_position)
        
        return replace(self, monsters=tuple(new_monsters_list))

    def __repr__(self) -> str:
        monsters_info = [
            f"[{i}]: {m[0].name[:10]} ({m[1].name[5:]})" if m else f"[{i}]: Empty"
            for i, m in enumerate(self.monsters)
        ]
        return f"Field({', '.join(monsters_info)})"