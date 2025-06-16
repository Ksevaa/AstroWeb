# Расчёт транзитных данных
from datetime import datetime, time
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const, aspects as flatlib_aspects
from db import get_db
from astro_utils import local_birth_datetime, find_house_for_longitude, decimal_to_dms_str

aspect_texts = {
    'CONJUNCTION': "Конъюнкция усиливает влияние планет, создавая мощное сочетание энергий.",
    'OPPOSITION': "Оппозиция часто указывает на внутренние конфликты и необходимость баланса.",
    'SEXTILE': "Секстиль приносит возможности и благоприятные обстоятельства.",
    'SQUARE': "Квадрат создаёт напряжение и испытания, требующие усилий.",
    'TRINE': "Трин дарит гармонию и лёгкое течение событий."
}

house_texts = {
    1: "Влияние на личные качества и самовыражение.",
    2: "Вопросы финансов и материальных ресурсов.",
    3: "Коммуникации, обучение, ближайшее окружение.",
    4: "Дом, семья, корни и внутренний мир.",
    5: "Творчество, дети, развлечения.",
    6: "Работа, здоровье, повседневные обязанности.",
    7: "Партнёрство и взаимоотношения.",
    8: "Совместные ресурсы, трансформации.",
    9: "Путешествия, философия, высшее образование.",
    10: "Карьера, статус, жизненные цели.",
    11: "Друзья, сообщества, мечты.",
    12: "Подсознание, тайны, уединение."
}

sign_texts = {
    'Aries': "Огонь и энергия Овна активируют инициативу и решимость.",
    'Taurus': "Стабильность и практичность Тельца помогает укрепить позиции.",
    'Gemini': "Любознательность Близнецов стимулирует коммуникацию.",
    'Cancer': "Чувствительность Рака усиливает эмоциональную сферу.",
    'Leo': "Творческий порыв Льва вдохновляет на новые свершения.",
    'Virgo': "Внимание к деталям Девы помогает в анализе и планировании.",
    'Libra': "Гармония Весов способствует установлению равновесия.",
    'Scorpio': "Глубина Скорпиона выводит на трансформации.",
    'Sagittarius': "Оптимизм Стрельца ведёт к расширению горизонтов.",
    'Capricorn': "Строгость Козерога укрепляет дисциплину и порядок.",
    'Aquarius': "Новаторство Водолея открывает нестандартные пути.",
    'Pisces': "Интуиция Рыб помогает воспринимать тонкие влияния."
}

def generate_interpretation(sign=None, house=None, aspect=None):
    texts = []
    if sign:
        texts.append(sign_texts.get(sign, ""))
    if house:
        texts.append(house_texts.get(house, ""))
    if aspect:
        texts.append(aspect_texts.get(aspect, ""))
    return " ".join(texts).strip()

def calculate_transits_and_forecast(user_id, date_str, category_name='general', period_name='day', action='insert', date_to_str=None):
    """
    action: 'insert' - вычислить и вставить прогнозы (по умолчанию)
            'select' - выбрать готовые прогнозы из БД
    date_str - дата начала периода (строка 'YYYY-MM-DD')
    date_to_str - дата окончания периода для выборки (опционально)
    """
    date_from = datetime.strptime(date_str, '%Y-%m-%d').date()
    date_to = None
    if date_to_str:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()

    conn = get_db()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Получаем пользователя
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        cursor.close()
        conn.close()
        return None

    # Получаем категорию прогноза
    cursor.execute("SELECT id FROM forecast_category WHERE name = %s", (category_name,))
    category = cursor.fetchone()
    if not category:
        print(f"Категория '{category_name}' не найдена.")
        cursor.close()
        conn.close()
        return None

    # Получаем период прогноза
    cursor.execute("SELECT id FROM forecast_period WHERE name = %s", (period_name,))
    period = cursor.fetchone()
    if not period:
        print(f"Период прогноза '{period_name}' не найден.")
        cursor.close()
        conn.close()
        return None
    period_id = period['id']

    if action == 'select':
        # Формируем запрос выборки прогнозов с фильтрацией по дате и параметрам
        query = """
            SELECT date_from, date_to, interpretation, transit_sign_id, transit_house_id, transit_aspect_id
            FROM forecast
            WHERE user_id = %s AND category_id = %s AND period_id = %s
        """
        params = [user_id, category['id'], period_id]

        if date_to:
            query += " AND date_from BETWEEN %s AND %s"
            params.extend([date_from, date_to])
        else:
            query += " AND date_from = %s"
            params.append(date_from)

        cursor.execute(query, params)
        forecasts = cursor.fetchall()
        cursor.close()
        conn.close()
        return forecasts

    dt_utc = local_birth_datetime(date_from, time(12, 0), user['timezone'])
    lat_str = decimal_to_dms_str(float(user["birth_latitude"]))
    lon_str = decimal_to_dms_str(float(user["birth_longitude"]))
    pos = GeoPos(lat_str, lon_str)

    chart = Chart(Datetime(dt_utc.strftime('%Y/%m/%d'), dt_utc.strftime('%H:%M'), '+00:00'), pos)

    bodies = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]
    houses_list = [chart.houses.get(f'House{i}') for i in range(1, 13)]

    transit_sign_ids = []
    transit_house_ids = []
    transit_aspect_ids = []

    for body in bodies:
        obj = chart.get(body)
        sign = obj.sign
        degree = obj.lon
        house_number = find_house_for_longitude(houses_list, obj.lon)

        cursor.execute("SELECT id FROM celestial_bodies WHERE name = %s", (body,))
        celestial_body = cursor.fetchone()
        cursor.execute("SELECT id FROM zodiac_signs WHERE name = %s", (sign,))
        zodiac_sign = cursor.fetchone()

        cursor.execute("""
            DELETE FROM forecast
            WHERE user_id = %s AND category_id = %s AND period_id = %s AND date_from = %s
        """, (user_id, category['id'], period_id, date_from))

        if celestial_body and zodiac_sign:
            cursor.execute("""
                INSERT INTO transit_celestial_in_sign (celestial_body_id, zodiac_sign_id, degree, date)
                VALUES (%s, %s, %s, %s)
            """, (celestial_body['id'], zodiac_sign['id'], degree, date_from))
            transit_sign_ids.append(cursor.lastrowid)

        if house_number:
            cursor.execute("SELECT id FROM houses WHERE number = %s", (house_number,))
            house = cursor.fetchone()
            if celestial_body and house:
                cursor.execute("""
                    INSERT INTO transit_house (celestial_body_id, house_id, date)
                    VALUES (%s, %s, %s)
                """, (celestial_body['id'], house['id'], date_from))
                transit_house_ids.append(cursor.lastrowid)

    objects = [chart.get(body) for body in bodies]

    ASPECTS_LIST = [const.CONJUNCTION, const.OPPOSITION, const.SEXTILE, const.SQUARE, const.TRINE]

    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            asp = flatlib_aspects.getAspect(objects[i], objects[j], ASPECTS_LIST)
            if asp:
                cursor.execute("SELECT id FROM aspects WHERE name = %s", (asp.type,))
                aspect_row = cursor.fetchone()
                if aspect_row is None:
                    continue
                aspect_id = aspect_row['id']

                cursor.execute("SELECT id FROM celestial_bodies WHERE name = %s", (objects[i].id,))
                body1 = cursor.fetchone()
                cursor.execute("SELECT id FROM celestial_bodies WHERE name = %s", (objects[j].id,))
                body2 = cursor.fetchone()
                if not body1 or not body2:
                    continue

                cursor.execute("""
                    INSERT INTO transit_aspect (celestial_body1_id, celestial_body2_id, aspect_id, date)
                    VALUES (%s, %s, %s, %s)
                """, (body1['id'], body2['id'], aspect_id, date_from))
                transit_aspect_ids.append(cursor.lastrowid)

    # Прогнозы для положений в знаках
    for ts_id in transit_sign_ids:
        cursor.execute("SELECT celestial_body_id, zodiac_sign_id FROM transit_celestial_in_sign WHERE id = %s", (ts_id,))
        row = cursor.fetchone()
        if not row:
            continue

        cursor.execute("SELECT name FROM celestial_bodies WHERE id = %s", (row['celestial_body_id'],))
        body_name = cursor.fetchone()['name']
        cursor.execute("SELECT name FROM zodiac_signs WHERE id = %s", (row['zodiac_sign_id'],))
        sign_name = cursor.fetchone()['name']

        interp = generate_interpretation(sign=sign_name)

        cursor.execute("""
            INSERT INTO forecast (user_id, category_id, period_id, transit_sign_id, date_from, date_to, interpretation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, category['id'], period_id, ts_id, date_from, date_from, interp))

    # Прогнозы по домам
    for th_id in transit_house_ids:
        cursor.execute("SELECT celestial_body_id, house_id FROM transit_house WHERE id = %s", (th_id,))
        row = cursor.fetchone()
        if not row:
            continue

        cursor.execute("SELECT number FROM houses WHERE id = %s", (row['house_id'],))
        house_number = cursor.fetchone()['number']

        interp = generate_interpretation(house=house_number)

        cursor.execute("""
            INSERT INTO forecast (user_id, category_id, period_id, transit_house_id, date_from, date_to, interpretation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, category['id'], period_id, th_id, date_from, date_from, interp))

    # Прогнозы по аспектам
    for ta_id in transit_aspect_ids:
        cursor.execute("SELECT celestial_body1_id, celestial_body2_id, aspect_id FROM transit_aspect WHERE id = %s", (ta_id,))
        row = cursor.fetchone()
        if not row:
            continue

        cursor.execute("SELECT name FROM celestial_bodies WHERE id = %s", (row['celestial_body1_id'],))
        body1_name = cursor.fetchone()['name']
        cursor.execute("SELECT name FROM celestial_bodies WHERE id = %s", (row['celestial_body2_id'],))
        body2_name = cursor.fetchone()['name']
        cursor.execute("SELECT name FROM aspects WHERE id = %s", (row['aspect_id'],))
        aspect_name = cursor.fetchone()['name']

        interp = generate_interpretation(aspect=aspect_name)

        cursor.execute("""
            INSERT INTO forecast (user_id, category_id, period_id, transit_aspect_id, date_from, date_to, interpretation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, category['id'], period_id, ta_id, date_from, date_from, interp))

    conn.commit()
    cursor.close()
    conn.close()
    return True
