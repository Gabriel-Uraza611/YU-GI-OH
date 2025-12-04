import pygame
from typing import Tuple

# Importamos las clases clave del Model para saber qué dibujar
from model.game.gamestate import GameState
from model.cards.card import Card
from model.game.move import Position

# --- Dimensiones y Colores ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_WIDTH = 90
CARD_HEIGHT = 130
SLOT_SIZE = 100
SLOT_PADDING = 10
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
        
    def draw_game(self, game_state: GameState):
        """
        Dibuja todos los componentes del juego en base al GameState actual.
        """
        self.screen.fill(COLOR_BG)
        
        # 1. Dibujar el campo de juego central (compartido)
        self._draw_field_background()
        
        # 2. Dibujar zonas y cartas del Jugador
        self._draw_player_areas(game_state.player, True, (SCREEN_HEIGHT // 2) + 20)
        self._draw_monster_slots(game_state.player.field.monsters, True)
        self._draw_hand(game_state.player.hand.cards, True)
        
        # 3. Dibujar zonas y cartas del Oponente (IA)
        self._draw_player_areas(game_state.ai_player, False, (SCREEN_HEIGHT // 2) - SLOT_SIZE - 20)
        self._draw_monster_slots(game_state.ai_player.field.monsters, False)
        self._draw_hand(game_state.ai_player.hand.cards, False) # Manos de la IA se dibujan como dorsos
        
        # 4. Dibujar información de turno y LP
        self._draw_info_panel(game_state)
        
        pygame.display.flip()

    def _draw_field_background(self):
        """Dibuja el área rectangular del campo de juego."""
        field_rect = pygame.Rect(
            (SCREEN_WIDTH - 5 * SLOT_SIZE - 4 * SLOT_PADDING) // 2, 
            SCREEN_HEIGHT // 2 - SLOT_SIZE - 10, # Un poco arriba de la mitad
            5 * SLOT_SIZE + 4 * SLOT_PADDING, 
            2 * SLOT_SIZE + 2 * SLOT_PADDING + 20 # Espacio para 2 filas de slots
        )
        pygame.draw.rect(self.screen, COLOR_FIELD_BG, field_rect, border_radius=10)

    def _draw_player_areas(self, player, is_player_turn: bool, y_start: int):
        """Dibuja los LP, Deck y Graveyard."""
        
        # LP Box
        lp_x = 20
        lp_y = y_start - 30 if is_player_turn else y_start + SLOT_SIZE + 10
        lp_text = self.font_lp.render(f"LP: {player.life_points}", True, (255, 255, 255))
        self.screen.blit(lp_text, (lp_x, lp_y))
        
        # Deck
        deck_x = SCREEN_WIDTH - CARD_WIDTH - 20
        deck_y = y_start + SLOT_PADDING
        deck_rect = pygame.Rect(deck_x, deck_y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_CARD_BACK, deck_rect, border_radius=5)
        deck_count = self.font_small.render(f"Deck: {len(player.deck)}", True, (255, 255, 255))
        self.screen.blit(deck_count, (deck_x, deck_y + CARD_HEIGHT + 5))


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
                card, position = slot
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

    def _draw_card_in_field(self, card: Card, rect: pygame.Rect, is_rotated: bool):
        """Dibuja la representación gráfica de una carta en el campo."""
        
        # 1. Fondo de la carta
        pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=5)
        
        # 2. Nombre
        name_surface = self.font_small.render(card.name, True, (0, 0, 0))
        text_rect = name_surface.get_rect(center=(rect.centerx, rect.y + 10))
        self.screen.blit(name_surface, text_rect)
        
        # 3. Stats (en un rectángulo central simulando imagen/arte)
        stat_rect = pygame.Rect(rect.x + 5, rect.y + 20, rect.width - 10, rect.height - 40)
        pygame.draw.rect(self.screen, (100, 100, 100), stat_rect)
        
        # 4. ATK/DEF en la parte inferior
        stat_text = self.font_small.render(f"ATK:{card.attack}/DEF:{card.defense}", True, (255, 255, 255))
        stat_text_rect = stat_text.get_rect(center=(rect.centerx, rect.bottom - 10))
        self.screen.blit(stat_text, stat_text_rect)
        
        # Si está rotada, solo para simular la rotación visualmente (Pygame real manejaría la rotación del Surface)
        if is_rotated:
             pygame.draw.line(self.screen, (255, 0, 0), rect.topleft, rect.bottomright, 2)
             
    def _draw_hand(self, cards: Tuple[Card, ...], is_player: bool):
        """
        Dibuja las cartas en la mano. Para el oponente, solo dibuja el dorso.
        """
        if is_player:
            y_row = SCREEN_HEIGHT - CARD_HEIGHT - 20
            start_x = (SCREEN_WIDTH - len(cards) * (CARD_WIDTH + SLOT_PADDING) + SLOT_PADDING) // 2
            
            for i, card in enumerate(cards):
                x = start_x + i * (CARD_WIDTH + SLOT_PADDING)
                rect = pygame.Rect(x, y_row, CARD_WIDTH, CARD_HEIGHT)
                self._draw_card_in_hand(card, rect)
        else:
            # Dibujar solo dorsos de la IA en la parte superior
            y_row = 20
            start_x = (SCREEN_WIDTH - len(cards) * (CARD_WIDTH + SLOT_PADDING) + SLOT_PADDING) // 2
            
            for i, card in enumerate(cards):
                x = start_x + i * (CARD_WIDTH + SLOT_PADDING)
                rect = pygame.Rect(x, y_row, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, COLOR_CARD_BACK, rect, border_radius=5)
                # Opcional: Escribir el contador en el centro
                count_text = self.font_small.render(f"{len(cards)}", True, (255, 255, 255))
                self.screen.blit(count_text, count_text.get_rect(center=rect.center))

    def _draw_card_in_hand(self, card: Card, rect: pygame.Rect):
        """Dibuja la representación detallada de una carta en la mano del jugador."""
        # 1. Fondo de la carta (similar al campo, pero con dimensiones de mano)
        pygame.draw.rect(self.screen, (220, 220, 220), rect, border_radius=5)
        
        # 2. Nombre
        name_surface = self.font_small.render(card.name, True, (0, 0, 0))
        text_rect = name_surface.get_rect(center=(rect.centerx, rect.y + 10))
        self.screen.blit(name_surface, text_rect)
        
        # 3. Stats
        stat_text = self.font_small.render(f"{card.attack}/{card.defense}", True, (50, 50, 50))
        stat_text_rect = stat_text.get_rect(center=(rect.centerx, rect.bottom - 10))
        self.screen.blit(stat_text, stat_text_rect)

    def _draw_info_panel(self, game_state: GameState):
        """Dibuja el turno y el estado general."""
        
        # Indicador de Turno
        turn_text = f"Turno Actual: {game_state.current_turn.upper()}"
        color = (255, 255, 0) if game_state.current_turn == 'player' else (255, 165, 0)
        
        text_surface = self.font_lp.render(turn_text, True, color)
        self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, 5))
        
        # Mensaje del juego (Placeholder, debería venir del Controller)
        message = f"Fase: {game_state.phase.upper()}"
        message_surface = self.font_small.render(message, True, (200, 200, 200))
        self.screen.blit(message_surface, (SCREEN_WIDTH // 2 - message_surface.get_width() // 2, 35))
        
        # Botón de "Pass/End Phase"
        self.pass_button_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2 - 25, 120, 50)
        pygame.draw.rect(self.screen, (0, 150, 0), self.pass_button_rect, border_radius=10)
        button_text = self.font_lp.render("PASS", True, (255, 255, 255))
        self.screen.blit(button_text, button_text.get_rect(center=self.pass_button_rect.center))

    def get_pass_button_rect(self) -> pygame.Rect:
        """Devuelve el rectángulo del botón PASS para la detección de clics."""
        # Se asume que este método es llamado DESPUÉS de _draw_info_panel
        return self.pass_button_rect