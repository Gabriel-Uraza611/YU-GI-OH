'''
Módulo para cargar y manejar cartas desde archivos JSON.

Este módulo proporciona funciones para cargar datos de cartas desde archivos
JSON y convertirlos en instancias de la clase Card, facilitando la gestión
de mazos y colecciones de cartas en juegos de cartas coleccionables.
'''
import json
from .fusions import FusionRecipe


def load_cards(filepath: str)-> dict:

    """
    Carga recetas de fusión desde un archivo JSON.

    Args:
        filepath: Ruta al archivo JSON con los datos de las recetas
  
    Returns:
        list: Lista de objetos FusionRecipe cargados
    """

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    except FileNotFoundError:
        print(f"Error: El archivo de fusiones no se encontró en la ruta: {filepath}")
        return []

    except json.JSONDecodeError:
        print(f"Error: El archivo {filepath} tiene un formato JSON inválido.")
        return []

    all_recipes = []
    for recipe_data in data:
        try:
            # Crear la receta con los tres IDs de material/resultado
            recipe = FusionRecipe(
                material_1_id=recipe_data['material_1_id'],
                material_2_id=recipe_data['material_2_id'],
                result_id=recipe_data['result_id'],
            )

            all_recipes.append(recipe)

        except KeyError as e:
            print(f"Advertencia: Receta incompleta, falta campo: {e}")
            continue
        except Exception as e:
            print(f"Error inesperado al procesar receta: {e}")
            continue

    print(f"Las {len(all_recipes)} recetas han sido cargadas correctamente desde {filepath}.")
    return all_recipes
