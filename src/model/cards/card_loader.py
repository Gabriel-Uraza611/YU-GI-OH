'''
Módulo para cargar y manejar cartas desde archivos JSON.

Este módulo proporciona funciones para cargar datos de cartas desde un archivo
JSON y convertirlos en instancias de la clase Card.
'''
import json
from .card import Card
import os


def load_cards(filepath: str) -> dict:
    """
    Carga cartas desde un archivo JSON.

    Args:
        filepath: Ruta al archivo JSON con los datos de las cartas

    Returns:
        dict: Diccionario con las cartas cargadas, clave: número de carta
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    except FileNotFoundError:
        print(f"Error: El archivo de cartas no se encontró en la ruta: {filepath}")
        return {}

    except json.JSONDecodeError:
        print(f"Error: El archivo {filepath} tiene un formato JSON inválido.")
        return {}

    all_cards = {}
    for card_data in data:
        try:
            # Leer estrellas y nombre de imagen (si existe)
            stars = card_data.get('stars', 3)
            image = card_data.get('image')  # nombre de archivo (opcional)

            # Opcional: si no hay imagen en JSON, intentar encontrar un archivo por número
            # assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'images')
            # if not image:
            #     for ext in ('.png', '.jpg', '.webp', '.jpeg'):
            #         candidate = os.path.join(assets_dir, f"{card_data['number']}{ext}")
            #         if os.path.exists(candidate):
            #             image = f"{card_data['number']}{ext}"
            #             break

            card = Card(
                name=card_data['name'],
                number=card_data['number'],
                attack=card_data['attack'],
                defense=card_data['defense'],
                stars=stars,
                image=image
            )

            all_cards[card.number] = card

        except KeyError as e:
            print(f"Advertencia: Carta incompleta, falta campo: {e}")
            continue
        except Exception as e:
            print(f"Error inesperado al procesar carta: {e}")
            continue

    print(f"Las cartas han sido cargadas correctamente desde {filepath}.")
    return all_cards
