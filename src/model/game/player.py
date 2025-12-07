from typing import List, Tuple, Optional
from cards.card import Card
from .hand import Hand
from .field import Field 
from dataclasses import dataclass, replace, field as dataclass_field

@dataclass(frozen=True)
class Player:
    """
    Representa a un jugador y todo su estado de juego de manera inmutable.
    Delega la gestión de cartas a Hand y Field.
    """
    
    name: str
    life_points: int = 8000
    
    # --- Delegación de Estado ---
    hand: Hand = dataclass_field(default_factory=Hand)
    field: Field = dataclass_field(default_factory=Field) 
    
    # Deck y Graveyard se mantienen inmutables con Tuplas
    deck: Tuple[Card, ...] = dataclass_field(default_factory=tuple)
    graveyard: Tuple[Card, ...] = dataclass_field(default_factory=tuple)
    
    can_normal_summon: bool = True # Flag para limitar 1 invocación normal por Main Phase
    
    def __repr__(self) -> str:
        # Nota: Usamos len(self.field) para simplificar la representación
        return (
            f"Player(Name: {self.name}, LP: {self.life_points}, "
            f"Deck: {len(self.deck)}, Hand: {len(self.hand)}, "
            f"Field: {len([m for m in self.field.monsters if m is not None])} Monsters)"
        )

    # --- Métodos de Copia Inmutable (para MiniMax/GameState) ---

    def draw_card(self) -> Tuple['Player', Optional[Card]]:
        """Retorna un nuevo Player con una carta robada del Deck a la Hand."""
        if not self.deck:
            return self, None 

        card_drawn = self.deck[0]
        new_deck = self.deck[1:]
        new_hand = self.hand.add_card(card_drawn)
        
        # Usamos replace() para crear el nuevo objeto inmutable
        return replace(self, deck=new_deck, hand=new_hand), card_drawn

    def send_card_to_graveyard(self, card: Card) -> 'Player':
        """Retorna un nuevo Player con la carta añadida al Graveyard."""
        new_graveyard = self.graveyard + (card,)
        return replace(self, graveyard=new_graveyard)

    def take_damage(self, damage: int) -> 'Player':
        """Retorna un nuevo Player con los Life Points reducidos."""
        new_lp = max(0, self.life_points - damage)
        return replace(self, life_points=new_lp)
        
    def gain_lp(self, lp: int) -> 'Player':
        """Retorna un nuevo Player con los Life Points incrementados."""
        new_lp = self.life_points + lp
        return replace(self, life_points=new_lp)

    def get_copy_with_field(self, new_field: Field) -> 'Player':
        """Retorna un nuevo Player con el campo (Field) actualizado."""
        return replace(self, field=new_field)

    def get_copy_with_hand(self, new_hand: Hand) -> 'Player':
        """Retorna un nuevo Player con la mano (Hand) actualizada."""
        return replace(self, hand=new_hand)

    def get_copy_with_summon_used(self, used: bool) -> 'Player':
        """Retorna un nuevo Player actualizando el flag de invocación."""
        # Se usa 'not used' para indicar si la próxima invocación *está disponible*
        return replace(self, can_normal_summon=not used)