import pygame
from typing import Optional, List, Tuple
from dataclasses import replace
# Importaciones del Model
from model.game.gamestate import GameState
from model.game.move import Move, ActionType, Position



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
        self.selecting_deck_size = True # Estado inicial

        # Estado de selección para invocaciones con sacrificio
        self.selected_card_hand: Optional[int] = None  # Índice de carta en mano seleccionada
        self.tributes_selected: List[int] = []  # Índices de monstruos a sacrificar
        self.selecting_tributes = False  # Flag para modo selección de sacrificios
        
        # Estado de selección para ataques
        self.selected_attacker: Optional[int] = None  # Índice del monstruo atacante

        # Añade estos atributos al __init__ de GameController (después de self.selected_attacker):
        self.selecting_position = False  # Flag para elegir posición al invocar
        self.card_to_place = None  # Card que se va a invocar
        self.position_choices = []  # Rectángulos de los botones de posición

        self.already_summoned = False  # Flag para rastrear si ya invocó una carta en esta Main Phase

        # Flag para mostrar el mensaje de "ya invocado"
        self.show_already_summoned_message = False  # Flag para mostrar el mensaje

        # Estado de selección de objetivo de ataque (diálogo)
        self.attack_target_dialog_active = False
        self.attack_target_rects: List[Tuple[pygame.Rect, int]] = []  # (rect, target_index) - target_index: slot o -1 para LP
        self.attack_close_rect: Optional[pygame.Rect] = None  # Rect del botón cerrar en diálogo de ataque

        # Mensaje de "no puedes atacar" (primera ronda)
        self.show_cannot_attack_message = False
        self.close_cannot_attack_rect: Optional[pygame.Rect] = None
        
        # Mensaje para indicar que un monstruo ya atacó
        self.show_already_attacked_message = False
        self.close_already_attacked_rect: Optional[pygame.Rect] = None

        self.selected_target: Optional[int] = None   # Para ataques
        self.close_message_rect: Optional[pygame.Rect] = None # Rect para el botón 'CERRAR' de 'ya invocaste'
        
        # ESTADO PARA ERROR DE SACRIFICIO ===
        self.show_tribute_error_message = False
        self.tribute_error_message: str = ""
        self.close_tribute_error_rect: Optional[pygame.Rect] = None
        # Estado para selección por-sacrificio (confirmación por carta)
        self.tributes_needed_required: int = 0
        self.confirming_tribute_card: bool = False
        self.pending_tribute_index: Optional[int] = None
        self.pending_tribute_card_name: str = ""
        self.pending_tribute_card_stats: Tuple[int, int] = (0, 0)
        self.confirm_tribute_rect: Optional[pygame.Rect] = None
        self.cancel_tribute_rect: Optional[pygame.Rect] = None
        # Rects para los botones en el diálogo de selección de sacrificios
        self.tribute_field_choice_rects: List[Tuple[pygame.Rect, int]] = []
        
        # === Atributos para mensajes de error genéricos ===
        self.error_message: str = ""
        self.error_title: str = ""
        self.error_timer: float = 0
        self.message_rect: Optional[pygame.Rect] = None
        self.close_btn_rect: Optional[pygame.Rect] = None
        
        # === DIÁLOGO DE CONFIRMACIÓN DE SACRIFICIO ===
        self.confirming_sacrifice = False  # Flag para mostrar diálogo de confirmación
        self.sacrifice_card_name: str = ""  # Nombre de la carta a invocar
        self.sacrifice_card_stats: Tuple[int, int] = (0, 0)  # (ATK, DEF)
        self.sacrifice_monsters_names: List[str] = []  # Nombres de monstruos a sacrificar
        self.sacrifice_confirm_rect: Optional[pygame.Rect] = None  # Rect del botón INVOCAR
        self.sacrifice_cancel_rect: Optional[pygame.Rect] = None  # Rect del botón CERRAR

    def handle_input(self):
        """
        Maneja los eventos de Pygame (clics de ratón, teclado, tamaño del deck, cerrar ventana).
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Solo procesar input si el juego no ha terminado
                if self.game_state.is_game_over():
                    return
                
                # Clic izquierdo
                mouse_pos = event.pos
                self._handle_mouse_click(mouse_pos)

    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]):
        """Distribuye los clics según el contexto del juego."""
        
        # PRIMERO: Si estamos seleccionando tamaño del deck, manejar eso
        if self.selecting_deck_size:
            self._handle_deck_size_selection(mouse_pos)
            return
        
        if self.game_state.current_turn != 'player':
            return
        
        # Si hay mensaje de "ya invocaste", detectar clic en cerrar
        if self.show_already_summoned_message:
            if self.close_message_rect and self.close_message_rect.collidepoint(mouse_pos):
                self.show_already_summoned_message = False
                self.close_message_rect = None
            return
        
        # Si hay mensaje de "no puedes atacar", detectar clic en cerrar
        if self.show_cannot_attack_message:
            if self.close_cannot_attack_rect and self.close_cannot_attack_rect.collidepoint(mouse_pos):
                self.show_cannot_attack_message = False
                self.close_cannot_attack_rect = None
            return

        # Si hay mensaje de "ya atacó", detectar clic en cerrar
        if self.show_already_attacked_message:
            if self.close_already_attacked_rect and self.close_already_attacked_rect.collidepoint(mouse_pos):
                self.show_already_attacked_message = False
                self.close_already_attacked_rect = None
            return
        
        # Si hay mensaje de ERROR DE SACRIFICIO, detectar clic en cerrar ===
        if self.show_tribute_error_message:
            if self.close_tribute_error_rect and self.close_tribute_error_rect.collidepoint(mouse_pos):
                self.show_tribute_error_message = False
                self.close_tribute_error_rect = None
            return
        
        # === DIALOGO DE CONFIRMACIÓN DE SACRIFICIO ===
        if self.confirming_sacrifice:
            self._handle_sacrifice_confirmation(mouse_pos)
            return

        # === DIALOGO DE CONFIRMACIÓN DE CADA SACRIFICIO (por carta) ===
        if self.confirming_tribute_card:
            self._handle_tribute_card_confirmation(mouse_pos)
            return
        
        # Si estamos eligiendo posición
        if self.selecting_position:
            self._handle_position_selection(mouse_pos)
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

        # DEBUG: imprimir mouse y rects para diagnosticar selección incorrecta
        print(f"[INPUT] mouse_pos={mouse_pos}")
        for i, r in enumerate(hand_card_rects):
            print(f"[RECT] hand[{i}] = {r}")

        for index, card_rect in enumerate(hand_card_rects):
            if card_rect.collidepoint(mouse_pos):
                print(f"[CLICK] mouse={mouse_pos} -> hit hand[{index}] rect={card_rect}")
                self._handle_hand_card_click(index)
                return
        
        # Click en carta de campo propia (para cambiar posición o atacar)
        field_card_rects = self.view.get_field_card_rects(self.game_state.player.field, is_player=True)
        for index, card_rect in enumerate(field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                if self.game_state.phase == 'battle':
                    self._handle_attacker_selection(index)
                else:
                    self._handle_field_card_click(index)
                return
        
        # Click en carta de campo enemiga (para atacar)
        if self.game_state.phase == 'battle':
            enemy_field_card_rects = self.view.get_field_card_rects(self.game_state.ai_player.field, is_player=False)
            for index, card_rect in enumerate(enemy_field_card_rects):
                if card_rect and card_rect.collidepoint(mouse_pos):
                    # Si ya tenemos un atacante seleccionado por el jugador, ejecutamos el ataque
                    if self.selected_attacker is not None:
                        self._execute_attack(index)
                    return
            # no return extra aquí — seguimos evaluando otros posibles clics
        
        # Click en carta de campo (para cambiar posición)
        field_card_rects = self.view.get_field_card_rects(self.game_state.player.field, is_player=True)
        for index, card_rect in enumerate(field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                self._handle_field_card_click(index)
                return

    def _handle_hand_card_click(self, card_index: int):
        """Maneja el click en una carta de la mano para invocarla."""
        
        # Si estamos en Main Phase y es turno del jugador
        if self.game_state.phase not in ('main',):
            print("Solo puedes invocar en Main Phase.")
            return
        
        # Verificar si ya invocó una carta en esta Main Phase
        if self.already_summoned:
            print("Ya invocaste una carta en esta Main Phase.")
            self.show_already_summoned_message = True
            return
        
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
            # Determinar sacrificios: 1 para Nivel 5-6, 2 para Nivel 7+ (asumiendo tu lógica de >= 6)
            tributes_needed = 2 if card.stars >= 6 else 1
            
            if len(monsters_on_field) < tributes_needed:
                # === ACTIVACIÓN DEL ERROR VISUAL (NUEVO) ===
                self.tribute_error_message = (
                    f"{card.name} (Nivel {card.stars})\n\n"
                    f"Requiere {tributes_needed} sacrificios.\n"
                    f"Tienes: {len(monsters_on_field)} monstruos"
                )
                self.show_tribute_error_message = True
                print(f"ERROR: Se necesitan {tributes_needed} sacrificios pero solo hay {len(monsters_on_field)} monstruos.")
                return # Bloquea la invocación
            
            # Iniciar modo selección de sacrificios
            self.selected_card_hand = card_index
            self.tributes_selected = []
            self.selecting_tributes = True
            # Guardar cuántos sacrificios se requieren para esta invocación
            self.tributes_needed_required = tributes_needed
            print(f"Selecciona {tributes_needed} monstruos para sacrificar (haz clic en el campo).")
            return
        
        # Invocación normal (Nivel 1-4): mostrar opciones de posición (ATK o DEF)
        self.selected_card_hand = card_index
        self.card_to_place = card
        self.selecting_position = True
        print(f"Elige posición para {card.name}: ATK (Ataque) o DEF (Defensa)")
        print(f"[DEBUG] Carta seleccionada en mano: index={card_index}, name={card.name}")

    def _handle_position_selection(self, mouse_pos: Tuple[int, int]):
        """Maneja la selección de posición (ATK o DEF) al invocar."""
        
        if not self.selecting_position or self.card_to_place is None:
            return
        
        # Posiciones relativas al diálogo (altura aumentada para acomodar botón cerrar)
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 120, 400, 240)
        
        # Botón ATK
        atk_rect = pygame.Rect(dialog_rect.x + 30, dialog_rect.y + 70, 120, 60)
        # Botón DEF
        def_rect = pygame.Rect(dialog_rect.x + 250, dialog_rect.y + 70, 120, 60)
        # Botón CERRAR
        close_rect = pygame.Rect(dialog_rect.x + 150, dialog_rect.y + 150, 100, 40)
        
        empty_slot = self.game_state.player.field.get_empty_slot_index()
        
        # Botón CERRAR: cancela la invocación
        if close_rect.collidepoint(mouse_pos):
            print("Invocación cancelada.")
            self.selecting_position = False
            self.card_to_place = None
            self.selected_card_hand = None
            return
        
        if atk_rect.collidepoint(mouse_pos):
            # Invocar en posición de Ataque
            self._invoke_card(self.selected_card_hand, empty_slot, Position.FACE_UP_ATK, [])
            self.selecting_position = False
            self.card_to_place = None
            return
        
        if def_rect.collidepoint(mouse_pos):
            # Invocar en posición de Defensa
            self._invoke_card(self.selected_card_hand, empty_slot, Position.FACE_UP_DEF, [])
            self.selecting_position = False
            self.card_to_place = None
            return

    def _draw_position_selection_prompt(self):
        """Dibuja los botones para elegir posición (ATK o DEF) con botón cerrar."""
        font_title = pygame.font.SysFont('Arial', 24, bold=True)
        font_btn = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Crear una superficie para el diálogo (altura aumentada para acomodar botón cerrar)
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 120, 400, 240)
        
        # Fondo semi-transparente DEL DIÁLOGO (no de toda la pantalla)
        dialog_surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        dialog_surface.fill((30, 30, 50))
        pygame.draw.rect(dialog_surface, (100, 100, 150), (0, 0, dialog_rect.width, dialog_rect.height), 3, border_radius=10)
        
        # Título dentro del diálogo (separado en dos líneas)
        title_text1 = "Elige posición:"
        title_surf1 = font_title.render(title_text1, True, (255, 255, 255))
        title_rect1 = title_surf1.get_rect(center=(dialog_rect.width // 2, 15))
        dialog_surface.blit(title_surf1, title_rect1)
        
        # Nombre de la carta en segunda línea
        card_name = self.card_to_place.name
        title_surf2 = font_title.render(card_name, True, (200, 200, 255))
        title_rect2 = title_surf2.get_rect(center=(dialog_rect.width // 2, 35))
        dialog_surface.blit(title_surf2, title_rect2)
        
        # Botón ATK
        atk_rect_local = pygame.Rect(30, 70, 120, 60)
        pygame.draw.rect(dialog_surface, (0, 200, 0), atk_rect_local, border_radius=10)
        atk_text = font_btn.render("ATAQUE", True, (255, 255, 255))
        dialog_surface.blit(atk_text, atk_text.get_rect(center=atk_rect_local.center))
        
        # Botón DEF
        def_rect_local = pygame.Rect(250, 70, 120, 60)
        pygame.draw.rect(dialog_surface, (0, 100, 200), def_rect_local, border_radius=10)
        def_text = font_btn.render("DEFENSA", True, (255, 255, 255))
        dialog_surface.blit(def_text, def_text.get_rect(center=def_rect_local.center))

        # Botón Cerrar (posición mejorada)
        close_rect_local = pygame.Rect(150, 150, 100, 40)
        pygame.draw.rect(dialog_surface, (200, 100, 100), close_rect_local, border_radius=10)
        close_text = font_btn.render("CERRAR", True, (255, 255, 255))
        dialog_surface.blit(close_text, close_text.get_rect(center=close_rect_local.center))

        # Dibujar el diálogo sobre la pantalla actual
        self.screen.blit(dialog_surface, dialog_rect.topleft)
    
    def _draw_sacrifice_confirmation_dialog(self):
        """Dibuja el diálogo de confirmación de sacrificio."""
        font_title = pygame.font.SysFont('Arial', 20, bold=True)
        font_label = pygame.font.SysFont('Arial', 16, bold=True)
        font_text = pygame.font.SysFont('Arial', 14)
        font_btn = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Tamaño y posición del diálogo (más alto para acomodar más contenido)
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2 - 180, 560, 360)
        
        # Fondo del diálogo
        dialog_surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        dialog_surface.fill((35, 35, 60))
        pygame.draw.rect(dialog_surface, (100, 150, 200), (0, 0, dialog_rect.width, dialog_rect.height), 3, border_radius=10)
        
        # Título principal
        title_text = "Confirmación de Invocación"
        title_surf = font_title.render(title_text, True, (255, 200, 100))
        dialog_surface.blit(title_surf, title_surf.get_rect(center=(dialog_rect.width // 2, 15)))
        
        # Línea separadora
        pygame.draw.line(dialog_surface, (100, 150, 200), (20, 40), (dialog_rect.width - 20, 40), 2)
        
        # Sección: Carta a invocar
        label1_surf = font_label.render("Invocar:", True, (200, 255, 200))
        dialog_surface.blit(label1_surf, (30, 50))
        
        card_text = f"{self.sacrifice_card_name} (ATK: {self.sacrifice_card_stats[0]} / DEF: {self.sacrifice_card_stats[1]})"
        card_surf = font_text.render(card_text, True, (255, 255, 200))
        dialog_surface.blit(card_surf, (50, 75))
        
        # Sección: Sacrificios
        label2_surf = font_label.render("Sacrificios:", True, (255, 200, 200))
        dialog_surface.blit(label2_surf, (30, 110))
        
        y_offset = 135
        for i, monster_name in enumerate(self.sacrifice_monsters_names):
            monster_text = f"• {monster_name}"
            monster_surf = font_text.render(monster_text, True, (200, 200, 255))
            dialog_surface.blit(monster_surf, (50, y_offset))
            y_offset += 25
        
        # Botones: INVOCAR y CERRAR
        btn_width = 100
        btn_height = 45
        btn_y = dialog_rect.height - 70
        
        # Botón INVOCAR (verde)
        invocar_rect_local = pygame.Rect(90, btn_y, btn_width, btn_height)
        pygame.draw.rect(dialog_surface, (50, 200, 50), invocar_rect_local, border_radius=8)
        invocar_text = font_btn.render("INVOCAR", True, (255, 255, 255))
        dialog_surface.blit(invocar_text, invocar_text.get_rect(center=invocar_rect_local.center))
        
        # Botón CERRAR (rojo)
        cerrar_rect_local = pygame.Rect(320, btn_y, btn_width, btn_height)
        pygame.draw.rect(dialog_surface, (200, 50, 50), cerrar_rect_local, border_radius=8)
        cerrar_text = font_btn.render("CERRAR", True, (255, 255, 255))
        dialog_surface.blit(cerrar_text, cerrar_text.get_rect(center=cerrar_rect_local.center))
        
        # Dibujar el diálogo sobre la pantalla
        self.screen.blit(dialog_surface, dialog_rect.topleft)
        
        # Guardar rects para detección de clics (en coordenadas globales)
        self.sacrifice_confirm_rect = pygame.Rect(dialog_rect.x + 90, dialog_rect.y + btn_y, btn_width, btn_height)
        self.sacrifice_cancel_rect = pygame.Rect(dialog_rect.x + 320, dialog_rect.y + btn_y, btn_width, btn_height)
    
    def _draw_tribute_card_confirmation(self):
        """Dibuja un diálogo pequeño para confirmar el sacrificio de una carta seleccionada."""
        font_title = pygame.font.SysFont('Arial', 18, bold=True)
        font_text = pygame.font.SysFont('Arial', 14)
        font_btn = pygame.font.SysFont('Arial', 14, bold=True)

        dialog_w, dialog_h = 420, 180
        dialog_rect = pygame.Rect(SCREEN_WIDTH//2 - dialog_w//2, SCREEN_HEIGHT//2 - dialog_h//2, dialog_w, dialog_h)

        surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        surface.fill((40, 40, 60))
        pygame.draw.rect(surface, (120, 140, 200), (0, 0, dialog_rect.width, dialog_rect.height), 2, border_radius=8)

        title = "Confirmar sacrificio"
        surface.blit(font_title.render(title, True, (255, 200, 120)), (dialog_rect.width//2 - 80, 8))

        # Mostrar información de la carta pendiente y estado de selección
        card_line = f"Carta: {self.pending_tribute_card_name} (ATK:{self.pending_tribute_card_stats[0]} DEF:{self.pending_tribute_card_stats[1]})"
        surface.blit(font_text.render(card_line, True, (230, 230, 230)), (20, 40))

        status_line = f"Seleccionados: {len(self.tributes_selected)} / {self.tributes_needed_required}"
        surface.blit(font_text.render(status_line, True, (200, 200, 255)), (20, 70))

        # Botones
        btn_w, btn_h = 100, 36
        y_btn = dialog_rect.height - 56
        confirm_local = pygame.Rect(60, y_btn, btn_w, btn_h)
        cancel_local = pygame.Rect(dialog_rect.width - 60 - btn_w, y_btn, btn_w, btn_h)

        pygame.draw.rect(surface, (50, 180, 50), confirm_local, border_radius=6)
        pygame.draw.rect(surface, (180, 60, 60), cancel_local, border_radius=6)
        txt_confirm = font_btn.render("SACRIFICAR", True, (255,255,255))
        surface.blit(txt_confirm, txt_confirm.get_rect(center=confirm_local.center))
        txt_cancel = font_btn.render("CANCELAR", True, (255,255,255))
        surface.blit(txt_cancel, txt_cancel.get_rect(center=cancel_local.center))

        # Blit
        self.screen.blit(surface, dialog_rect.topleft)

        # Store global rects
        self.confirm_tribute_rect = pygame.Rect(dialog_rect.x + confirm_local.x, dialog_rect.y + confirm_local.y, btn_w, btn_h)
        self.cancel_tribute_rect = pygame.Rect(dialog_rect.x + cancel_local.x, dialog_rect.y + cancel_local.y, btn_w, btn_h)

    def _draw_tribute_selection_prompt(self):
        """Dibuja un diálogo que permite elegir qué monstruos sacrificar (botones por slot)."""
        field = self.game_state.player.field
        font_title = pygame.font.SysFont('Arial', 20, bold=True)
        font_small = pygame.font.SysFont('Arial', 14)

        dialog_w, dialog_h = 520, 260
        dialog_rect = pygame.Rect(SCREEN_WIDTH//2 - dialog_w//2, SCREEN_HEIGHT//2 - dialog_h//2, dialog_w, dialog_h)

        surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        surface.fill((30, 30, 50))
        pygame.draw.rect(surface, (100, 120, 180), (0, 0, dialog_rect.width, dialog_rect.height), 2, border_radius=8)

        # Título
        title = "¿Qué monstruos sacrificar?"
        surface.blit(font_title.render(title, True, (255, 220, 120)), (20, 10))

        # Instrucción y contador
        needed = self.tributes_needed_required if self.tributes_needed_required > 0 else (
            2 if self.game_state.player.hand.cards[self.selected_card_hand].stars >= 6 else 1
        )
        instr = f"Selecciona {needed} monstruo(s) para sacrificar. Seleccionados: {len(self.tributes_selected)}"
        surface.blit(font_small.render(instr, True, (220, 220, 220)), (20, 44))

        # Limpiar rects previas
        self.tribute_field_choice_rects = []

        # Dibujar botones para cada slot del campo
        start_x = 20
        start_y = 80
        btn_w, btn_h = 140, 60
        padding = 12
        for i in range(field.MONSTER_SLOTS):
            x = start_x + (i % 3) * (btn_w + padding)
            y = start_y + (i // 3) * (btn_h + padding)
            local_rect = pygame.Rect(x, y, btn_w, btn_h)
            # Fondo distinto si vacío
            card = field.get_card_at(i)
            if card:
                pygame.draw.rect(surface, (50, 150, 80), local_rect, border_radius=8)
                name = card.name[:18]
                atkdef = f"ATK:{card.attack} DEF:{card.defense}"
                surface.blit(font_small.render(name, True, (255,255,255)), (x+8, y+8))
                surface.blit(font_small.render(atkdef, True, (220,220,220)), (x+8, y+30))
            else:
                pygame.draw.rect(surface, (80, 80, 100), local_rect, border_radius=8)
                surface.blit(font_small.render("VACÍO", True, (180,180,180)), (x+8, y+20))

            # Si ya fue seleccionado, marcarlo
            if i in self.tributes_selected:
                overlay = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                overlay.fill((0,0,0,120))
                surface.blit(overlay, (x, y))
                surface.blit(font_small.render("SELECCIONADO", True, (255,200,200)), (x+8, y+btn_h-22))

            # Guardar rect global
            global_rect = pygame.Rect(dialog_rect.x + local_rect.x, dialog_rect.y + local_rect.y, btn_w, btn_h)
            self.tribute_field_choice_rects.append((global_rect, i))

        # Blit
        self.screen.blit(surface, dialog_rect.topleft)
    
    
    def _handle_tribute_selection(self, mouse_pos: Tuple[int, int]):
        """Maneja la selección de monstruos para sacrificar."""
        # Si se está mostrando el diálogo modal de selección de sacrificios, usar sus rects
        if self.tribute_field_choice_rects:
            for rect, idx in self.tribute_field_choice_rects:
                if rect.collidepoint(mouse_pos):
                    card_obj = self.game_state.player.field.get_card_at(idx)
                    if card_obj and idx not in self.tributes_selected:
                        self.pending_tribute_index = idx
                        self.pending_tribute_card_name = card_obj.name
                        self.pending_tribute_card_stats = (card_obj.attack, card_obj.defense)
                        self.confirming_tribute_card = True
                        tributes_needed = self.tributes_needed_required if self.tributes_needed_required > 0 else (
                            2 if self.game_state.player.hand.cards[self.selected_card_hand].stars >= 6 else 1
                        )
                        print(f"Confirmar sacrificio de slot {idx}: {card_obj.name} ({len(self.tributes_selected)}/{tributes_needed} seleccionados)")
                    return

        # Si no hay rects de diálogo (o no hizo click ahí), caer al comportamiento por defecto
        field_card_rects = self.view.get_field_card_rects(self.game_state.player.field, is_player=True)
        tributes_needed = self.tributes_needed_required if self.tributes_needed_required > 0 else (
            2 if self.game_state.player.hand.cards[self.selected_card_hand].stars >= 6 else 1
        )

        for index, card_rect in enumerate(field_card_rects):
            if card_rect and card_rect.collidepoint(mouse_pos):
                card_obj = self.game_state.player.field.get_card_at(index)
                if index not in self.tributes_selected and card_obj:
                    self.pending_tribute_index = index
                    self.pending_tribute_card_name = card_obj.name
                    self.pending_tribute_card_stats = (card_obj.attack, card_obj.defense)
                    self.confirming_tribute_card = True
                    print(f"Confirmar sacrificio de slot {index}: {card_obj.name} ({len(self.tributes_selected)}/{tributes_needed} seleccionados)")
                return
    
    def _handle_sacrifice_confirmation(self, mouse_pos: Tuple[int, int]):
        """Maneja los clics en el diálogo de confirmación de sacrificio."""
        if self.sacrifice_confirm_rect and self.sacrifice_confirm_rect.collidepoint(mouse_pos):
            # Presionó INVOCAR
            empty_slot = self.game_state.player.field.get_empty_slot_index()
            if empty_slot is not None:
                self._invoke_card(
                    self.selected_card_hand,
                    empty_slot,
                    Position.FACE_UP_ATK,
                    self.tributes_selected
                )
            # Limpiar estado
            self.confirming_sacrifice = False
            self.selected_card_hand = None
            self.tributes_selected = []
            self.sacrifice_card_name = ""
            self.sacrifice_card_stats = (0, 0)
            self.sacrifice_monsters_names = []
            self.tributes_needed_required = 0
            return
        
        if self.sacrifice_cancel_rect and self.sacrifice_cancel_rect.collidepoint(mouse_pos):
            # Presionó CERRAR/CANCELAR
            self.confirming_sacrifice = False
            self.selected_card_hand = None
            self.tributes_selected = []
            self.sacrifice_card_name = ""
            self.sacrifice_card_stats = (0, 0)
            self.sacrifice_monsters_names = []
            self.tributes_needed_required = 0
            return

    def _handle_tribute_card_confirmation(self, mouse_pos: Tuple[int, int]):
        """Maneja el diálogo de confirmación de cada carta a sacrificar."""
        # Confirmar sacrificio de la carta pendiente
        if self.confirm_tribute_rect and self.confirm_tribute_rect.collidepoint(mouse_pos):
            # Añadir el índice pendiente a la lista de sacrificios (si no está ya y no excede)
            if self.pending_tribute_index is not None and self.pending_tribute_index not in self.tributes_selected:
                if len(self.tributes_selected) < self.tributes_needed_required:
                    self.tributes_selected.append(self.pending_tribute_index)
                    print(f"Sacrificio confirmado: slot {self.pending_tribute_index}. ({len(self.tributes_selected)}/{self.tributes_needed_required})")
                else:
                    print("Ya se seleccionaron los sacrificios necesarios.")

            # Limpiar el estado pendiente
            self.confirming_tribute_card = False
            self.pending_tribute_index = None
            self.pending_tribute_card_name = ""
            self.pending_tribute_card_stats = (0, 0)

            # Si alcanzamos la cantidad requerida, abrir la confirmación final
            if len(self.tributes_selected) == self.tributes_needed_required:
                card_to_invoke = self.game_state.player.hand.cards[self.selected_card_hand]
                self.sacrifice_card_name = card_to_invoke.name
                self.sacrifice_card_stats = (card_to_invoke.attack, card_to_invoke.defense)
                self.sacrifice_monsters_names = [
                    self.game_state.player.field.get_card_at(idx).name
                    for idx in self.tributes_selected
                ]
                self.confirming_sacrifice = True
                self.selecting_tributes = False

            return

        # Cancelar selección de este sacrificio
        if self.cancel_tribute_rect and self.cancel_tribute_rect.collidepoint(mouse_pos):
            print("Cancelado sacrificio pendiente.")
            self.confirming_tribute_card = False
            self.pending_tribute_index = None
            self.pending_tribute_card_name = ""
            self.pending_tribute_card_stats = (0, 0)
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

        # Verificar que tengamos un slot válido
        if field_slot is None:
            print("No hay slots disponibles para invocar.")
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

        # Aplicar el movimiento, pero comprobar si tuvo efecto
        try:
            prev_state = self.game_state
            new_state = self.game_state.apply_move(move)

            if new_state == prev_state:
                # El movimiento no se aplicó (válido pero sin efecto o inválido)
                print(f"Invocación de {card.name} en slot {field_slot} no se aplicó (movimiento inválido o sin efecto).")
                return

            # Si llegó aquí, el move sí aplicó cambios
            self.game_state = new_state
            print(f"Carta {card.name} invocada en slot {field_slot}.")
            # Marcar que ya se invocó una carta en esta Main Phase
            self.already_summoned = True

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
            
            # Si entramos en Main Phase, robar una carta automáticamente (excepto en el primer turno)
            if next_phase == 'main' and self.game_state.current_turn == 'player':
                # Robar carta: el jugador humano debe robar al entrar en Main Phase, excepto en ronda 1
                if self.round_number > 1:
                    self._draw_card_for_player()
                    print(f"Robaste una carta en Main Phase de ronda {self.round_number}.")
                else:
                    print("Primer turno del jugador: omitiendo robo automático.")
            
            # Si se cambia de turno (change_turn), resetear flag de invocación
            if next_phase == 'change_turn':
                self.already_summoned = False  # Resetear para el próximo turno
                self.round_number += 1
                print(f"Turno cambiado. Ronda/Turno ahora: {self.round_number}")

            if self.game_state.current_turn == 'ai':
                self._execute_ai_turn()
        except Exception as e:
            print(f"Error al aplicar PASS: {e}")

    def _draw_card_for_player(self):
        """Dibuja una carta automáticamente al entrar en Main Phase."""
        if self.game_state.player.deck:
            new_player, drawn_card = self.game_state.player.draw_card()
            self.game_state = replace(self.game_state, player=new_player)
            if drawn_card:
                print(f"Robaste: {drawn_card.name}")
            else:
                print("No hay cartas en el Deck.")
        else:
            print("¡Tu Deck está vacío!")

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
            # Verificar si el juego ha terminado ANTES de procesar input
            if self.game_state.is_game_over() and not hasattr(self, 'game_over_shown'):
                self.game_over_shown = True
                print("¡El juego ha terminado!")
            
            self.handle_input()
            if self.selecting_deck_size:
                self._draw_deck_size_prompt()
                pygame.display.flip()
                self.clock.tick(60)
                continue

            # 1. Dibujar la View principal
            self.view.draw_game(self.game_state, self.round_number)
                  
            # 2. Mostrar mensaje de ya invocó
            if self.show_already_summoned_message:
                self.close_message_rect = self.view.draw_already_summoned_message(self.screen)

            # 2b. Mostrar mensaje "no puedes atacar"
            if self.show_cannot_attack_message:
                self.close_cannot_attack_rect = self.view.draw_cannot_attack_message(self.screen)

            # 2c. Mensaje: monstruo ya atacó
            if self.show_already_attacked_message:
                self.close_already_attacked_rect = self.view.draw_already_attacked_message(self.screen)

            # 3. Mostrar diálogo de selección de objetivo
            if self.attack_target_dialog_active:
                self._draw_attack_target_selection_prompt()
            
            # 4. Otros diálogos
            if self.selecting_position:
                self._draw_position_selection_prompt()
            
            # 4b. Diálogo de selección de sacrificios (elige qué monstruos sacrificar)
            if self.selecting_tributes:
                self._draw_tribute_selection_prompt()
            
            # Dialogo de confirmación por-carta (antes de la confirmación final)
            if self.confirming_tribute_card:
                self._draw_tribute_card_confirmation()

            # === DIÁLOGO DE CONFIRMACIÓN DE SACRIFICIO (final) ===
            if self.confirming_sacrifice:
                self._draw_sacrifice_confirmation_dialog()

            # 5. Mostrar diálogo de selección de sacrificios
            if self.show_tribute_error_message:
                self.close_tribute_error_rect = self.view.draw_tribute_error_message(
                    self.screen, 
                    "Bloqueo de Invocación", 
                    self.tribute_error_message
                )
            else:
                # Asegurarse de que el rect esté limpio cuando no hay mensaje
                self.close_tribute_error_rect = None
            # 6. Mostrar pantalla de Game Over si aplica
            if self.game_state.is_game_over():
                self._draw_game_over_screen()

            if self.error_message:
                message_rect, close_rect = self.view.draw_block_message(
                    self.screen, self.error_message, self.error_title
                )
                self.message_rect = message_rect
                self.close_btn_rect = close_rect
                
                if pygame.time.get_ticks() > self.error_timer:
                    self._close_error_message()
            else:
                self.message_rect = None
                self.close_btn_rect = None

            pygame.display.flip()
        
            # 6. Controlar la tasa de frames
            self.clock.tick(60)

    def _draw_already_summoned_message(self):
        """Dibuja un mensaje de que ya se invocó una carta."""
        font_title = pygame.font.SysFont('Arial', 24, bold=True)
        font_btn = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Crear una superficie para el diálogo
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 80, 400, 160)
        
        # Fondo del diálogo
        dialog_surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        dialog_surface.fill((50, 30, 30))
        pygame.draw.rect(dialog_surface, (200, 50, 50), (0, 0, dialog_rect.width, dialog_rect.height), 3, border_radius=10)
        
        # Título
        title_text = "¡Ya invocaste una carta!"
        title_surf = font_title.render(title_text, True, (255, 100, 100))
        title_rect = title_surf.get_rect(center=(dialog_rect.width // 2, 25))
        dialog_surface.blit(title_surf, title_rect)
        
        # Mensaje
        msg_text = "Solo puedes invocar 1 carta por Main Phase"
        msg_surf = pygame.font.SysFont('Arial', 16).render(msg_text, True, (200, 200, 200))
        msg_rect = msg_surf.get_rect(center=(dialog_rect.width // 2, 65))
        dialog_surface.blit(msg_surf, msg_rect)
        
        # Botón Cerrar
        close_rect_local = pygame.Rect(150, 100, 100, 40)
        pygame.draw.rect(dialog_surface, (100, 100, 200), close_rect_local, border_radius=10)
        close_text = font_btn.render("CERRAR", True, (255, 255, 255))
        dialog_surface.blit(close_text, close_text.get_rect(center=close_rect_local.center))
        
        # Dibujar el diálogo
        self.screen.blit(dialog_surface, dialog_rect.topleft)
        
        # Guardar el rect para detectar clics (en coordenadas globales)
        self.close_message_rect = pygame.Rect(dialog_rect.x + 150, dialog_rect.y + 100, 100, 40)

    def _draw_cannot_attack_message(self):
        """Dibuja un mensaje que indica que no puedes atacar en la primera ronda."""
        font_title = pygame.font.SysFont('Arial', 22, bold=True)
        font_btn = pygame.font.SysFont('Arial', 16)

        dialog_rect = pygame.Rect(SCREEN_WIDTH//2 - 220, SCREEN_HEIGHT//2 - 70, 440, 140)
        dialog_surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        dialog_surface.fill((40, 40, 40))
        pygame.draw.rect(dialog_surface, (180, 100, 100), (0, 0, dialog_rect.width, dialog_rect.height), 2, border_radius=8)

        title_surf = font_title.render("No puedes atacar ahora", True, (255, 200, 100))
        dialog_surface.blit(title_surf, title_surf.get_rect(center=(dialog_rect.width//2, 28)))

        msg = "No puedes atacar en la primera ronda."
        msg_surf = pygame.font.SysFont('Arial', 16).render(msg, True, (220, 220, 220))
        dialog_surface.blit(msg_surf, msg_surf.get_rect(center=(dialog_rect.width//2, 64)))

        # Botón cerrar
        close_local = pygame.Rect((dialog_rect.width//2 - 60, 92, 120, 32))
        pygame.draw.rect(dialog_surface, (100, 120, 200), close_local, border_radius=6)
        close_text = font_btn.render("CERRAR", True, (255, 255, 255))
        dialog_surface.blit(close_text, close_text.get_rect(center=close_local.center))

        # Blit y guardar rect global para detección
        self.screen.blit(dialog_surface, dialog_rect.topleft)
        self.close_cannot_attack_rect = pygame.Rect(dialog_rect.x + close_local.x, dialog_rect.y + close_local.y, close_local.w, close_local.h)

    def _handle_attacker_selection(self, field_index: int):
        """Selecciona un monstruo para atacar en Battle Phase y abre diálogo de objetivo."""
        
        if self.game_state.phase != 'battle':
            print("Solo puedes atacar en Battle Phase.")
            return
        
        if self.round_number == 1:
            self.show_cannot_attack_message = True
            print("No puedes atacar en la primera ronda.")
            return
        
        field = self.game_state.player.field
        card = field.get_card_at(field_index)
        
        if card is None:
            print("No hay carta en ese slot.")
            return
        
        has_attacked = field.get_has_attacked_at(field_index)
        if has_attacked:
            print(f"El monstruo {card.name} ya ha atacado en esta Battle Phase.")
            # Mostrar un diálogo/modal informativo
            self.show_already_attacked_message = True
            return
        
        position = field.get_position_at(field_index)
        if position != Position.FACE_UP_ATK:
            print("Solo monstruos en posición de Ataque pueden atacar.")
            return
        
        # Guardar atacante y abrir diálogo de selección de objetivo
        self.selected_attacker = field_index
        self.attack_target_dialog_active = True
        self.attack_target_rects = []

        # Construir lista de objetivos (monstruos enemigos)
        enemy_field = self.game_state.ai_player.field
        start_x = SCREEN_WIDTH // 2 - 160  # posición base en diálogo (ajusta si quieres)
        start_y = SCREEN_HEIGHT // 2 - 20
        btn_w, btn_h = 120, 50
        padding = 10
        any_enemy = False

        for i in range(enemy_field.MONSTER_SLOTS):
            slot = enemy_field.get_card_at(i)
            if slot:
                any_enemy = True
                # construye rect global para el botón (se usa solo para detectar clicks en diálogo)
                idx = len(self.attack_target_rects)
                x = start_x + idx * (btn_w + padding)
                rect = pygame.Rect(x, start_y, btn_w, btn_h)
                self.attack_target_rects.append((rect, i))

        # Si no hay monstruos, ofrecer ataque directo
        if not any_enemy:
            # posición única para el botón directo
            rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, SCREEN_HEIGHT // 2 - btn_h // 2, btn_w, btn_h)
            self.attack_target_rects.append((rect, -1))

        print(f"Monstruo atacante seleccionado: {card.name} (slot {field_index}). Elige objetivo (diálogo).")
    
    def _handle_attack_target_selection(self, mouse_pos: Tuple[int, int]):
        """Maneja la selección del objetivo de ataque en el diálogo."""
        # Solo permitir si estamos en Battle Phase
        if self.game_state.phase != 'battle' or not self.attack_target_dialog_active or self.selected_attacker is None:
            return

        # Verificar clic en botón CERRAR (nuevo)
        if hasattr(self, 'attack_close_rect') and self.attack_close_rect.collidepoint(mouse_pos):
            print("Ataque cancelado.")
            self.attack_target_dialog_active = False
            self.attack_target_rects = []
            self.selected_attacker = None
            self.attack_close_rect = None
            return

        # Verificar clic en los rectángulos de objetivo
        for rect, target_index in self.attack_target_rects:
            if rect.collidepoint(mouse_pos):
                # Ejecutar ataque usando el flujo estándar: ATTACK move
                self._execute_attack(target_index)
                # cerrar diálogo
                self.attack_target_dialog_active = False
                self.attack_target_rects = []
                self.selected_attacker = None
                return

    def _execute_attack_direct(self):
        """Wrapper para ejecutar ataque directo usando el mismo movimiento ATTACK."""
        if self.game_state.phase != 'battle':
            print("No puedes atacar fuera de Battle Phase.")
            return
        if self.selected_attacker is None:
            return
        self._execute_attack(-1)

    def _draw_attack_target_selection_prompt(self):
        """Dibuja el diálogo con botones para seleccionar el objetivo de ataque y botón cerrar."""
        if not self.attack_target_dialog_active or self.selected_attacker is None:
            return

        font_title = pygame.font.SysFont('Arial', 16, bold=True)  # Reducido de 20
        font_btn = pygame.font.SysFont('Arial', 12)  # Reducido de 16
        font_close = pygame.font.SysFont('Arial', 12, bold=True)
        dialog_w = max(500, len(self.attack_target_rects) * 130)
        dialog_rect = pygame.Rect((SCREEN_WIDTH - dialog_w)//2, SCREEN_HEIGHT//2 - 120, dialog_w, 220)  # Altura aumentada

        # Fondo del diálogo
        dialog_surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        dialog_surface.fill((30, 30, 50))
        pygame.draw.rect(dialog_surface, (120, 120, 140), (0, 0, dialog_rect.width, dialog_rect.height), 2, border_radius=8)

        # Título (reducido)
        attacker_card = self.game_state.player.field.get_card_at(self.selected_attacker)
        title = f"Ataque: {attacker_card.name}" if attacker_card else "Elige objetivo"  # Texto más corto
        title_surf = font_title.render(title, True, (255, 255, 255))
        dialog_surface.blit(title_surf, title_surf.get_rect(center=(dialog_rect.width//2, 15)))

        # Dibujar botones según attack_target_rects (coordenadas relativas al diálogo)
        for idx, (rect_global, target_index) in enumerate(self.attack_target_rects):
            # calcular posición relativa dentro del diálogo
            btn_w, btn_h = 110, 45  # Reducido de 120, 50
            total = len(self.attack_target_rects)
            start_x = (dialog_rect.width - (btn_w * total + 8 * (total - 1))) // 2
            x = start_x + idx * (btn_w + 8)
            y = 50
            btn_rect_local = pygame.Rect(x, y, btn_w, btn_h)

            # texto (reducido y más conciso)
            if target_index == -1:
                txt = "DIRECTO"  # Reducido de "ATACAR DIRECTO"
            else:
                enemy_slot = self.game_state.ai_player.field.get_card_at(target_index)
                enemy_pos = self.game_state.ai_player.field.get_position_at(target_index)
                if enemy_slot:
                    pos_label = "ATK" if enemy_pos == Position.FACE_UP_ATK else "DEF"
                    txt = f"{enemy_slot.name[:10]} ({pos_label})"  # Nombre más corto
                else:
                    txt = f"Slot {target_index}"

            pygame.draw.rect(dialog_surface, (0, 140, 0), btn_rect_local, border_radius=8)
            txt_surf = font_btn.render(txt, True, (255, 255, 255))
            dialog_surface.blit(txt_surf, txt_surf.get_rect(center=btn_rect_local.center))

            # guardar rect global actualizado para detección de clic (coordenadas globales)
            self.attack_target_rects[idx] = (pygame.Rect(dialog_rect.x + btn_rect_local.x,
                                                          dialog_rect.y + btn_rect_local.y,
                                                          btn_w, btn_h),
                                             target_index)

        # Botón CERRAR (nuevo)
        close_btn_w, close_btn_h = 100, 40
        close_btn_x = (dialog_rect.width - close_btn_w) // 2
        close_btn_y = dialog_rect.height - close_btn_h - 15
        close_btn_rect_local = pygame.Rect(close_btn_x, close_btn_y, close_btn_w, close_btn_h)
        
        pygame.draw.rect(dialog_surface, (180, 100, 100), close_btn_rect_local, border_radius=8)
        close_text = font_close.render("CERRAR", True, (255, 255, 255))
        dialog_surface.blit(close_text, close_text.get_rect(center=close_btn_rect_local.center))
        
        # Guardar rect global del botón cerrar para detección de clic
        self.attack_close_rect = pygame.Rect(dialog_rect.x + close_btn_rect_local.x,
                                             dialog_rect.y + close_btn_rect_local.y,
                                             close_btn_w, close_btn_h)

        # Blit diálogo
        self.screen.blit(dialog_surface, dialog_rect.topleft)

    def _handle_attack_target_dialog_click(self, mouse_pos: Tuple[int, int]):
        """Procesa el click sobre el diálogo de selección de objetivo de ataque."""
        if self.game_state.phase != 'battle' or not self.attack_target_dialog_active:
            return

        for rect, target_index in self.attack_target_rects:
            if rect.collidepoint(mouse_pos):
                self._execute_attack(target_index)
                self.attack_target_dialog_active = False
                self.attack_target_rects = []
                self.selected_attacker = None
                return

    def _execute_attack(self, target_index: int):
        """
        Ejecuta un ataque del monstruo seleccionado contra el objetivo especificado.
        
        Args:
            target_index: Índice del monstruo enemigo a atacar, o -1 para ataque directo.
        """
        if self.game_state.phase != 'battle' or self.selected_attacker is None:
            return
        
        attacker_card = self.game_state.player.field.get_card_at(self.selected_attacker)
        if not attacker_card:
            print("No hay monstruo atacante válido.")
            return
        
        # Crear movimiento de ataque
        move = Move(
            action_type=ActionType.ATTACK,
            source_index=self.selected_attacker,
            target_index=target_index
        )
        
        try:
            new_state = self.game_state.apply_move(move)
            self.game_state = new_state
            
            if target_index == -1:
                print(f"{attacker_card.name} realizó ataque directo.")
            else:
                defender_card = self.game_state.ai_player.field.get_card_at(target_index)
                if defender_card:
                    print(f"{attacker_card.name} atacó a {defender_card.name}.")
                else:
                    print(f"{attacker_card.name} atacó al monstruo en slot {target_index}.")
            
            # Limpiar estado de ataque
            self.selected_attacker = None
            self.attack_target_dialog_active = False
            self.attack_target_rects = []
            
        except Exception as e:
            print(f"Error al ejecutar ataque: {e}")

    def _draw_game_over_screen(self):
        """Dibuja la pantalla de Game Over."""
        font_title = pygame.font.SysFont('Arial', 48, bold=True)
        font_msg = pygame.font.SysFont('Arial', 28)
        
        # Determinar ganador
        if self.game_state.player.life_points <= 0:
            title = "¡GAME OVER!"
            winner = "La IA ha ganado"
            winner_color = (255, 150, 50)
        elif self.game_state.ai_player.life_points <= 0:
            title = "¡VICTORIA!"
            winner = "¡Has ganado!"
            winner_color = (50, 255, 50)
        else:
            return  # No hay ganador
        
        # Fondo oscuro semi-transparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Título
        title_surf = font_title.render(title, True, (255, 255, 255))
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)))
        
        # Mensaje del ganador
        winner_surf = font_msg.render(winner, True, winner_color)
        self.screen.blit(winner_surf, winner_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        
        # Mensaje de reinicio
        restart_text = "Cierra la ventana para salir"
        restart_surf = pygame.font.SysFont('Arial', 18).render(restart_text, True, (200, 200, 200))
        self.screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))

    # CÓDIGO AÑADIDO EN GAME_CONTROLLER.PY (al final de la clase)

    def _draw_deck_size_prompt(self):
        """Dibuja el menú de selección de tamaño del deck."""
        font_title = pygame.font.SysFont('Arial', 32, bold=True)
        font_btn = pygame.font.SysFont('Arial', 20, bold=True)
        
        dialog_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300)
        
        dialog_surface = pygame.Surface((dialog_rect.width, dialog_rect.height))
        dialog_surface.fill((30, 30, 50))
        pygame.draw.rect(dialog_surface, (100, 100, 150), (0, 0, dialog_rect.width, dialog_rect.height), 3, border_radius=10)
        
        title_text = "Selecciona el tamaño del Deck"
        title_surf = font_title.render(title_text, True, (255, 255, 255))
        dialog_surface.blit(title_surf, title_surf.get_rect(center=(dialog_rect.width // 2, 40)))
        
        sizes = [15, 20, 40]
        self.size_buttons = []
        
        btn_w, btn_h = 100, 60
        total_w = len(sizes) * btn_w + (len(sizes) - 1) * 20
        start_x = (dialog_rect.width - total_w) // 2
        
        for i, size in enumerate(sizes):
            x_local = start_x + i * (btn_w + 20)
            y_local = 120
            btn_rect_local = pygame.Rect(x_local, y_local, btn_w, btn_h)
            
            color = (0, 150, 0) if size == 40 else (0, 100, 150)
            pygame.draw.rect(dialog_surface, color, btn_rect_local, border_radius=10)
            btn_text = font_btn.render(str(size), True, (255, 255, 255))
            dialog_surface.blit(btn_text, btn_text.get_rect(center=btn_rect_local.center))
            
            # Guardar rect global
            self.size_buttons.append((pygame.Rect(dialog_rect.x + x_local, dialog_rect.y + y_local, btn_w, btn_h), size))
            
        self.screen.blit(dialog_surface, dialog_rect.topleft)

    def _handle_deck_size_selection(self, mouse_pos: Tuple[int, int]):
        """Maneja el clic en los botones de selección de tamaño de deck, inicializa el juego y roba manos."""
        if not self.selecting_deck_size:
            return

        for rect, size in self.size_buttons:
            if rect.collidepoint(mouse_pos):
                self.deck_size_selected = size
                self.selecting_deck_size = False
                print(f"Tamaño de deck seleccionado: {size}")
                
                try:
                    # 1. Inicializar decks (Crea decks de tamaño 'size')
                    self.game_state = self.game_state.reinitialize_decks(size) 
                    
                    # 2. El jugador humano roba su mano inicial (5 cartas)
                    # La función draw_starting_hand() maneja el robo de las 5 cartas
                    new_player, _ = self.game_state.player.draw_starting_hand()
                    
                    # 3. La IA roba su mano inicial (5 cartas)
                    new_ai, _ = self.game_state.ai_player.draw_starting_hand()
                    
                    # 4. Actualizar el GameState con los nuevos estados de Player y AI
                    self.game_state = replace(self.game_state, player=new_player, ai_player=new_ai)

                    # 5. Iniciar el juego en Draw Phase
                    self.game_state = replace(self.game_state, phase='draw', current_turn='player')
                    print("Juego inicializado. Jugador comienza en Draw Phase.")
                
                except AttributeError as e:
                    # Esto ocurre si no implementaste draw_starting_hand o reinitialize_decks
                    print(f"ERROR: Falta implementar métodos esenciales en el Modelo: {e}")
                    self.selecting_deck_size = True
                
                except Exception as e:
                     print(f"ERROR: Fallo durante la inicialización: {e}")
                     self.selecting_deck_size = True
                     
                return
            
