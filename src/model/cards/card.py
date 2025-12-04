'''
En esta clase se definen los atributos de cada carta y el metodo __repr__ para representar 
la carta como una cadena de texto.
'''

class Card:
    '''
    Clase que representa una carta con sus atributos.
    '''

    def __init__(self, name:str, number:str, attack:int, defense:int):

        """
        Args:
            name: Nombre de la carta
            number: Número identificador
            category: Categoría (monster/spell/trap)
            attack: Puntos de ataque
            defense: Puntos de defensa
            level: Nivel de la carta
        """

        self.name = name
        self.number = number
        self.attack = attack
        self.defense = defense

    def __repr__(self):

        return (
            f"Card(name: {self.name}, number: {self.number}, "
            f"ATK: {self.attack}, DEF: {self.defense})"
        )

    def __str__(self):
        return (
            f"╔══════════════════════╗\n"
            f"║ {self.name:^20} ║\n"
            f"╠══════════════════════╣\n"
            f"║ #{self.number:<18} ║\n"
            f"╠══════════════════════╣\n"
            f"║ ATK: {self.attack:<6} ║\n"
            f"║ DEF: {self.defense:<6} ║\n" 
            f"╚══════════════════════╝"
        )
