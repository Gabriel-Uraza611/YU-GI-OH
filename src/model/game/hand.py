from typing import List, Tuple, Optional
from model.cards.card import Card
from dataclasses import dataclass, replace, field

@dataclass(frozen=True)
class Hand:
    """
    Representa la mano de cartas de un jugador de manera inmutable.
    """
    cards: Tuple[Card, ...] = field(default_factory=tuple)

    def get_card_at(self, index: int) -> Optional[Card]:
        """Devuelve la carta en un índice dado si existe."""
        if 0 <= index < len(self.cards):
            return self.cards[index]
        return None

    def add_card(self, card: Card) -> 'Hand':
        """Retorna un nuevo Hand con una carta añadida."""
        return replace(self, cards=self.cards + (card,))

    def remove_card_at(self, index: int) -> Tuple['Hand', Card]:
        """
        Retorna un nuevo Hand con la carta eliminada y la carta retirada.
        """
        if not (0 <= index < len(self.cards)):
            raise IndexError("Índice de mano inválido.")

        card_removed = self.cards[index]
        new_cards_list = list(self.cards)
        new_cards_list.pop(index)
        
        return replace(self, cards=tuple(new_cards_list)), card_removed
        
    def __len__(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:
        return f"Hand(Cards: {len(self.cards)})"