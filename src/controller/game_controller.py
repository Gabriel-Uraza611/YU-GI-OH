import pygame
import sys
from typing import Optional

# Importaciones del Model
from model.game.gamestate import GameState
from model.game.move import Move, ActionType, Position
from model.game.player import Player

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
                
                # Ejemplo de manejo de botón PASS (para simplificar el turno)
                if self.game_state.current_turn == 'player':
                    pass_button_rect = self.view.get_pass_button_rect()
                    if pass_button_rect.collidepoint(mouse_pos):
                        self._handle_pass_action()
                        
                # Aquí iría la lógica más compleja:
                # 1. Detectar si hizo clic en una carta de la mano (para invocar)
                # 2. Detectar si hizo clic en una carta del campo (para atacar/cambiar posición)

    def _handle_pass_action(self):
        """
        Aplica el movimiento de PASS al GameState.
        """
        print("Jugador presionó PASS.")
        
        # El movimiento de PASS cambia la fase y/o el turno
        pass_move = Move(action_type=ActionType.PASS, target_zone='turn')
        
        # Aplicamos el movimiento al estado (función que debe estar en GameState)
        self.game_state = self.game_state.apply_move(pass_move)
        
        # Si el turno cambia a la IA, la ejecutamos inmediatamente
        if self.game_state.current_turn == 'ai':
            self._execute_ai_turn()

    def _execute_ai_turn(self):
        """
        Ejecuta el turno completo de la IA.
        """
        print("Ejecutando turno de la IA...")
        # Llama a la lógica compleja de MiniMax (implementada en ai_controller)
        self.game_state = self.ai_controller.execute_ai_turn(self.game_state)
        print("Turno de la IA finalizado.")

    def run(self):
        """
        Bucle principal del juego.
        """
        while self.running:
            self.handle_input()
            
            # 1. Actualizar el Model (ya se hace en handle_input con apply_move)
            
            # 2. Dibujar la View
            self.view.draw_game(self.game_state)
            
            # 3. Controlar la tasa de frames
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()