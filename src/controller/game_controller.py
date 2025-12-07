import pygame
import sys
from typing import Optional, List, Tuple

# Importaciones del Model
from model.game.gamestate import GameState
from model.game.move import Move, ActionType, Position
from model.game.player import Player
from model.cards.card import Card

# Importación de la Vista
from view.game_view import GameView, SCREEN_WIDTH, SCREEN_HEIGHT

class GameController:
    """
    Controlador principal que maneja el bucle de Pygame y la interacción
    entre la View y el Model (GameState).
    """
    
    def __init__(self, initial_game_state: GameState, ai_controller):
        """
        Inicializa Pygame, la Vista y el estado del juego.
        
        Args:
            initial_game_state: El estado inicial del juego (Model).
            ai_controller: La instancia del controlador de la IA.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Fusion Duels - Pygame")
        self.clock = pygame.time.Clock()
        
        # MVC Components
        self.game_state: GameState = initial_game_state
        self.view = GameView(self.screen)
        self.ai_controller = ai_controller
        
        self.running = True
        self.round_number = 1  # Contador de rondas
        
        # Estado de selección para invocaciones con sacrificio
        self.selected_card_hand: Optional[int] = None  # Índice de carta en mano seleccionada
        self.tributes_selected: List[int] = []  # Índices de monstruos a sacrificar
        self.selecting_tributes = False  # Flag para modo selección de sacrificios
        
        # Estado de selección para ataques
        self.selected_attacker: Optional[int] = None  # Índice del monstruo atacante

    def handle_input(self):
        """
        Maneja los eventos de Pygame (clics de ratón, teclado, cerrar ventana).
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Clic izquierdo
                mouse_pos = event.pos
                self._handle_mouse_click(mouse_pos)

    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]):
        """Distribuye los clics según el contexto del juego."""
        
        if self.game_state.current_turn != 'player':
            # Si es turno de la IA, no procesamos clics
            return
        
        # Si estamos en modo selección de sacrificios
        if self.selecting_tributes:
            self._handle_tribute_selection(mouse_pos)
            return
        
        # Si estamos en Battle Phase y seleccionamos atacante
        if self.selected_attacker is not None and self.game_state.phase == 'battle':
            self._handle_attack_target_selection(mouse_pos)
            return
        
        # Botón PASS
        pass_button_rect = self.view.get_pass_button_rect()
        if pass_button_rect and pass_button_rect.collidepoint(mouse_pos):
            self._handle_pass_action()
            return
        
        # Click en carta de la mano (para invocar)
        hand_card_rects = self.view.get_hand_card_rects(self.game_state.player.hand.cards, is_player=True)
        for index, card_rect in enumerate(hand_card_rects):
            if card_rect.collidepoint(mouse_pos):
                self._handle_hand_card_click(index)
                return
        
        # Click en carta de campo propia (para cambiar posición o atacar)
        field_card_rects = self.view.get_field_card_rects(self.game_state.player.field, is_player=True)
        for index, card_rect in enumerate(field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                if self.game_state.phase == 'battle':
                    # En Battle Phase, seleccionar atacante
                    self._handle_attacker_selection(index)
                else:
                    # En Main Phase, cambiar posición
                    self._handle_field_card_click(index)
                return
        
        # Click en carta de campo enemiga (para atacar)
        if self.game_state.phase == 'battle':
            enemy_field_card_rects = self.view.get_field_card_rects(self.game_state.ai_player.field, is_player=False)
            for index, card_rect in enumerate(enemy_field_card_rects):
                if card_rect and card_rect.collidepoint(mouse_pos):
                    if self.selected_attacker is not None:
                        self._execute_attack(index)
                    return
                return
        
        # Click en carta de campo (para cambiar posición)
        field_card_rects = self.view.get_field_card_rects(self.game_state.player.field, is_player=True)
        for index, card_rect in enumerate(field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                self._handle_field_card_click(index)
                return

    def _handle_hand_card_click(self, card_index: int):
        """Maneja el click en una carta de la mano para invocarla."""
        
        hand = self.game_state.player.hand
        if card_index >= len(hand.cards):
            return
        
        card = hand.cards[card_index]
        
        # Buscar un slot vacío para la invocación
        empty_slot = self.game_state.player.field.get_empty_slot_index()
        if empty_slot is None:
            print("No hay slots disponibles en el campo.")
            return
        
        # Verificar si necesita sacrificios (5+ estrellas)
        if card.stars >= 5:
            # Contar monstruos en el campo
            monsters_on_field = [m for m in self.game_state.player.field.monsters if m is not None]
            tributes_needed = 2 if card.stars >= 6 else 1  # 5-5 estrellas: 1 sacrificio, 6+ estrellas: 2 sacrificios
            
            if len(monsters_on_field) < tributes_needed:
                print(f"Se necesitan {tributes_needed} sacrificios pero solo hay {len(monsters_on_field)} monstruos.")
                return
            
            # Iniciar modo selección de sacrificios
            self.selected_card_hand = card_index
            self.tributes_selected = []
            self.selecting_tributes = True
            print(f"Selecciona {tributes_needed} monstruos para sacrificar (haz clic en el campo).")
            return
        
        # Invocación normal (sin sacrificios)
        self._invoke_card(card_index, empty_slot, Position.FACE_UP_ATK, [])

    def _handle_tribute_selection(self, mouse_pos: Tuple[int, int]):
        """Maneja la selección de monstruos para sacrificar."""
        
        field_card_rects = self.view.get_field_card_rects(self.game_state.player.field, is_player=True)
        tributes_needed = 2 if self.game_state.player.hand.cards[self.selected_card_hand].stars >= 6 else 1
        
        for index, card_rect in enumerate(field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                if index not in self.tributes_selected and self.game_state.player.field.get_card_at(index):
                    self.tributes_selected.append(index)
                    print(f"Sacrificio seleccionado: slot {index}. ({len(self.tributes_selected)}/{tributes_needed})")
                    
                    # Si ya tenemos suficientes sacrificios, invocar
                    if len(self.tributes_selected) == tributes_needed:
                        empty_slot = self.game_state.player.field.get_empty_slot_index()
                        if empty_slot is not None:
                            self._invoke_card(
                                self.selected_card_hand,
                                empty_slot,
                                Position.FACE_UP_ATK,
                                self.tributes_selected
                            )
                            self.selecting_tributes = False
                            self.selected_card_hand = None
                            self.tributes_selected = []
                return

    def _invoke_card(self, hand_index: int, field_slot: int, position: Position, tribute_indices: List[int]):
        """
        Invoca una carta de la mano al campo.
        
        Args:
            hand_index: Índice de la carta en la mano
            field_slot: Slot del campo donde invocar
            position: Posición (ATK o DEF)
            tribute_indices: Índices de monstruos a sacrificar (lista vacía si no hay)
        """
        
        hand = self.game_state.player.hand
        if hand_index >= len(hand.cards):
            return
        
        card = hand.cards[hand_index]
        
        # Crear movimiento de invocación
        move = Move(
            action_type=ActionType.SUMMON,
            card_id=card.number,
            source_zone='hand',
            source_index=hand_index,
            target_zone='field',
            target_index=field_slot,
            position=position,
            fusion_materials_indices=tuple(tribute_indices)  # Usamos este campo para los sacrificios
        )
        
        # Aplicar el movimiento
        try:
            self.game_state = self.game_state.apply_move(move)
            print(f"Carta {card.name} invocada en slot {field_slot}.")
        except Exception as e:
            print(f"Error al invocar la carta: {e}")

    def _handle_field_card_click(self, field_index: int):
        """Maneja el click en una carta de campo para cambiar posición."""
        
        field = self.game_state.player.field
        current_position = field.get_position_at(field_index)
        
        if current_position is None:
            return
        
        # Cambiar posición: ATK -> DEF o DEF -> ATK
        new_position = Position.FACE_UP_DEF if current_position == Position.FACE_UP_ATK else Position.FACE_UP_ATK
        
        move = Move(
            action_type=ActionType.CHANGE_POSITION,
            source_zone='field',
            source_index=field_index,
            position=new_position
        )
        
        try:
            self.game_state = self.game_state.apply_move(move)
            pos_name = "Ataque" if new_position == Position.FACE_UP_ATK else "Defensa"
            print(f"Carta en slot {field_index} cambió a posición {pos_name}.")
        except Exception as e:
            print(f"Error al cambiar posición: {e}")

    def _handle_pass_action(self):
        """
        Aplica el movimiento de PASS al GameState.
        """
        print("Jugador presionó PASS.")
        
        # Obtener el siguiente target_zone según la fase actual
        phase = self.game_state.phase
        if phase == 'draw':
            next_phase = 'main'
        elif phase == 'main':
            next_phase = 'battle'
        elif phase == 'battle':
            next_phase = 'end'
        elif phase == 'end':
            next_phase = 'change_turn'
        else:
            next_phase = 'main'
        
        pass_move = Move(action_type=ActionType.PASS, target_zone=next_phase)
        
        try:
            # Aplicamos el movimiento al estado
            self.game_state = self.game_state.apply_move(pass_move)
            print(f"Fase avanzada a: {next_phase}")
            
            # Si se cambia de turno (change_turn), incrementar contador de rondas
            if next_phase == 'change_turn':
                # Incrementar contador cuando el turno cambia (alternancia por jugador)
                self.round_number += 1
                print(f"Turno cambiado. Ronda/Turno ahora: {self.round_number}")

            if self.game_state.current_turn == 'ai':
                self._execute_ai_turn()
        except Exception as e:
            print(f"Error al aplicar PASS: {e}")

    def _execute_ai_turn(self):
        """
        Ejecuta el turno completo de la IA.
        """
        print("Ejecutando turno de la IA...")
        try:
            self.game_state = self.ai_controller.execute_ai_turn(self.game_state)
            print("Turno de la IA finalizado.")
            # Si la IA devolvió el turno al jugador, incrementamos el contador
            if self.game_state.current_turn == 'player':
                self.round_number += 1
                print(f"Ronda/Turno ahora: {self.round_number}")
        except Exception as e:
            print(f"Error durante turno de IA: {e}")

    def run(self):
        """
        Bucle principal del juego.
        """
        while self.running:
            self.handle_input()
            
            # 1. Actualizar el Model (ya se hace en handle_input con apply_move)
            
            # 2. Dibujar la View
            self.view.draw_game(self.game_state, self.round_number)
            
            # 3. Mostrar modo de selección de sacrificios
            if self.selecting_tributes:
                self._draw_tribute_selection_prompt()
            
            # 4. Controlar la tasa de frames
            self.clock.tick(60)
    
    def _draw_tribute_selection_prompt(self):
        """Dibuja un prompt indicando que se deben seleccionar sacrificios."""
        font = pygame.font.SysFont('Arial', 20, bold=True)
        card = self.game_state.player.hand.cards[self.selected_card_hand]
        tributes_needed = 2 if card.stars >= 6 else 1
        
        prompt = f"Selecciona {tributes_needed} monstruo(s) para sacrificar (haz clic en el campo)"
        text_surface = font.render(prompt, True, (255, 200, 0))
        
        # Mostrar en la parte inferior de la pantalla
        rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self.screen.blit(text_surface, rect)
        pygame.display.update(rect)
    
    def _handle_attacker_selection(self, field_index: int):
        """Selecciona un monstruo para atacar en Battle Phase."""
        
        if self.game_state.phase != 'battle':
            print("Solo puedes atacar en Battle Phase.")
            return
        
        # Verificar si es primera ronda (no se puede atacar)
        if self.round_number == 1:
            print("No puedes atacar en la primera ronda.")
            return
        
        card = self.game_state.player.field.get_card_at(field_index)
        if card is None:
            print("No hay carta en ese slot.")
            return
        
        # Verificar que esté en posición de ataque
        position = self.game_state.player.field.get_position_at(field_index)
        if position != Position.FACE_UP_ATK:
            print("Solo monstruos en posición de Ataque pueden atacar.")
            return
        
        self.selected_attacker = field_index
        print(f"Monstruo atacante seleccionado: {card.name} (slot {field_index})")
        print("Ahora haz clic en un monstruo enemigo o LP para atacar.")
    
    def _handle_attack_target_selection(self, mouse_pos: Tuple[int, int]):
        """Maneja la selección del objetivo del ataque."""
        
        enemy_field_card_rects = self.view.get_field_card_rects(self.game_state.ai_player.field, is_player=False)
        
        # Verificar si clickeó en LP enemigo (esquina inferior derecha)
        lp_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2 - 50, 120, 50)
        if lp_rect.collidepoint(mouse_pos):
            # Ataque directo a LP
            self._execute_attack(-1)
            return
        
        # Verificar si clickeó en un monstruo enemigo
        for index, card_rect in enumerate(enemy_field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                self._execute_attack(index)
                return
    
    def _execute_attack(self, target_index: int):
        """
        Ejecuta un ataque.
        
        Args:
            target_index: Índice del monstruo enemigo (-1 para ataque directo a LP)
        """
        if self.selected_attacker is None:
            return
        
        move = Move(
            action_type=ActionType.ATTACK,
            source_zone='field',
            source_index=self.selected_attacker,
            target_zone='field',
            target_index=target_index
        )
        
        try:
            attacker = self.game_state.player.field.get_card_at(self.selected_attacker)
            
            if target_index == -1:
                print(f"{attacker.name} atacó directamente a los LP del oponente!")
            else:
                defender = self.game_state.ai_player.field.get_card_at(target_index)
                if defender:
                    print(f"{attacker.name} atacó a {defender.name}!")
                else:
                    print("No hay tarjeta para atacar en ese slot.")
                    self.selected_attacker = None
                    return
            
            self.game_state = self.game_state.apply_move(move)
            self.selected_attacker = None  # Resetear selección de atacante
            
        except Exception as e:
            print(f"Error al atacar: {e}")
            self.selected_attacker = None