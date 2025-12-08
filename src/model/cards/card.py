'''
En esta clase se definen los atributos de cada carta y el metodo __repr__ para representar 
la carta como una cadena de texto.
'''

from typing import Optional

class Card:
    '''
    Clase que representa una carta con sus atributos.
    '''

    def __init__(self, name: str, number: str, attack: int, defense: int, stars: int = 3, image: Optional[str] = None):

        """
        Args:
            name: Nombre de la carta
            number: Número identificador
            attack: Puntos de ataque
            defense: Puntos de defensa
            stars: Número de estrellas (nivel) para invocación. Default 3.
            image: Nombre de archivo de la imagen dentro de assets/images (opcional)
        """

        self.name = name
        self.number = number
        self.attack = attack
        self.defense = defense
        self.stars = stars
        self.position = 'atk'  # 'atk' o 'def' (ataque o defensa)
        self.image = image

    def __repr__(self):

        return (
            f"Card(name: {self.name}, number: {self.number}, "
            f"ATK: {self.attack}, DEF: {self.defense}, Stars: {self.stars})"
        )

    def __str__(self):
        return (
            f"╔══════════════════════╗\n"
            f"║ {self.name:^20} ║\n"
            f"╠══════════════════════╣\n"
            f"║ #{self.number:<18} ║\n"
            f"║ ★ {'x' + str(self.stars):<17} ║\n"
            f"╠══════════════════════╣\n"
            f"║ ATK: {self.attack:<6} ║\n"
            f"║ DEF: {self.defense:<6} ║\n" 
            f"╚══════════════════════╝"
        )
