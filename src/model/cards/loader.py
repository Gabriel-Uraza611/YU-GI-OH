'''
Módulo para cargar y manejar cartas desde archivos JSON.

Este módulo proporciona funciones para cargar datos de cartas desde archivos
JSON y convertirlos en instancias de la clase Card, facilitando la gestión
de mazos y colecciones de cartas en juegos de cartas coleccionables.
'''
import json
from    .card import Card


def load_cards(filepath: str)-> dict:

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
            # Crear la carta con todos los parámetros necesarios
            card = Card(
                name=card_data['name'],
                number=card_data['number'],
                category=card_data['category'],
                attack=card_data['attack'],
                defense=card_data['defense'],
                level=card_data.get('level')
            )

            # Usar el número de carta como clave (o crear un ID si es necesario)
            all_cards[card.number] = card

        except KeyError as e:
            print(f"Advertencia: Carta incompleta, falta campo: {e}")
            continue
        except Exception as e:
            print(f"Error inesperado al procesar carta: {e}")
            continue

    print(f"Las cartas han sido cargadas correctamente desde {filepath}.")
    return all_cards
