# Расчёт натальной карты
from datetime import datetime, time, timedelta
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from db import get_db
from astro_utils import local_birth_datetime, decimal_to_dms_str, find_house_for_longitude

def calculate_natal_chart(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        print(f"Пользователь с ID {user_id} не найден.")
        return

    if isinstance(user["birth_time"], timedelta):
        seconds = user["birth_time"].total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        user["birth_time"] = time(hour=hours, minute=minutes)
    elif user["birth_time"] is None:
        user["birth_time"] = time(12, 0)

    dt_utc = local_birth_datetime(user["birth_date"], user["birth_time"], user["timezone"])
    lat_str = decimal_to_dms_str(float(user["birth_latitude"]))
    lon_str = decimal_to_dms_str(float(user["birth_longitude"]))
    pos = GeoPos(lat_str, lon_str)

    chart = Chart(Datetime(dt_utc.strftime('%Y/%m/%d'), dt_utc.strftime('%H:%M'), '+00:00'), pos)
    houses_list = [chart.houses.get(f'House{i}') for i in range(1, 13)]

    bodies = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]

    # Сохраняем положение светил в знаках и домах
    for body in bodies:
        obj = chart.get(body)
        sign = obj.sign
        degree = obj.lon
        house_number = find_house_for_longitude(houses_list, obj.lon)

        cursor.execute("SELECT id FROM celestial_bodies WHERE name = %s", (body,))
        body_id = cursor.fetchone()
        if not body_id:
            continue

        cursor.execute("SELECT id FROM zodiac_signs WHERE name = %s", (sign,))
        sign_id = cursor.fetchone()
        if not sign_id:
            continue

        house_id = None
        if house_number:
            cursor.execute("SELECT id FROM houses WHERE number = %s", (house_number,))
            result = cursor.fetchone()
            if result:
                house_id = result['id']

        cursor.execute("SELECT id FROM celestial_body_in_sign WHERE user_id = %s AND body_id = %s", (user_id, body_id['id']))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO celestial_body_in_sign (user_id, body_id, zodiac_sign_id, degree) VALUES (%s, %s, %s, %s)",
                           (user_id, body_id['id'], sign_id['id'], degree))

        if house_id:
            cursor.execute("SELECT id FROM celestial_body_in_house WHERE user_id = %s AND body_id = %s", (user_id, body_id['id']))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO celestial_body_in_house (user_id, body_id, house_id) VALUES (%s, %s, %s)",
                               (user_id, body_id['id'], house_id))

    # Сохраняем дома в знаках
    for house in houses_list:
        sign = house.sign
        degree = house.lon

        cursor.execute("SELECT id FROM houses WHERE number = %s", (int(house.id[5:]),))
        house_id = cursor.fetchone()
        cursor.execute("SELECT id FROM zodiac_signs WHERE name = %s", (sign,))
        sign_id = cursor.fetchone()
        if house_id and sign_id:
            cursor.execute("SELECT id FROM doma_v_znake WHERE user_id = %s AND house_id = %s", (user_id, house_id['id']))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO doma_v_znake (user_id, house_id, zodiac_sign_id, degree) VALUES (%s, %s, %s, %s)",
                               (user_id, house_id['id'], sign_id['id'], degree))

    # Расчёт аспектов между натальными светилами
    aspect_angles = {
        'Conjunction': 0,
        'Sextile': 60,
        'Square': 90,
        'Trine': 120,
        'Opposition': 180
    }
    orb_limit = 6

    body_objs = {body: chart.get(body) for body in bodies}
    for i, body1 in enumerate(bodies):
        for body2 in bodies[i+1:]:
            obj1 = body_objs[body1]
            obj2 = body_objs[body2]
            diff = abs(obj1.lon - obj2.lon) % 360
            diff = min(diff, 360 - diff)

            for name, angle in aspect_angles.items():
                orb = abs(diff - angle)
                if orb <= orb_limit:
                    cursor.execute("SELECT id FROM celestial_bodies WHERE name = %s", (body1,))
                    b1 = cursor.fetchone()
                    cursor.execute("SELECT id FROM celestial_bodies WHERE name = %s", (body2,))
                    b2 = cursor.fetchone()
                    cursor.execute("SELECT id FROM aspects WHERE name = %s", (name,))
                    asp = cursor.fetchone()
                    if not (b1 and b2 and asp):
                        continue

                    cursor.execute("""
                        SELECT id FROM aspects_between_bodies
                        WHERE user_id = %s AND body1_id = %s AND body2_id = %s AND aspect_id = %s
                    """, (user_id, b1['id'], b2['id'], asp['id']))
                    if cursor.fetchone():
                        continue

                    cursor.execute("""
                        INSERT INTO aspects_between_bodies (user_id, body1_id, body2_id, aspect_id, orb)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, b1['id'], b2['id'], asp['id'], orb))

    conn.commit()
    cursor.close()
    conn.close()
    print("Полный расчёт натальной карты завершён.")
