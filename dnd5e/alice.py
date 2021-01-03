import json
import re
from random import randint
from functools import reduce

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


DEFAULT_ANSWER = 'Я ничего не понимаю'
REGULAR_TROW_RE = re.compile(r'^(кинь|брось) (?P<count>[1-9]) д (?P<sides>4|6|8|12|20) ?($|(?P<sign>плюс|минус) (?P<mod>[\d]+))$')
ATTACT_TROW_RE = re.compile(r'^(кинь|брось) на (попадание|атаку) (|модификатор|с модификатором) ?(?P<sign>плюс|минус) (?P<mod>[\d]+)$')


def roll_dice(count, sides, mod=0):
    return reduce(lambda value, _: value + randint(1, sides), range(count), mod)


def dice_from_match(match_data):
    count = int(match_data['count'])
    sides = int(match_data['sides'])

    if match_data['mod'] is None:
        mod = 0
    else:
        mod = int(match_data['mod']) if match_data['sign'] == 'плюс' else -int(match_data['mod'])

    return {'count': count, 'sides': sides, 'mod': mod}


def trow_regular_dice(data):
    return f'Результат броска: {roll_dice(**dice_from_match(data))}'


def trow_attact_hit(data):
    result = roll_dice(1, 20)
    if result == 20:
        return 'Критическое попадание!. Поздравляю'
    if result == 1:
        return 'Критический промах!. Сожалею'

    if data['mod'] is None:
        mod = 0
    else:
        mod = int(data['mod']) if data['sign'] == 'плюс' else -int(data['mod'])
    return f'Результат броска на попадание {result + mod}'


@require_POST
@csrf_exempt
def alice_api(request):
    request = json.loads(request.body)
    response = {}

    response['version'] = request['version']
    response['session'] = request['session']
    response['response'] = {
        'end_session': False,
        'text': DEFAULT_ANSWER
    }

    match = ATTACT_TROW_RE.match(request['request']['command'])
    if match:
        response['response']['text'] = trow_attact_hit(match.groupdict())
        return JsonResponse(response)

    match = REGULAR_TROW_RE.match(request['request']['command'])
    if match:
        response['response']['text'] = trow_regular_dice(match.groupdict())
        return JsonResponse(response)

    return JsonResponse(response)