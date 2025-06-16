# Создание и сохранение прогноза на основе транзитов
from db import get_db
from datetime import datetime
from forecast_templates import interpret_aspect, get_template_for_aspect
from transits import calculate_transits_and_forecast

def generate_daily_forecast(user_id, date_str, category):
    from datetime import datetime
    from forecast_utils import calculate_transits_and_forecast, interpret_aspect
    from db import get_db

    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    calculate_transits_and_forecast(user_id, date_str)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Получаем ID категории
    cursor.execute("SELECT id FROM forecast_category WHERE name = %s", (category,))
    category_row = cursor.fetchone()
    if not category_row:
        cursor.close()
        conn.close()
        return f"Категория '{category}' не найдена."

    category_id = category_row['id']

    # Получаем прогнозы на указанную дату и категорию для пользователя
    cursor.execute("""
        SELECT interpretation
        FROM forecast
        WHERE user_id = %s
          AND category_id = %s
          AND %s BETWEEN date_from AND date_to
    """, (user_id, category_id, date))
    rows = cursor.fetchall()

    if rows:
        texts = [row['interpretation'] for row in rows if row['interpretation']]
        if texts:
            cursor.close()
            conn.close()
            return f"Прогноз на {date_str} по категории '{category}':\n" + "\n".join(texts)

    # Если интерпретаций нет — получаем аспекты и строим интерпретации вручную
    cursor.execute("""
        SELECT ta.celestial_body1_id, ta.celestial_body2_id, ta.aspect_id
        FROM forecast f
        JOIN transit_aspect ta ON ta.forecast_id = f.id
        WHERE f.user_id = %s
          AND f.category_id = %s
          AND %s BETWEEN f.date_from AND f.date_to
    """, (user_id, category_id, date))
    aspect_links = cursor.fetchall()

    if not aspect_links:
        cursor.close()
        conn.close()
        return f"Прогноз на {date_str} по категории '{category}': Никаких важных влияний."

    # Получаем названия светил и аспектов
    messages = []
    for aspect in aspect_links:
        cursor.execute("""
            SELECT cb1.name AS natal, cb2.name AS transit, a.name AS aspect
            FROM celestial_bodies cb1, celestial_bodies cb2, aspects a
            WHERE cb1.id = %s AND cb2.id = %s AND a.id = %s
        """, (aspect['celestial_body1_id'], aspect['celestial_body2_id'], aspect['aspect_id']))
        asp_data = cursor.fetchone()

        if asp_data:
            msg = interpret_aspect(asp_data['natal'], asp_data['transit'], asp_data['aspect'], category)
            if msg:
                messages.append(msg)

    cursor.close()
    conn.close()

    if not messages:
        return f"Прогноз на {date_str} по категории '{category}': Никаких важных влияний."
    return f"Прогноз на {date_str} по категории '{category}':\n" + "\n".join(messages)

def interpret_transits(transits, category_id):
    # Используем краткие обобщённые шаблоны
    aspects = transits['aspects']
    summaries = []

    for aspect in aspects:
        text = get_template_for_aspect(aspect, category_id)
        if text:
            summaries.append(text)

    return "\n".join(summaries) or "Нейтральный день без значимых влияний."

def create_weekly_forecast(user_id, category_id, date_start):
    from forecast_templates import get_weekly_template

    conn = get_db()
    cursor = conn.cursor()
    date_from = date_start
    date_to = date_start + timedelta(days=6)

    interpretation = get_weekly_template(category_id)  # Пример

    cursor.execute("""
        INSERT INTO forecast (
            user_id, category_id, period_id,
            transit_sign_id, transit_aspect_id, transit_house_id,
            date_from, date_to, interpretation
        )
        VALUES (%s, %s, 2, NULL, NULL, NULL, %s, %s, %s)
    """, (user_id, category_id, date_from, date_to, interpretation))

    conn.commit()
    cursor.close()
    conn.close()

    #return interpretation

# НА МЕСЯЦ
from flatlib.datetime import Date, Time, Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from datetime import date, timedelta

def generate_month_forecast(user_id, year, month):
    real_month = month + 1

    def get_sun_sign_for_month(year, month):
        day = 15
        date_str = f"{day:02d}/{month:02d}/{year % 100:02d}"  # DD/MM/YY
        date_obj = Date(date_str)
        time_obj = Time("12:00")
        dt = Datetime(date_obj, time_obj, "+03:00")  # МСК
        lat = "55:45:00"
        lon = "37:37:12"
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)
        sun = chart.get(const.SUN)

        signs_map = {
            'Aries': 'Овен',
            'Taurus': 'Телец',
            'Gemini': 'Близнецы',
            'Cancer': 'Рак',
            'Leo': 'Лев',
            'Virgo': 'Дева',
            'Libra': 'Весы',
            'Scorpio': 'Скорпион',
            'Sagittarius': 'Стрелец',
            'Capricorn': 'Козерог',
            'Aquarius': 'Водолей',
            'Pisces': 'Рыбы',
        }
        return signs_map.get(sun.sign, 'Неизвестно')

    start_date = date(year, real_month, 1)
    # Следующий месяц (корректно для декабря)
    if real_month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, real_month + 1, 1)

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT th.date, cb.name AS planet, h.number AS house
        FROM transit_house th
        JOIN celestial_bodies cb ON cb.id = th.celestial_body_id
        JOIN houses h ON h.id = th.house_id
        WHERE th.date >= %s AND th.date < %s
        ORDER BY th.date
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()

    important_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
    events = []

    for row in rows:
        if row['planet'] in important_planets:
            events.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'event': f"{row['planet']} в доме {row['house']}"
            })

    seen = set()
    unique_events = []
    for event in events:
        key = (event['date'], event['event'])
        if key not in seen:
            seen.add(key)
            unique_events.append(event)

    sunSign = get_sun_sign_for_month(year, real_month)

    return {
        'sunSign': sunSign,
        'events': unique_events,
    }

def generate_year_forecast(natal_chart_data, user_id, year):
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    step_days = 7  # Проверяем аспекты раз в неделю

    natal_chart = natal_chart_data['chart']
    natal_positions = {body.id: body for body in natal_chart.objects if body.id in [const.JUPITER, const.SATURN]}

    forecast_events = []

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y/%m/%d')
        jdtime = Datetime(date_str, natal_chart_data['birth_time'].strftime('%H:%M'), natal_chart_data['timezone'])
        chart = Chart(jdtime, natal_chart_data['pos'])

        # Только медленные планеты
        for planet in [const.JUPITER, const.SATURN]:
            trans_planet = chart.get(planet)
            for natal_body_id, natal_body in natal_positions.items():
                aspects = get_transit_aspects(trans_planet, natal_body)
                for aspect in aspects:
                    # Создаём ключ интерпретации
                    key = f'{trans_planet.id}_{aspect.type}_{natal_body.id}'
                    template = YEARLY_TEMPLATES.get(key)
                    if template:
                        text = template.replace('{date}', current_date.strftime('%d.%m.%Y'))
                        forecast_events.append(text)
        current_date += timedelta(days=step_days)
    return '\n\n'.join(sorted(set(forecast_events)))

