from dataclasses import dataclass, field, replace
from typing import List, Dict, Tuple

# Importaciones de los componentes modulares
from model.cards.card import Card
from model.fusions.fusion_recipe import FusionRecipe, get_fusion_result
from .player import Player
from .move import Move, ActionType, Position
from model.cards.deck import random_deck

# Constante para MiniMax (se asume que existe en un módulo ai/minimax o se define aquí)
INF = float('inf') 

@dataclass(frozen=True)
class GameState:
    """
    El contenedor central que define el estado completo del juego.
    Utiliza instancias de Player para delegar el estado de mano, campo, etc.
    Es inmutable (frozen=True) para ser utilizado en el algoritmo MiniMax.
    """
    
    # --- Estructura Básica del Juego: DELEGACIÓN ---
    player: Player = field(default_factory=lambda: Player(name="Player"))
    ai_player: Player = field(default_factory=lambda: Player(name="AI"))
    current_turn: str = 'player' # 'player' o 'ai'
    phase: str = 'draw'          # 'draw', 'main', 'battle', 'end'
    
    # --- Datos de Referencia (Se inicializan una vez) ---
    all_cards: Dict[str, Card] = field(default_factory=dict, compare=False)
    all_recipes: List[FusionRecipe] = field(default_factory=list, compare=False)
    
    def __post_init__(self):
        """Asegura la validez del estado (inmutable)."""
        if self.current_turn not in ('player', 'ai'):
            raise ValueError("Turno inválido.")
        if self.phase not in ('draw', 'main', 'battle', 'end'):
            raise ValueError("Fase inválida.")

    def __repr__(self) -> str:
        return (
            f"GameState(Turn: {self.current_turn.upper()}, Phase: {self.phase.upper()}, "
            f"Player LP: {self.player.life_points}, AI LP: {self.ai_player.life_points})"
        )

    # ----------------------------------------------------------------------
    # --- LÓGICA REQUERIDA POR MINIMAX (Heurística) ---
    # ----------------------------------------------------------------------

    def is_game_over(self) -> bool:
        """Verifica si el juego ha terminado (e.g., LP a cero)."""
        return self.player.life_points <= 0 or self.ai_player.life_points <= 0

    def evaluate(self) -> float:
        """
        Función heurística para evaluar el estado desde la perspectiva de la IA (MAX player).
        Retorna un valor alto si la IA está ganando.
        """
        # Devuelve un valor muy alto/bajo para los estados terminales
        if self.ai_player.life_points <= 0:
            return -INF # La IA perdió
        if self.player.life_points <= 0:
            return INF # La IA ganó

        # Ponderación de factores (ajustada para el ejemplo)
        LP_WEIGHT = 1.0
        HAND_WEIGHT = 50.0 
        BOARD_POWER_WEIGHT = 0.2

        # 1. Ventaja de Life Points
        lp_advantage = self.ai_player.life_points - self.player.life_points
        
        # 2. Ventaja de Campo (ATK/DEF total en campo)
        ai_field_power = 0
        for slot in self.ai_player.field.monsters:
            if slot:
                card, position, _ = slot
                # ATK cuenta si está en ataque, DEF si está en defensa
                power = card.attack if position == Position.FACE_UP_ATK else card.defense
                ai_field_power += power
                
        player_field_power = 0
        for slot in self.player.field.monsters:
            if slot:
                card, position, _ = slot
                power = card.attack if position == Position.FACE_UP_ATK else card.defense
                player_field_power += power
                
        field_advantage = (ai_field_power - player_field_power) * BOARD_POWER_WEIGHT
        
        # 3. Cartas en mano (potencial)
        hand_advantage = (len(self.ai_player.hand) - len(self.player.hand)) * HAND_WEIGHT
        
        # Puntuación final: (Ventaja de la IA)
        final_score = (lp_advantage * LP_WEIGHT) + field_advantage + hand_advantage
        
        return final_score


    # ----------------------------------------------------------------------
    # --- LÓGICA DE JUEGO COMPLETA (Generación y Aplicación de Movimientos) ---
    # ----------------------------------------------------------------------
    
    def _get_current_players(self) -> Tuple[Player, Player]:
        """Devuelve el jugador actual y el oponente."""
        if self.current_turn == 'ai':
            return self.ai_player, self.player
        else:
            return self.player, self.ai_player
            
    # El método apply_move ahora debe actualizar las copias de los jugadores y crear un nuevo estado.

    def get_possible_moves(self) -> List[Move]:
        """
        Genera todos los movimientos legales posibles para el jugador actual 
        en la fase actual.
        """
        if self.is_game_over():
            return []
            
        moves: List[Move] = []
        current_p, opponent_p = self._get_current_players()
        
        # --- FASE DE ROBAR (Draw Phase) ---
        if self.phase == 'draw':
            # Solo pasar a Main (el robo ya se maneja en el cambio de turno)
            moves.append(Move(action_type=ActionType.PASS, target_zone='main'))
            
        # --- FASE PRINCIPAL (Main Phase) ---
        elif self.phase == 'main':
            # 1. Pasar a Battle o End
            moves.append(Move(action_type=ActionType.PASS, target_zone='battle'))
            moves.append(Move(action_type=ActionType.PASS, target_zone='end'))
            
            empty_slot_index = current_p.field.get_empty_slot_index()

            # 2. Invocación Normal / Set (si puede y hay slot)
            if current_p.can_normal_summon and empty_slot_index is not None:
                for idx, card in enumerate(current_p.hand.cards):
                    # Asumimos que todas las cartas son Monstruos Invocables
                    
                    # Invocación en ATK
                    moves.append(Move(
                        action_type=ActionType.SUMMON, 
                        card_id=card.number,
                        source_zone='hand', 
                        target_index=empty_slot_index,
                        source_index=idx,
                        position=Position.FACE_UP_ATK
                    ))
                    # Set en DEF (boca abajo)
                    moves.append(Move(
                        action_type=ActionType.SET, 
                        card_id=card.number,
                        source_zone='hand', 
                        target_index=empty_slot_index,
                        source_index=idx,
                        position=Position.FACE_UP_DEF # Usamos esta para representar SET
                    ))

            # 3. Fusión
            if empty_slot_index is not None and len(current_p.hand) >= 2:
                # Iterar sobre todas las combinaciones de 2 cartas en la mano
                for i in range(len(current_p.hand)):
                    for j in range(i + 1, len(current_p.hand)):
                        card1 = current_p.hand.get_card_at(i)
                        card2 = current_p.hand.get_card_at(j)
                        
                        if card1 and card2:
                            result_id = get_fusion_result(card1, card2, self.all_recipes)
                            
                            if result_id and result_id in self.all_cards:
                                moves.append(Move(
                                    action_type=ActionType.FUSION_SUMMON, 
                                    card_id=result_id,
                                    source_zone='hand',
                                    target_zone='field',
                                    target_index=empty_slot_index,
                                    fusion_materials_indices=(i, j)
                                ))
                                
            # 4. Cambiar Posición 
            for idx in range(current_p.field.MONSTER_SLOTS):
                monster_slot = current_p.field.monsters[idx]
                if monster_slot:
                    # Permite cambiar de posición solo una vez por turno (simplificación)
                    
                    card, current_pos, _ = monster_slot
                    # Cambio a ATK
                    if current_pos != Position.FACE_UP_ATK:
                        moves.append(Move(
                            action_type=ActionType.CHANGE_POSITION,
                            source_index=idx,
                            position=Position.FACE_UP_ATK
                        ))
                    # Cambio a DEF
                    if current_pos != Position.FACE_UP_DEF:
                        moves.append(Move(
                            action_type=ActionType.CHANGE_POSITION,
                            source_index=idx,
                            position=Position.FACE_UP_DEF
                        ))

        # --- FASE DE BATALLA (Battle Phase) ---
        elif self.phase == 'battle':
            # 1. Pasar a End
            moves.append(Move(action_type=ActionType.PASS, target_zone='end'))

            # 2. Ataque
            # Monstruos que pueden atacar (asumimos que todos en ATK pueden atacar y que no hayan atacado ya)
            for i in range(current_p.field.MONSTER_SLOTS):
                monster_slot = current_p.field.monsters[i]
                if monster_slot:
                    # monster_slot is (Card, Position, has_attacked)
                    _, pos, has_attacked = monster_slot
                    if pos == Position.FACE_UP_ATK and not has_attacked:
                        # a) Ataque directo a LP (si no hay monstruos en campo oponente)
                        if all(slot is None for slot in opponent_p.field.monsters):
                            moves.append(Move(
                                action_type=ActionType.ATTACK,
                                source_index=i,
                                target_index=-1
                            ))
                        else:
                            # b) Ataque a monstruos del oponente
                            for j in range(opponent_p.field.MONSTER_SLOTS):
                                if opponent_p.field.monsters[j] is not None:
                                    moves.append(Move(
                                        action_type=ActionType.ATTACK,
                                        source_index=i,
                                        target_index=j
                                    ))

        # --- FASE FINAL (End Phase) ---
        elif self.phase == 'end':
            # Solo pasar el turno
            moves.append(Move(action_type=ActionType.PASS, target_zone='change_turn'))

        return moves

    def apply_move(self, move: Move) -> 'GameState':
        """
        Retorna un NUEVO GameState que resulta de aplicar el movimiento dado.
        """
        # if self.is_game_over():
        #     return self

        try:
            # Obtener copias de los jugadores (para modificar y crear un nuevo estado)
            # Esto es crucial para la inmutabilidad
            new_player, new_ai_player = self.player, self.ai_player

            # Identificar quién está actuando
            is_ai_turn = self.current_turn == 'ai'
            acting_p = new_ai_player if is_ai_turn else new_player
            opponent_p = new_player if is_ai_turn else new_ai_player

            new_phase = self.phase
            new_turn = self.current_turn

            # --- Lógica de Transición de Fases (PASS) ---
            if move.action_type == ActionType.PASS:
                if move.target_zone == 'main':
                    new_phase = 'main'
                    # RESET: Permitir invocación normal al entrar a Main Phase
                    acting_p = acting_p.get_copy_with_summon_used(False)
                elif move.target_zone == 'battle':
                    new_phase = 'battle'
                    # Reset attack flags for acting player's field when entering Battle Phase
                    try:
                        new_field = acting_p.field.reset_attacks()
                        acting_p = acting_p.get_copy_with_field(new_field)
                    except Exception:
                        pass
                elif move.target_zone == 'end':
                    new_phase = 'end'
                elif move.target_zone == 'change_turn':

                    # 1. Cambiar turno y fase
                    new_turn = 'player' if self.current_turn == 'ai' else 'ai'
                    new_phase = 'draw'

                    # 2. Resetear flag de Invocación Normal para ambos jugadores
                    new_player = new_player.get_copy_with_summon_used(False)
                    new_ai_player = new_ai_player.get_copy_with_summon_used(False)

                    # 3. Ejecutar Robo (Draw) para el jugador que recibe el turno
                    next_acting_p = new_ai_player if new_turn == 'ai' else new_player
                    next_acting_p, _ = next_acting_p.draw_card()

                    if new_turn == 'ai':
                        new_ai_player = next_acting_p
                    else:
                        new_player = next_acting_p

            # --- Lógica de Acciones en Main Phase ---
            elif self.phase == 'main':

                if move.action_type in (ActionType.SUMMON, ActionType.SET):
                    if move.target_index is None or move.source_index is None or not acting_p.can_normal_summon: return self

                    card_to_place = acting_p.hand.get_card_at(move.source_index)
                    if not card_to_place: return self

                    # Verificar si la carta necesita sacrificios (tributos)
                    tributes_needed = 0
                    if card_to_place.stars >= 6:
                        tributes_needed = 2
                    elif card_to_place.stars >= 5:
                        tributes_needed = 1

                    # Si se necesitan sacrificios, validar que estén proporcionados
                    if tributes_needed > 0:
                        if not move.fusion_materials_indices or len(move.fusion_materials_indices) != tributes_needed:
                            return self  # Sacrificios insuficientes

                        # 1. Remover tributos (sacrificios) del campo, en orden descendente para evitar cambio de índices
                        tribute_indices = sorted(move.fusion_materials_indices, reverse=True)
                        new_field = acting_p.field
                        for tribute_idx in tribute_indices:
                            new_field, sacrificed_card = new_field.remove_monster(tribute_idx)
                            # Opcionalmente, enviar al cementerio
                            acting_p = acting_p.send_card_to_graveyard(sacrificed_card)

                        acting_p = acting_p.get_copy_with_field(new_field)

                    # 2. Retirar carta de la mano
                    new_hand, _ = acting_p.hand.remove_card_at(move.source_index)

                    # 3. Colocar carta en el campo
                    position = move.position if move.position else Position.FACE_UP_ATK
                    new_field = acting_p.field.place_monster(card_to_place, move.target_index, position)

                    # 4. Actualizar jugador
                    acting_p = acting_p.get_copy_with_hand(new_hand)
                    acting_p = acting_p.get_copy_with_field(new_field)
                    acting_p = acting_p.get_copy_with_summon_used(True) # Usa la invocación normal

                elif move.action_type == ActionType.FUSION_SUMMON:
                    if not move.fusion_materials_indices or move.target_index is None: return self

                    idx1, idx2 = move.fusion_materials_indices
                    card1 = acting_p.hand.get_card_at(idx1)
                    card2 = acting_p.hand.get_card_at(idx2)

                    # Obtener resultado de fusión
                    result_id = get_fusion_result(card1, card2, self.all_recipes)
                    if not result_id or result_id not in self.all_cards: return self

                    result_card = self.all_cards[result_id]

                    # 1. Remover materiales (el índice mayor primero para no cambiar el menor)
                    remove_idx1 = max(idx1, idx2)
                    remove_idx2 = min(idx1, idx2)

                    new_hand, material1 = acting_p.hand.remove_card_at(remove_idx1)
                    new_hand, material2 = new_hand.remove_card_at(remove_idx2)

                    # 2. Enviar materiales al cementerio
                    acting_p = acting_p.send_card_to_graveyard(material1)
                    acting_p = acting_p.send_card_to_graveyard(material2)

                    # 3. Colocar resultado en campo (ATK por defecto)
                    new_field = acting_p.field.place_monster(result_card, move.target_index, Position.FACE_UP_ATK)

                    # 4. Actualizar jugador con nuevo Hand y Field
                    acting_p = acting_p.get_copy_with_hand(new_hand)
                    acting_p = acting_p.get_copy_with_field(new_field)
                    # 5. MARCAR: Fusion Summon también cuenta como la invocación normal del turno
                    acting_p = acting_p.get_copy_with_summon_used(True)

                elif move.action_type == ActionType.CHANGE_POSITION:
                    if move.source_index is None or move.position is None: return self

                    new_field = acting_p.field.change_monster_position(move.source_index, move.position)
                    acting_p = acting_p.get_copy_with_field(new_field)

            # --- Lógica de Acciones en Battle Phase ---
            elif self.phase == 'battle':

                if move.action_type == ActionType.ATTACK:
                    if move.source_index is None: return self
                    
                    attacking_slot = acting_p.field.monsters[move.source_index]
                    if not attacking_slot or attacking_slot[1] != Position.FACE_UP_ATK: return self
                    
                    attacking_card = attacking_slot[0]
                    
                    # A. Ataque Directo a LP
                    if move.target_index == -1:
                        damage = attacking_card.attack
                        opponent_p = opponent_p.take_damage(damage)
                        print(f"¡{acting_p.name} ataca directamente a {opponent_p.name} por {damage} de daño!")
                    # B. Ataque a Monstruo
                    elif move.target_index is not None:
                        # VALIDATE: Ensure target slot has a card
                        if move.target_index < 0 or move.target_index >= opponent_p.field.MONSTER_SLOTS:
                            return self  # Invalid target index
                        
                        target_slot = opponent_p.field.monsters[move.target_index]
                        if not target_slot: 
                            return self  # Target slot is empty
                        
                        defending_card, defending_pos, _ = target_slot
                        
                        # Only one battle outcome per attack
                        if defending_pos == Position.FACE_UP_ATK:
                            # Battle ATK vs ATK: Compare ATK values
                            atk_diff = attacking_card.attack - defending_card.attack
                            if atk_diff > 0:
                                opponent_p = opponent_p.take_damage(atk_diff)
                                new_opp_field, destroyed = opponent_p.field.remove_monster(move.target_index)
                                opponent_p = opponent_p.get_copy_with_field(new_opp_field).send_card_to_graveyard(destroyed)
                                print(f"El monstruo de {acting_p.name} destruye al de {opponent_p.name} en batalla (ATK vs ATK).")
                            elif atk_diff < 0:
                                acting_p = acting_p.take_damage(abs(atk_diff))
                                new_act_field, destroyed = acting_p.field.remove_monster(move.source_index)
                                acting_p = acting_p.get_copy_with_field(new_act_field).send_card_to_graveyard(destroyed)
                                print(f"El monstruo de {opponent_p.name} destruye al de {acting_p.name} en batalla (ATK vs ATK).")
                            else:  # atk_diff == 0
                                new_opp_field, destroyed_opp = opponent_p.field.remove_monster(move.target_index)
                                opponent_p = opponent_p.get_copy_with_field(new_opp_field).send_card_to_graveyard(destroyed_opp)
                                new_act_field, destroyed_act = acting_p.field.remove_monster(move.source_index)
                                acting_p = acting_p.get_copy_with_field(new_act_field).send_card_to_graveyard(destroyed_act)
                                print(f"Ambos monstruos son destruidos en una explosiva batalla (ATK vs ATK).")
                                
                        elif defending_pos == Position.FACE_UP_DEF:
                            # Battle ATK vs DEF
                            def_diff = defending_card.defense - attacking_card.attack
                            if def_diff < 0:
                                # Monstruo defendedor es destruido (no hay daño a LP)
                                new_opp_field, destroyed = opponent_p.field.remove_monster(move.target_index)
                                opponent_p = opponent_p.get_copy_with_field(new_opp_field).send_card_to_graveyard(destroyed)
                                print(f"El monstruo de {acting_p.name} destruye al de {opponent_p.name} en batalla (ATK vs DEF).")
                            else:  # def_diff >= 0
                                # Jugador atacante recibe daño igual a la diferencia (no hay destrucción)
                                if def_diff > 0:
                                    acting_p = acting_p.take_damage(def_diff)
                                    print(f"{acting_p.name} recibe {def_diff} de daño por el contraataque del monstruo en DEF.")
                                else:
                                    print(f"El ataque de {acting_p.name} no puede penetrar la defensa de {opponent_p.name}.")

            # Finalmente, marcar que el monstruo atacante ya atacó (si aún está en campo)
            try:
                if 0 <= move.source_index < acting_p.field.MONSTER_SLOTS and acting_p.field.monsters[move.source_index] is not None:
                    new_field = acting_p.field.mark_monster_attacked(move.source_index)
                    acting_p = acting_p.get_copy_with_field(new_field)
            except Exception:
                # Si por algún motivo el índice ya no existe o el slot fue destruido durante la batalla,
                # no hacemos nada (es seguro continuar).
                pass

            # --- Asignación de Jugadores Actualizados ---
            if is_ai_turn:
                final_player = opponent_p
                final_ai_player = acting_p
            else:
                final_player = acting_p
                final_ai_player = opponent_p

            # Retornar el nuevo estado inmutable
            # Si la acción es PASS para cambiar de turno, se usa el new_turn y new_phase
            is_turn_change = (move.action_type == ActionType.PASS and move.target_zone == 'change_turn')

            return GameState(
                player=final_player,
                ai_player=final_ai_player,
                current_turn=new_turn if is_turn_change else self.current_turn,
                phase=new_phase if move.action_type == ActionType.PASS else self.phase,
                all_cards=self.all_cards,
                all_recipes=self.all_recipes
            )

        except ValueError as ve:
            print(f"[GameState] Movimiento inválido al aplicar move: {ve}")
            return self
        except Exception as e:
            print(f"[GameState] Error al aplicar move: {e}")
            return self

    def get_copy_with_players(self, player: Player, ai_player: Player) -> 'GameState':
        """Retorna una copia del GameState con los jugadores provistos (inmutable)."""
        return replace(self, player=player, ai_player=ai_player)
    
    def reinitialize_decks(self, deck_size: int) -> 'GameState':
        """
        Crea y baraja nuevos decks de tamaño 'deck_size' para ambos jugadores
        utilizando la función random_deck (que garantiza la aleatoriedad).
        """
        
        # 1. Crear el mazo del jugador (aleatorio y de tamaño 'deck_size')
        new_player_deck_list = random_deck(self.all_cards, deck_size)
        
        # 2. Crear el mazo de la IA (aleatorio y de tamaño 'deck_size')
        new_ai_deck_list = random_deck(self.all_cards, deck_size)
        
        # Convertir a tupla, ya que el Player lo requiere
        new_player_deck = tuple(new_player_deck_list)
        new_ai_deck = tuple(new_ai_deck_list)

        # 3. Crear los nuevos objetos Player inmutables
        new_player = self.player.get_copy_with_new_deck(new_player_deck)
        new_ai_player = self.ai_player.get_copy_with_new_deck(new_ai_deck)

        # 4. Retornar el GameState actualizado
        return replace(self, player=new_player, ai_player=new_ai_player)