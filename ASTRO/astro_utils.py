from datetime import datetime, time
import pytz
from timezonefinder import TimezoneFinder
import mysql.connector
from flatlib import const
from db import get_db
tf = TimezoneFinder()

def get_timezone(lat, lon):
    return tf.timezone_at(lat=lat, lng=lon)

def local_birth_datetime(birth_date, birth_time, timezone_str):
    if birth_time is None:
        birth_time = time(12, 0)
    local_tz = pytz.timezone(timezone_str)
    local_dt = datetime.combine(birth_date, birth_time)
    local_dt = local_tz.localize(local_dt)
    return local_dt.astimezone(pytz.utc)

def decimal_to_dms_str(dec):
    degrees = int(dec)
    minutes_float = abs(dec - degrees) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60)
    return f"{abs(degrees)}:{minutes:02d}:{seconds:02d}"

def find_house_for_longitude(houses, lon):
    lon = lon % 360
    cusps = sorted([(int(h.id[5:]), h.lon % 360) for h in houses])

    for i in range(len(cusps)):
        house_num, cusp_lon = cusps[i]
        next_house_num, next_cusp_lon = cusps[(i + 1) % len(cusps)]

        if cusp_lon < next_cusp_lon:
            if cusp_lon <= lon < next_cusp_lon:
                return house_num
        else:
            if lon >= cusp_lon or lon < next_cusp_lon:
                return house_num
    return None

ORBS = {
    const.MOON: 6.0,
    'default': 5.0,
}

def get_natal_data_from_db(user_id: int):
    """
    Загружает из БД все натальные показатели пользователя.
    Возвращает словарь с данными:
    {
        'aspects': [(body1, body2, aspect_type, orb), ...],
        'bodies_in_houses': [(body, house), ...],
        'bodies_in_signs': [(body, sign), ...],
        'houses_in_signs': [(house, sign), ...]
    }
    """
    cnx = mysql.connector.connect(**get_db)
    cursor = cnx.cursor(dictionary=True)

    natal_data = {}

    cursor.execute(
        "SELECT body1, body2, aspect_type, orb FROM aspects_between_bodies WHERE user_id = %s", (user_id,)
    )
    natal_data['aspects'] = cursor.fetchall()

    cursor.execute(
        "SELECT body, house FROM celestial_body_in_house WHERE user_id = %s", (user_id,)
    )
    natal_data['bodies_in_houses'] = cursor.fetchall()

    cursor.execute(
        "SELECT body, sign FROM celestial_body_in_sign WHERE user_id = %s", (user_id,)
    )
    natal_data['bodies_in_signs'] = cursor.fetchall()

    cursor.execute(
        "SELECT house, sign FROM doma_v_znake WHERE user_id = %s", (user_id,)
    )
    natal_data['houses_in_signs'] = cursor.fetchall()

    cursor.close()
    cnx.close()

    return natal_data