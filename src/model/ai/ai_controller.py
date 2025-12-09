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
        print(f"AIController real inicializado con profundidad {depth}.")

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

        print(f"\n=== TURNO DE LA IA (Ronda/Turno) ===")
        print(f"IA LP: {current_state.ai_player.life_points} | Jugador LP: {current_state.player.life_points}")
        print(f"Fase actual: {current_state.phase}")
        
        # 1. FASE DE ROBAR (Draw Phase)
        if current_state.phase == 'draw':
            # Hacemos el robo explícito para la IA aquí (apply_move a 'main' no realiza el draw automáticamente)
            print("IA: En Draw Phase, robando carta (IA)...")
            new_ai_player, drawn = current_state.ai_player.draw_card()
            if drawn:
                print(f"IA: Robó {drawn.name}")
            else:
                print("IA: No hay cartas para robar.")
            # Reemplazar el ai_player en el estado
            current_state = current_state.get_copy_with_players(current_state.player, new_ai_player)

            # Ahora pasar a Main (para que la IA evalúe jugadas en Main)
            draw_pass_move = next(
                (m for m in current_state.get_possible_moves() if m.action_type == ActionType.PASS and m.target_zone == 'main'),
                None
            )
            if draw_pass_move:
                current_state = current_state.apply_move(draw_pass_move)
                print("IA: Pasó a Main Phase.")
            else:
                print("ERROR: No se encontró movimiento de PASS en Draw Phase.")
                # Aunque no haya PASS, seguimos para evitar bloqueo
        
        # 2. FASE PRINCIPAL (Main Phase) - Toma de decisiones con MiniMax
        if current_state.phase == 'main':
            print("IA: En Main Phase, buscando mejor acción con MiniMax...")
            
            action_count = 0
            while True:
                # La IA usa MiniMax para elegir el mejor movimiento en el estado actual
                possible_moves = current_state.get_possible_moves()
                print(f"IA: Movimientos posibles en Main: {len(possible_moves)} opciones")
                
                best_move = find_best_move(current_state, depth=self.depth)

                if best_move is None:
                    print("IA: No hay movimientos para elegir en Main Phase. Pasando a Battle.")
                    pass_to_battle = Move(action_type=ActionType.PASS, target_zone='battle')
                    current_state = current_state.apply_move(pass_to_battle)
                    break 
                
                # Si el mejor movimiento es una transición de fase, ejecutarla y salir
                if best_move.action_type == ActionType.PASS:
                    if best_move.target_zone == 'battle':
                        print("IA: Mejor movimiento es PASS a Battle Phase.")
                        current_state = current_state.apply_move(best_move)
                        break
                    elif best_move.target_zone == 'end':
                        print("IA: Mejor movimiento es PASS a End Phase (saltando Battle).")
                        current_state = current_state.apply_move(best_move)
                        break
                        
                # Si es un movimiento de acción (Summon, Fusion, CHANGE_POSITION, etc.), ejecutar
                print(f"IA: Ejecutando acción #{action_count + 1}: {best_move.action_type.name}")
                prev_state = current_state
                current_state = current_state.apply_move(best_move)
                if current_state == prev_state:
                    print("IA: El movimiento seleccionado no tuvo efecto o fue inválido, pasando a Battle.")
                    pass_to_battle = Move(action_type=ActionType.PASS, target_zone='battle')
                    current_state = current_state.apply_move(pass_to_battle)
                    break
                action_count += 1
                
                # Después de una acción, salir si el juego terminó
                if current_state.is_game_over():
                    print("Juego terminado durante Main Phase.")
                    return current_state
        
        # 3. FASE DE BATALLA (Battle Phase) - Toma de decisiones con MiniMax
        if current_state.phase == 'battle':
            print("IA: En Battle Phase, buscando mejor acción de ataque con MiniMax...")
            
            attack_count = 0
            while True:
                possible_moves = current_state.get_possible_moves()
                print(f"IA: Movimientos posibles en Battle: {len(possible_moves)} opciones")
                
                best_move = find_best_move(current_state, depth=self.depth)
                
                if best_move is None:
                    print("IA: No hay movimientos en Battle Phase. Pasando a End.")
                    pass_to_end = Move(action_type=ActionType.PASS, target_zone='end')
                    current_state = current_state.apply_move(pass_to_end)
                    break 

                if best_move.action_type == ActionType.PASS and best_move.target_zone == 'end':
                    print("IA: Mejor movimiento es PASS a End Phase.")
                    current_state = current_state.apply_move(best_move)
                    break 
                
                # Si es un ataque
                if best_move.action_type == ActionType.ATTACK:
                    attacker_slot = current_state.ai_player.field.monsters[best_move.source_index]
                    if attacker_slot:
                        attacker_card = attacker_slot[0]
                        attacker_name = attacker_card.name
                        target_name = "LP Directo"
                        if best_move.target_index != -1:
                            target_slot = current_state.player.field.monsters[best_move.target_index]
                            if target_slot:
                                target_name = target_slot[0].name
                        print(f"IA: Ataque #{attack_count + 1}: {attacker_name} ataca a {target_name}")
                        prev_state = current_state
                        current_state = current_state.apply_move(best_move)
                        if current_state == prev_state:
                            print("IA: Ataque inválido o sin efecto, pasando a End.")
                            pass_to_end = Move(action_type=ActionType.PASS, target_zone='end')
                            current_state = current_state.apply_move(pass_to_end)
                            break
                        attack_count += 1
                
                else:
                    # Otros movimientos no deberían generarse en Battle Phase.
                    print(f"IA: Movimiento inesperado en Battle Phase. Pasando a End.")
                    pass_to_end = Move(action_type=ActionType.PASS, target_zone='end')
                    current_state = current_state.apply_move(pass_to_end)
                    break
                    
                # Después de un ataque, salir si el juego terminó
                if current_state.is_game_over():
                    print("Juego terminado durante Battle Phase.")
                    return current_state
                    
        # 4. FASE FINAL (End Phase) - Transición de turno
        if current_state.phase == 'end':
            print("IA: En End Phase, pasando turno...")
            end_pass_move = next(
                (m for m in current_state.get_possible_moves() if m.action_type == ActionType.PASS and m.target_zone == 'change_turn'), 
                None
            )
            if end_pass_move:
                current_state = current_state.apply_move(end_pass_move)
                print("IA: Turno terminado, pasando al jugador.")
            else:
                print("ERROR: No se encontró movimiento de cambio de turno en End Phase.")


        print(f"=== FIN DEL TURNO DE LA IA ===\n")
        return current_state