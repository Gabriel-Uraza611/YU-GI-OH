from typing import Tuple, Optional
from model.game.gamestate import GameState
from model.game.move import Move

# --- Parámetros de Configuración del Algoritmo ---
# Se pueden ajustar la profundidad y los valores de infinito según el rendimiento deseado.
MAX_DEPTH = 3  
INF = float('inf')

def find_best_move(initial_state: GameState, depth: int = MAX_DEPTH) -> Optional[Move]:
    """
    Función principal para encontrar el mejor movimiento utilizando MiniMax 
    con poda Alpha-Beta.
    
    Args:
        initial_state: El estado actual del juego.
        depth: Profundidad máxima de búsqueda.
        
    Returns:
        El mejor objeto Move encontrado para la IA, o None si no hay movimientos.
    """
    
    # El turno actual en este punto siempre será la IA ('ai')
    
    best_value = -INF
    best_move: Optional[Move] = None
    
    # Generar todos los movimientos posibles desde el estado inicial
    possible_moves = initial_state.get_possible_moves()
    
    if not possible_moves:
        return None

    # Iterar sobre los movimientos, aplicando MiniMax
    # Usamos alpha = -INF y beta = INF para el llamado inicial
    for move in possible_moves:
        
        # 1. Aplicar el movimiento para obtener el nuevo estado (Estado sucesor)
        next_state = initial_state.apply_move(move)
        
        # 2. Llamar a la función minimax_value (para el MIN player, que es el oponente)
        # La poda se inicia con alpha = best_value (el máximo encontrado hasta ahora)
        # y beta = INF (no hay límite superior para el oponente aún)
        value = minimax_value(
            state=next_state,
            depth=depth - 1, # Reducir la profundidad
            alpha=best_value, 
            beta=INF,
            is_maximizing_player=False # El siguiente jugador es el MIN player
        )
        
        # 3. Actualizar el mejor movimiento si el valor es superior
        if value > best_value:
            best_value = value
            best_move = move
            
    # print(f"MiniMax ha terminado. Mejor Valor: {best_value}, Mejor Movimiento: {best_move}")
    return best_move


def minimax_value(
    state: GameState, 
    depth: int, 
    alpha: float, 
    beta: float, 
    is_maximizing_player: bool
) -> float:
    """
    Implementación recursiva de MiniMax con poda Alpha-Beta.
    
    Args:
        state: El estado actual a evaluar.
        depth: Profundidad restante.
        alpha: El mejor valor encontrado para el MAX player (IA).
        beta: El mejor valor encontrado para el MIN player (Oponente).
        is_maximizing_player: True si es el turno de la IA (MAX), False si es del oponente (MIN).
        
    Returns:
        El valor heurístico del estado.
    """
    
    # --- 1. Caso Base: El juego terminó o se alcanzó la profundidad máxima ---
    if depth == 0 or state.is_game_over():
        # Retornar la evaluación heurística del estado
        # La función state.evaluate() ya está orientada a la IA (MAX player)
        return state.evaluate()

    # --- 2. Generar Movimientos ---
    possible_moves = state.get_possible_moves()
    
    # Caso Base Adicional: No hay movimientos legales (ej: Deck Out si se implementa, o fin de fase)
    if not possible_moves:
        # En este caso, simplemente evaluamos el estado actual
        return state.evaluate()

    # --- 3. Búsqueda (Maximización o Minimización) ---
    
    if is_maximizing_player:
        # Turno de la IA (MAX player)
        max_eval = -INF
        for move in possible_moves:
            next_state = state.apply_move(move)
            
            # Llamada recursiva: el siguiente es el MIN player
            eval_value = minimax_value(next_state, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_value)
            
            # Poda Alpha
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                # print("Poda Alpha activada.")
                break
        return max_eval

    else:
        # Turno del Oponente (MIN player)
        min_eval = INF
        for move in possible_moves:
            next_state = state.apply_move(move)
            
            # Llamada recursiva: el siguiente es el MAX player
            eval_value = minimax_value(next_state, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_value)
            
            # Poda Beta
            beta = min(beta, min_eval)
            if beta <= alpha:
                # print("Poda Beta activada.")
                break
        return min_eval