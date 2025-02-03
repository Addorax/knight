import json
import sys
import requests

server_address = 'https://geocode-maps.yandex.ru/1.x?'
api_key = '40d1649f-0493-4b70-98ba-98533de7710b'
ll_spn = 'geocode="Москва Красная пл-дь, 1"'
map_request = f"{server_address}{ll_spn}&apikey={api_key}&format=json"
response = requests.get(map_request)

if not response:
    print("Ошибка выполнения запроса:")
    print(map_request)
    print("Http статус:", response.status_code, "(", response.reason, ")")
    sys.exit(1)
res = json.loads(response.content)
object = (res['response']['GeoObjectCollection']['featureMember'][0]['GeoObject'])
address = object['metaDataProperty']['GeocoderMetaData']['Address']
postal_code = address['postal_code']
f_address = address('formatted')
print(f'{postal_code}, {f_address}')
