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
    
    # Crear mazos y convertir a listas
    player_deck_list = list(random_deck(all_cards))
    ai_deck_list = list(random_deck(all_cards))
    
    # Repartir mano inicial (5 cartas)
    HAND_SIZE = 5
    
    player_hand = Hand(cards=tuple(player_deck_list[:HAND_SIZE]))
    player_deck_tuple = tuple(player_deck_list[HAND_SIZE:]) 
    
    ai_hand = Hand(cards=tuple(ai_deck_list[:HAND_SIZE]))
    ai_deck_tuple = tuple(ai_deck_list[HAND_SIZE:]) 

    # Crear instancias de Player
    player = Player(name="Player 1", hand=player_hand, deck=player_deck_tuple)
    ai_player = Player(name="AI Opponent", hand=ai_hand, deck=ai_deck_tuple)

    print(f"Jugador: {player}")
    print(f"IA: {ai_player}")
    
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
    ai_controller = AIController(max_depth=3) 
    
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
    # Se añade un placeholder para AIController si aún no está implementado
    class AIController:
        def __init__(self, max_depth):
            print(f"AIController placeholder inicializado con profundidad {max_depth}.")
        def execute_ai_turn(self, state: GameState) -> GameState:
            print("IA: Robando carta y pasando turno (lógica real no implementada).")
            # Simplemente roba una carta y pasa para mantener el flujo de la simulación
            new_ai_player, _ = state.ai_player.draw_card()
            new_state = state.get_copy_with_players(state.player, new_ai_player)
            # El movimiento de PASS cambia la fase/turno
            pass_move = Move(action_type=ActionType.PASS, target_zone='turn')
            return new_state.apply_move(pass_move)
    
    main()