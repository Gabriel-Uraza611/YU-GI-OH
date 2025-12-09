import numpy as np
from typing import Dict, List, Any

def random_deck(all_cards: Dict[str, Any], deck_size: int) -> List[Any]:
    '''
    Crea un mazo de cartas seleccionando aleatoriamente 'deck_size' cartas
    del conjunto de cartas disponibles.
    '''
    # === CORRECCIÓN CLAVE: deck_size viene del argumento, no es fijo ===
    rng = np.random.default_rng() 
    
    card_array = np.array(list(all_cards.values()))
    
    # Ajustar el tamaño si se pide más cartas de las disponibles
    size = min(deck_size, len(card_array))
    
    deck = rng.choice(
        a=card_array,
        size=size,           # Ahora usa el valor de 'deck_size' que recibe
        replace=False
    )
    
    return deck.tolist()