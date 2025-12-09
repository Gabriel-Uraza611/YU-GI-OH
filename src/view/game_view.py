import os
import pygame
from typing import Tuple

# Importamos las clases clave del Model para saber qué dibujar
from model.game.gamestate import GameState
from model.cards.card import Card
from model.game.move import Position

# --- Dimensiones y Colores ---
SCREEN_WIDTH = 1336
SCREEN_HEIGHT = 768
CARD_WIDTH = 125
CARD_HEIGHT = 180
SLOT_SIZE = 150
SLOT_PADDING = 15
COLOR_BG = (40, 40, 60)         # Fondo azul oscuro
COLOR_FIELD_BG = (50, 80, 50)   # Fondo de campo verde oscuro
COLOR_CARD_BACK = (150, 10, 10) # Rojo oscuro (Dorso de la carta)

class GameView:
    """
    Clase responsable de dibujar el estado del juego (GameState) en pantalla.
    """
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame.font.init()
        self.font_small = pygame.font.SysFont('Arial', 14)
        self.font_lp = pygame.font.SysFont('Arial', 24, bold=True)
        self.round_number = 1  # Número de ronda actual

        # Cache de imágenes de cartas
        self.image_cache = {}
        # Ruta a assets/images — desde src/view subir dos niveles hasta la raíz del repo
        self.assets_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'images'))

    def _load_card_image(self, filename: str, size: Tuple[int, int]) -> pygame.Surface | None:
        """Carga y cachea una imagen de carta. `filename` es solo el nombre de archivo."""
        if not filename:
            return None
        key = (filename, size)
        if key in self.image_cache:
            return self.image_cache[key]
        path = os.path.join(self.assets_dir, filename)
        if not os.path.exists(path):
            return None
        try:
            surf = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.smoothscale(surf, size)
            self.image_cache[key] = surf
            return surf
        except Exception:
            return None

    def draw_game(self, game_state: GameState, round_number: int = 1):
        """
        Dibuja todos los componentes del juego en base al GameState actual.
        """
        self.round_number = round_number
        self.screen.fill(COLOR_BG)
        
        # 1. Dibujar el campo de juego central (compartido)
        self._draw_field_background()
        
        # 2. Dibujar zonas y cartas del Oponente (IA) - deck y cementerio, y su mano visible
        self._draw_player_areas(game_state.ai_player, False, (SCREEN_HEIGHT // 2) - SLOT_SIZE - 20)
        self._draw_monster_slots(game_state.ai_player.field.monsters, False)
        self._draw_hand(game_state.ai_player.hand.cards, False)
        
        # 3. Dibujar zonas y cartas del Jugador - deck, cementerio y mano
        self._draw_player_areas(game_state.player, True, (SCREEN_HEIGHT // 2) + 20)
        self._draw_monster_slots(game_state.player.field.monsters, True)
        self._draw_hand(game_state.player.hand.cards, True)
        
        # 4. Dibujar panel de LP (arriba, pequeño)
        self._draw_lp_panel(game_state)
        
        # 5. Dibujar la info (turno/phase/round) en la parte inferior derecha
        self._draw_info_panel(game_state)
        
        # Dibujar botón PASS en esquina superior derecha (visible y clickable)
        btn_w, btn_h = 100, 36
        btn_x = SCREEN_WIDTH - btn_w - 16
        btn_y = 8
        self.pass_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (0, 150, 0), self.pass_button_rect, border_radius=8)
        button_text = self.font_small.render("PASS", True, (255, 255, 255))
        self.screen.blit(button_text, button_text.get_rect(center=self.pass_button_rect.center))

    def _draw_field_background(self):
        """Dibuja el área rectangular del campo de juego."""
        field_width = 5 * SLOT_SIZE + 4 * SLOT_PADDING
        field_height = 2 * SLOT_SIZE + SLOT_PADDING + 40

        field_rect = pygame.Rect(
            (SCREEN_WIDTH - field_width) // 2,
            (SCREEN_HEIGHT - field_height) // 2,
            field_width,
            field_height
        )
        pygame.draw.rect(self.screen, COLOR_FIELD_BG, field_rect, border_radius=10)

    def _draw_player_areas(self, player, is_player_turn: bool, y_start: int):
        """Dibuja Deck y Cementerio; el cementerio muestra la carta más reciente (top)."""

        # Deck (lado derecho)
        deck_x = SCREEN_WIDTH - CARD_WIDTH - 20
        deck_y = y_start + SLOT_PADDING
        deck_rect = pygame.Rect(deck_x, deck_y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_CARD_BACK, deck_rect, border_radius=5)

        if deck_y < SCREEN_HEIGHT // 2:
            text_y = deck_y - 20   # texto arriba
        else:
            text_y = deck_y + CARD_HEIGHT + 15  # texto abajo

        deck_count = self.font_small.render(f"Deck: {len(player.deck)}", True, (255, 255, 255))
        self.screen.blit(deck_count, (deck_x, text_y))

        # Cementerio (lado izquierdo)
        graveyard_x = 20
        graveyard_y = y_start + SLOT_PADDING
        graveyard_rect = pygame.Rect(graveyard_x, graveyard_y, CARD_WIDTH, CARD_HEIGHT)

        pygame.draw.rect(self.screen, (60, 60, 80), graveyard_rect, border_radius=5)
        pygame.draw.rect(self.screen, (120, 120, 160), graveyard_rect, 2, border_radius=5)

        # Mostrar carta superior del cementerio
        try:
            if player.graveyard:
                top_card = player.graveyard[-1]
                img = self._load_card_image(top_card.image, (CARD_WIDTH, CARD_HEIGHT))
                if img:
                    self.screen.blit(img, graveyard_rect.topleft)
                else:
                    pygame.draw.rect(self.screen, (90, 90, 110), graveyard_rect, border_radius=5)
        except Exception:
            pass

        # Si el cementerio está en la mitad superior, mover texto ARRIBA del rectángulo
        if graveyard_y < SCREEN_HEIGHT // 2:
            text_y = graveyard_y - 20   # texto arriba
        else:
            text_y = graveyard_y + CARD_HEIGHT + 15  # texto abajo

        graveyard_count = self.font_small.render(f"GY: {len(player.graveyard)}", True, (255, 255, 255))
        self.screen.blit(graveyard_count, (graveyard_x, text_y))



    def _draw_monster_slots(self, monsters: Tuple[Tuple[Card, Position] | None, ...], is_player: bool):
        """
        Dibuja los slots de monstruos y las cartas en ellos.
        """
        y_center = SCREEN_HEIGHT // 2
        
        # La zona del jugador va abajo, la del oponente va arriba
        y_row = y_center + 10 if is_player else y_center - SLOT_SIZE - 10
        
        start_x = (SCREEN_WIDTH - len(monsters) * SLOT_SIZE - (len(monsters) - 1) * SLOT_PADDING) // 2
        
        for i, slot in enumerate(monsters):
            x = start_x + i * (SLOT_SIZE + SLOT_PADDING)
            slot_rect = pygame.Rect(x, y_row, SLOT_SIZE, SLOT_SIZE)
            pygame.draw.rect(self.screen, (30, 30, 30), slot_rect, 1, border_radius=5) # Borde del slot
            
            if slot is not None:
                card, position, has_attacked = slot
                # Ajustar las dimensiones de la carta para que quepa en el slot
                card_rect = pygame.Rect(x + 5, y_row + 5, SLOT_SIZE - 10, SLOT_SIZE - 10)
                
                # Rotar la carta si está en FACE_UP_DEF
                is_rotated = position == Position.FACE_UP_DEF
                
                # Dibujar la carta
                self._draw_card_in_field(card, card_rect, is_rotated)
                
                # Dibujar un indicador de posición
                pos_text = position.name.split('_')[-1]
                color = (0, 255, 0) if pos_text == 'ATK' else (0, 150, 255)
                text_surface = self.font_small.render(pos_text, True, color)
                self.screen.blit(text_surface, (x + 5, y_row + 5))

                # Puedes indicar visualmente si ya atacó (por ejemplo, atenuar)
                if has_attacked:
                    # dibujar overlay sutil para indicar que ya atacó
                    overlay = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 100))
                    self.screen.blit(overlay, card_rect.topleft)

    def _draw_card_in_field(self, card: Card, rect: pygame.Rect, is_rotated: bool):
        """Dibuja la representación gráfica de una carta en el campo."""
        # 1. Fondo de la carta
        pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=5)

        # 2. Nombre
        name_surface = self.font_small.render(card.name[:15], True, (0, 0, 0))
        text_rect = name_surface.get_rect(center=(rect.centerx, rect.y + 5))
        self.screen.blit(name_surface, text_rect)

        # 3. Imagen/arte (si existe) — ocupa el área central del slot
        stat_rect = pygame.Rect(rect.x + 5, rect.y + 28, rect.width - 10, rect.height - 50)
        img = self._load_card_image(card.image, (stat_rect.width, stat_rect.height))
        if img:
            self.screen.blit(img, stat_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (100, 100, 100), stat_rect)

        # 4. ATK/DEF en la parte inferior
        stat_text = self.font_small.render(f"ATK:{card.attack}", True, (255, 255, 255))
        stat_text_rect = stat_text.get_rect(center=(rect.centerx, rect.bottom - 15))
        self.screen.blit(stat_text, stat_text_rect)

        def_text = self.font_small.render(f"DEF:{card.defense}", True, (255, 255, 255))
        def_text_rect = def_text.get_rect(center=(rect.centerx, rect.bottom - 5))
        self.screen.blit(def_text, def_text_rect)

        # Si está rotada, mostrar indicador visual
        if is_rotated:
             pygame.draw.line(self.screen, (255, 0, 0), rect.topleft, rect.bottomright, 2)

    def _draw_hand(self, cards: Tuple[Card, ...], is_player: bool):
        """
        Dibuja las cartas en la mano.
        - Jugador: cartas completas en la parte inferior.
        - IA: mostrar las cartas visibles (caras) en la parte superior.
        """
        if is_player:
            y_row = SCREEN_HEIGHT - CARD_HEIGHT - 20
            total_width = len(cards) * (CARD_WIDTH + SLOT_PADDING) - SLOT_PADDING
            start_x = (SCREEN_WIDTH - total_width) // 2
            for i, card in enumerate(cards):
                x = start_x + i * (CARD_WIDTH + SLOT_PADDING)
                rect = pygame.Rect(x, y_row, CARD_WIDTH, CARD_HEIGHT)
                self._draw_card_in_hand(card, rect)
        else:
            # Mostrar la mano de la IA (caras visibles) en la parte superior
            y_row = 20
            total_width = len(cards) * (CARD_WIDTH + SLOT_PADDING) - SLOT_PADDING
            start_x = (SCREEN_WIDTH - total_width) // 2
            for i, card in enumerate(cards):
                x = start_x + i * (CARD_WIDTH + SLOT_PADDING)
                rect = pygame.Rect(x, y_row, CARD_WIDTH, CARD_HEIGHT)
                # Usamos la misma representación de mano para que el jugador vea la carta
                self._draw_card_in_hand(card, rect)

    def _draw_card_in_hand(self, card: Card, rect: pygame.Rect):
        """Dibuja la representación detallada de una carta en la mano del jugador."""
        # 1. Fondo de la carta (similar al campo, pero con dimensiones de mano)
        pygame.draw.rect(self.screen, (220, 220, 220), rect, border_radius=5)

        # 1.5 Imagen (si existe) — ocupa la parte media/alta de la carta
        img_rect = pygame.Rect(rect.x + 5, rect.y + 28, rect.width - 10, rect.height - 60)
        img = self._load_card_image(card.image, (img_rect.width, img_rect.height))
        if img:
            self.screen.blit(img, img_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (180, 180, 180), img_rect)

        # 2. Nombre
        name_surface = self.font_small.render(card.name[:12], True, (0, 0, 0))
        text_rect = name_surface.get_rect(center=(rect.centerx, rect.y + 8))
        self.screen.blit(name_surface, text_rect)

        # 3. Stats
        stat_text = self.font_small.render(f"A:{card.attack} D:{card.defense}", True, (50, 50, 50))
        stat_text_rect = stat_text.get_rect(center=(rect.centerx, rect.bottom - 8))
        self.screen.blit(stat_text, stat_text_rect)

    def _draw_info_panel(self, game_state: GameState):
        """Dibuja turno, fase y ronda en la esquina inferior derecha (panel compacto)."""
        panel_w = 300
        panel_h = 64
        padding = 12
        panel_x = SCREEN_WIDTH - panel_w - 12
        panel_y = SCREEN_HEIGHT - panel_h - 12

        # Fondo semi-transparente para mayor contraste sin tapar información
        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 180))  # color negro translúcido
        self.screen.blit(overlay, (panel_x, panel_y))

        # Texto: Turno (arriba)
        turn_text = f"Turno: {game_state.current_turn.upper()}"
        turn_color = (255, 255, 160) if game_state.current_turn == 'player' else (255, 200, 120)
        turn_surf = self.font_small.render(turn_text, True, turn_color)
        self.screen.blit(turn_surf, (panel_x + padding, panel_y + 8))

        # Texto: Fase (medio)
        phase_text = f"Fase: {game_state.phase.upper()}"
        phase_surf = self.font_small.render(phase_text, True, (200, 200, 200))
        self.screen.blit(phase_surf, (panel_x + padding, panel_y + 28))

        # Texto: Ronda (abajo)
        round_text = f"Ronda: {self.round_number}"
        round_surf = self.font_small.render(round_text, True, (180, 220, 180))
        self.screen.blit(round_surf, (panel_x + padding, panel_y + 44))

        # Nota: el botón PASS continúa estando donde definiste antes (top-right).

    def _draw_lp_panel(self, game_state: GameState):
        """Dibuja los LP de ambos jugadores sin recuadro (texto plano)."""
        panel_y = 44  # misma posición que antes (debajo del header)
        # PLAYER LP (izquierda)
        player_lp_text = f"PLAYER LP: {game_state.player.life_points}"
        player_color = (200, 255, 200) if game_state.player.life_points > 0 else (255, 120, 120)
        player_surf = self.font_small.render(player_lp_text, True, player_color)
        self.screen.blit(player_surf, (12, panel_y + 6))

        # AI LP (derecha)
        ai_lp_text = f"AI LP: {game_state.ai_player.life_points}"
        ai_color = (200, 255, 200) if game_state.ai_player.life_points > 0 else (255, 120, 120)
        ai_surf = self.font_small.render(ai_lp_text, True, ai_color)
        self.screen.blit(ai_surf, (SCREEN_WIDTH - ai_surf.get_width() - 12, panel_y + 6))

        # Nota: no dibujamos separación central para no tapar estadísticas

    def get_pass_button_rect(self) -> pygame.Rect:
        """Devuelve el rectángulo del botón PASS para la detección de clics."""
        # Se asume que este método es llamado DESPUÉS de _draw_info_panel
        return getattr(self, 'pass_button_rect', pygame.Rect(0, 0, 0, 0))
    
    def get_hand_card_rects(self, hand_cards, is_player: bool):
        """
        Devuelve una lista de rectángulos para cada carta en la mano.
        Permite detectar clics en cartas de la mano.
        """
        rects = []
        if is_player:
            hand_y = SCREEN_HEIGHT - CARD_HEIGHT - 20
            total_width = len(hand_cards) * (CARD_WIDTH + SLOT_PADDING) - SLOT_PADDING
            start_x = (SCREEN_WIDTH - total_width) // 2
            for i in range(len(hand_cards)):
                x = start_x + i * (CARD_WIDTH + SLOT_PADDING)
                rect = pygame.Rect(x, hand_y, CARD_WIDTH, CARD_HEIGHT)
                rects.append(rect)
        else:
            # IA en la parte superior
            hand_y = 20
            total_width = len(hand_cards) * (CARD_WIDTH + SLOT_PADDING) - SLOT_PADDING
            start_x = (SCREEN_WIDTH - total_width) // 2
            for i in range(len(hand_cards)):
                x = start_x + i * (CARD_WIDTH + SLOT_PADDING)
                rect = pygame.Rect(x, hand_y, CARD_WIDTH, CARD_HEIGHT)
                rects.append(rect)

        return rects
    
    def get_field_card_rects(self, field, is_player: bool):
        """
        Devuelve una lista de rectángulos para cada slot de monstruo.
        Permite detectar clics en cartas del campo.
        """
        rects = []
        field_y = (SCREEN_HEIGHT // 2) + 20 if is_player else (SCREEN_HEIGHT // 2) - SLOT_SIZE - 20
        
        # Distribuir slots horizontalmente
        total_width = 5 * SLOT_SIZE + 4 * SLOT_PADDING
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        for i in range(5):  # 5 slots de monstruo
            x = start_x + i * (SLOT_SIZE + SLOT_PADDING)
            rect = pygame.Rect(x, field_y, SLOT_SIZE, SLOT_SIZE)
            rects.append(rect)
        
        return rects