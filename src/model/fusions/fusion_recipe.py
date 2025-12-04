'''
Este modulo define la estructura y funcionalidad para manejar recetas de fusión entre cartas.
'''

from cards.card import Card

class FusionRecipe:
    """Define la estructura de una receta de fusión."""

    def __init__(self, material_1_id: str, material_2_id: str, result_id: str):
        self.material_1_id = material_1_id
        self.material_2_id = material_2_id
        self.result_id = result_id

    def __repr__(self):
        return f"FusionRecipe({self.material_1_id} + {self.material_2_id} -> {self.result_id})"

def get_fusion_result(card1: Card, card2: Card, all_recipes: list[FusionRecipe]) -> str | None:

    """
    Busca si dos cartas dadas (card1, card2) coinciden con alguna receta.
    La búsqueda se realiza por coincidencia exacta de códigos (strings).
    """

    code1 = card1.number
    code2 = card2.number

    for recipe in all_recipes:
        is_match_ab = (code1 == recipe.material_1_id and code2 == recipe.material_2_id)
        is_match_ba = (code1 == recipe.material_2_id and code2 == recipe.material_1_id)
        if is_match_ab or is_match_ba:
            return recipe.result_id # Devuelve el código de la carta resultante

    return None
