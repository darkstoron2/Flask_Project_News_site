import requests


def find_a_town(town):  # Нахождение места, по адресу из новости
    try:
        # Поиск места
        geocoder_request = f"https://geocode-maps.yandex.ru/1.x?geocode=" \
                           f"{town}&apikey=40d1649f-0493-4b70-98ba-98533de7710b&format=json"
        response = requests.get(geocoder_request)
        json_response = response.json()['response']['GeoObjectCollection']['featureMember'][0]
        coords_city = json_response['GeoObject']['Point']['pos'].split()
        map_request = f"https://static-maps.yandex.ru/1.x/?l=sat&ll={coords_city[0]},{coords_city[1]}&z=16"
        response = requests.get(map_request)
        # Если адрес нашелся, то в map.png сохраняется карта местности
        if not response:
            return False
        with open(f"static/img/map.png", "wb") as file:
            file.write(response.content)
        return True
    except Exception:
        return False