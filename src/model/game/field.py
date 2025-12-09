from typing import Optional, Tuple
from model.cards.card import Card
from model.game.move import Position
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Field:
    """
    Representa la zona de monstruos de un jugador de manera inmutable.
    Cada slot guarda una tupla (Card, Position, has_attacked) o None.
    """

    MONSTER_SLOTS: int = 5

    monsters: Tuple[Optional[Tuple[Card, Position, bool]], ...] = (None,) * MONSTER_SLOTS

    def get_card_at(self, index: int) -> Optional[Card]:
        if 0 <= index < self.MONSTER_SLOTS and self.monsters[index]:
            return self.monsters[index][0]
        return None

    def get_position_at(self, index: int) -> Optional[Position]:
        if 0 <= index < self.MONSTER_SLOTS and self.monsters[index]:
            return self.monsters[index][1]
        return None

    def get_has_attacked_at(self, index: int) -> Optional[bool]:
        if 0 <= index < self.MONSTER_SLOTS and self.monsters[index]:
            return self.monsters[index][2]
        return None

    def get_empty_slot_index(self) -> Optional[int]:
        try:
            return self.monsters.index(None)
        except ValueError:
            return None

    def place_monster(self, card: Card, index: int, position: Position) -> 'Field':
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is None):
            raise ValueError("Slot de monstruo inválido o ya ocupado.")

        new_monsters_list = list(self.monsters)
        # When placing a monster, it hasn't attacked yet
        new_monsters_list[index] = (card, position, False)

        return replace(self, monsters=tuple(new_monsters_list))

    def remove_monster(self, index: int) -> Tuple['Field', Card]:
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is not None):
            raise ValueError("Slot de monstruo inválido o vacío.")

        card_removed = self.monsters[index][0]
        new_monsters_list = list(self.monsters)
        new_monsters_list[index] = None

        return replace(self, monsters=tuple(new_monsters_list)), card_removed

    def change_monster_position(self, index: int, new_position: Position) -> 'Field':
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is not None):
            raise ValueError("Slot de monstruo inválido o vacío.")

        card, current_pos, has_attacked = self.monsters[index]
        new_monsters_list = list(self.monsters)
        new_monsters_list[index] = (card, new_position, has_attacked)

        return replace(self, monsters=tuple(new_monsters_list))

    def mark_monster_attacked(self, index: int) -> 'Field':
        """Marca el monstruo del slot `index` como ya atacado."""
        if not (0 <= index < self.MONSTER_SLOTS and self.monsters[index] is not None):
            raise ValueError("Slot inválido o vacío para marcar ataque.")
        card, pos, _ = self.monsters[index]
        new_monsters_list = list(self.monsters)
        new_monsters_list[index] = (card, pos, True)
        return replace(self, monsters=tuple(new_monsters_list))

    def reset_attacks(self) -> 'Field':
        """Resetea el flag de ataque a False para todos los monstruos."""
        new_monsters_list = []
        for slot in self.monsters:
            if slot:
                card, pos, _ = slot
                new_monsters_list.append((card, pos, False))
            else:
                new_monsters_list.append(None)
        return replace(self, monsters=tuple(new_monsters_list))

    def __repr__(self) -> str:
        monsters_info = [
            f"[{i}]: {m[0].name[:10]} ({m[1].name[5:]}){'*' if m and m[2] else ''}" if m else f"[{i}]: Empty"
            for i, m in enumerate(self.monsters)
        ]
        return f"Field({', '.join(monsters_info)})"