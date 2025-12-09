import os
import sys
import random
from typing import Dict, List, Any, Tuple

# Agregar src al path para que los imports funcionen desde cualquier lugar
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Carga de Cartas y Recetas
from model.cards.card import Card
from model.cards.card_loader import load_cards
from model.cards.deck import random_deck 
from model.fusions.fusion_recipe import FusionRecipe
from model.fusions.recipe_loader import load_recipes

# Clases del Juego
from model.game.gamestate import GameState
from model.game.player import Player
from model.game.hand import Hand
from model.game.field import Field
from model.game.move import Move, ActionType

# Lógica de la IA
from model.ai.ai_controller import AIController # Se asume que este archivo existe.

# CONTROLADOR: Iniciaremos el juego a través del controlador de Pygame
from controller.game_controller import GameController

# --- Configuración de Archivos ---
# Ruta base: proyecto raíz (YU-GI-OH/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARDS_FILE = os.path.join(BASE_DIR, 'data', 'cards.json')
RECIPES_FILE = os.path.join(BASE_DIR, 'data', 'recipies.json')

# --- Funciones de Inicialización ---

def initialize_game_data() -> Tuple[Dict[str, Card], List[FusionRecipe]]:
    """Carga las cartas y recetas del juego."""
    print("--- 1. Inicializando Datos del Juego ---")
    
    # Cargar todas las cartas
    all_cards = load_cards(CARDS_FILE)
    if not all_cards:
        raise Exception(f"No se pudieron cargar las cartas desde {CARDS_FILE}. Terminando.")
        
    # Cargar todas las recetas
    all_recipes = load_recipes(RECIPES_FILE)
    if not all_recipes:
        print(f"Advertencia: No se cargaron recetas desde {RECIPES_FILE}.")
    
    return all_cards, all_recipes

def initialize_players(all_cards: Dict[str, Card]) -> Tuple[Player, Player]:
    """
    Crea los mazos iniciales, baraja y reparte la mano inicial (5 cartas).
    """
    print("\n--- 2. Inicializando Jugadores y Mazos ---")
    
    DEFAULT_DECK_SIZE = 40 
    
    player_deck_list = random_deck(all_cards, deck_size=DEFAULT_DECK_SIZE)
    ai_deck_list = random_deck(all_cards, deck_size=DEFAULT_DECK_SIZE)
    

    player_deck_tuple = tuple(player_deck_list)
    ai_deck_tuple = tuple(ai_deck_list) 

    player = Player(name="Player 1", deck=player_deck_tuple)
    ai_player = Player(name="AI Opponent", deck=ai_deck_tuple)
    
    return player, ai_player

# NOTA: La función 'simulate_player_turn' ya NO es necesaria. Su lógica
# se moverá al GameController cuando manejemos el clic del botón 'PASS'.

def main():
    """Función principal para inicializar y lanzar la GUI de Pygame."""
    
    # 1. Cargar datos
    try:
        all_cards, all_recipes = initialize_game_data()
    except Exception as e:
        print(f"Error fatal en la inicialización: {e}")
        return

    # 2. Inicializar jugadores
    player_1, ai_player = initialize_players(all_cards)

    # 3. Inicializar GameState (el MODEL)
    initial_state = GameState(
        player=player_1, 
        ai_player=ai_player, 
        all_cards=all_cards, 
        all_recipes=all_recipes,
        current_turn='player' # Empieza el jugador humano
    )

    # 4. Inicializar el controlador de la IA
    ai_controller = AIController(depth=3) 
    
    # 5. Inicializar y lanzar el CONTROLADOR de Pygame
    print("\n\n######################################")
    print("# LANZANDO INTERFAZ GRÁFICA (Pygame) #")
    print("######################################\n")
    
    game_controller = GameController(
        initial_game_state=initial_state,
        ai_controller=ai_controller
    )
    game_controller.run() # Inicia el bucle principal de Pygame

if __name__ == '__main__':
    main()