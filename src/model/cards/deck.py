"""
Creador de mazos aleatorios a partir de un conjunto de cartas disponibles.
"""

import numpy as np

def random_deck(all_cards: dict) -> np.ndarray:
    '''
    Crea un mazo de cartas seleccionando aleatoriamente 40 cartas del conjunto
    de cartas disponibles.

    Args:
        all_cards: Diccionario con todas las cartas disponibles, clave: número de carta

    Returns:
        list: Lista con las cartas seleccionadas para el mazo
    '''

    deck_size = 30
    card_array = np.array(list(all_cards.values()))
    deck = np.random.choice(
        a=card_array,        # Población (el array de todas las cartas)
        size=deck_size,      # Cantidad a seleccionar (40)
        replace=False        # ¡Sin reemplazo!
    )
    return deck
