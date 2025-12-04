from typing import Tuple, Optional, List
from model.game.gamestate import GameState
from model.game.move import Move, ActionType
from model.ai.minimax import find_best_move

class AIController:
    """
    Gestiona el turno completo de la IA, tomando decisiones fase por fase
    utilizando el algoritmo MiniMax.
    """

    def __init__(self, depth: int = 3):
        """Inicializa el controlador con la profundidad de búsqueda para MiniMax."""
        self.depth = depth

    def execute_ai_turn(self, initial_state: GameState) -> GameState:
        """
        Ejecuta el turno completo de la IA, desde la fase de Robar hasta la 
        fase Final, tomando decisiones en las fases Main y Battle.

        Args:
            initial_state: El GameState al comienzo del turno de la IA.

        Returns:
            El GameState final después de que la IA ha completado su turno.
        """
        
        current_state = initial_state

        # Asegurarse de que es el turno de la IA
        if current_state.current_turn != 'ai':
            print("ERROR: AIController llamado cuando no es el turno de la IA.")
            return current_state

        print(f"--- Turno de la IA iniciado ---")
        
        # 1. FASE DE ROBAR (Draw Phase)
        # En la fase de robar, solo hay un movimiento 'PASS' que aplica el robo y avanza a Main.
        if current_state.phase == 'draw':
            # Nota: El robo de carta se ejecuta en GameState.apply_move(PASS, change_turn) 
            # antes de que se establezca la fase 'draw'. Aquí solo pasamos a Main.
            
            draw_pass_move = next(
                (m for m in current_state.get_possible_moves() if m.action_type == ActionType.PASS and m.target_zone == 'main'), 
                None
            )
            if draw_pass_move:
                current_state = current_state.apply_move(draw_pass_move)
                print("AI: Transicionando a Main Phase.")
            else:
                print("Error: No se encontró movimiento de PASS en Draw Phase.")
                return current_state
        
        # 2. FASE PRINCIPAL (Main Phase) - Toma de decisiones
        if current_state.phase == 'main':
            print("AI: Ejecutando Main Phase (MiniMax Decision)...")
            
            while True:
                # La IA usa MiniMax para elegir el mejor movimiento en el estado actual
                best_move = find_best_move(current_state, depth=self.depth)

                if best_move is None:
                    print("AI: No hay movimientos de acción en Main Phase. Pasando a Battle.")
                    # Si no hay movimientos, forzamos la transición a Battle
                    pass_to_battle = Move(action_type=ActionType.PASS, target_zone='battle')
                    current_state = current_state.apply_move(pass_to_battle)
                    break 
                
                # Si el mejor movimiento es una transición de fase, ejecutarla y salir
                if best_move.action_type == ActionType.PASS:
                    if best_move.target_zone == 'battle':
                        print("AI: Transicionando a Battle Phase.")
                        current_state = current_state.apply_move(best_move)
                        break
                    elif best_move.target_zone == 'end':
                        print("AI: Transicionando directamente a End Phase.")
                        current_state = current_state.apply_move(best_move)
                        # Continúa la ejecución para entrar en la lógica de 'end'
                        break
                        
                # Si es un movimiento de acción (Summon, Fusion, etc.), ejecutar y re-evaluar
                print(f"AI: Ejecutando acción en Main Phase: {best_move}")
                current_state = current_state.apply_move(best_move)
                
                # Después de una acción, salir si el juego terminó
                if current_state.is_game_over():
                    print("Juego terminado durante Main Phase.")
                    return current_state
        
        # 3. FASE DE BATALLA (Battle Phase) - Toma de decisiones
        if current_state.phase == 'battle':
            print("AI: Ejecutando Battle Phase (MiniMax Decision)...")
            
            while True:
                # La IA toma una decisión en Battle Phase: Ataque o Pasar a End
                best_move = find_best_move(current_state, depth=self.depth)
                
                if best_move is None:
                    print("AI: No hay ataques disponibles. Pasando a End.")
                    # Si no hay movimientos, forzamos la transición a End
                    pass_to_end = Move(action_type=ActionType.PASS, target_zone='end')
                    current_state = current_state.apply_move(pass_to_end)
                    break 

                if best_move.action_type == ActionType.PASS and best_move.target_zone == 'end':
                    print("AI: Transicionando a End Phase.")
                    current_state = current_state.apply_move(best_move)
                    break 
                
                # Si es un ataque
                if best_move.action_type == ActionType.ATTACK:
                    print(f"AI: Ejecutando ataque en Battle Phase: {best_move}")
                    current_state = current_state.apply_move(best_move)
                
                else:
                    # Otros movimientos no deberían generarse en Battle Phase.
                    print(f"AI: MiniMax sugirió un movimiento inesperado. Transicionando a End.")
                    pass_to_end = Move(action_type=ActionType.PASS, target_zone='end')
                    current_state = current_state.apply_move(pass_to_end)
                    break
                    
                # Después de un ataque, salir si el juego terminó
                if current_state.is_game_over():
                    print("Juego terminado durante Battle Phase.")
                    return current_state
                    
        # 4. FASE FINAL (End Phase) - Transición de turno
        if current_state.phase == 'end':
            # Solo pasar el turno (cambio de jugador)
            end_pass_move = next(
                (m for m in current_state.get_possible_moves() if m.action_type == ActionType.PASS and m.target_zone == 'change_turn'), 
                None
            )
            if end_pass_move:
                current_state = current_state.apply_move(end_pass_move)
                print("AI: Transición de turno completada.")
            else:
                print("Error: No se encontró movimiento de cambio de turno en End Phase.")


        print(f"--- Turno de la IA finalizado. Nuevo estado: {current_state} ---")
        return current_state