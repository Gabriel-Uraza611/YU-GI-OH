'''
En esta clase se definen los atributos de cada carta y el metodo __repr__ para representar 
la carta como una cadena de texto.
'''

class Card:
    '''
    Clase que representa una carta con sus atributos.
    '''

    def __init__(self, name:str, number:str, category:str, attack:int, defense:int, level:int):

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
        self.category = category
        self.attack = attack
        self.defense = defense
        self.level = level

    def __repr__(self):

        return (
            f"Card(name: {self.name}, number: {self.number}, "
            f"category: {self.category}, ATK: {self.attack}, "
            f"DEF: {self.defense}, lv: {self.level})"
        )

    def __str__(self):
        return (
            f"╔══════════════════════╗\n"
            f"║ {self.name:^20} ║\n"
            f"╠══════════════════════╣\n"
            f"║ #{self.number:<18} ║\n"
            f"║ {self.category:<20} ║\n"
            f"╠══════════════════════╣\n"
            f"║ ATK: {self.attack:<6} DEF: {self.defense:<4} ║\n"
            f"║ Lv: {self.level:<17} ║\n"
            f"╚══════════════════════╝"
        )
