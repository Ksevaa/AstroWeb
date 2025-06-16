from flask import (Flask, render_template, redirect, url_for, flash, session, jsonify, request)  # Основные импорты Flask
import requests  # HTTP-запросы
import mysql.connector  # MySQL подключение
from werkzeug.security import generate_password_hash, check_password_hash  # Хеширование паролей
from datetime import datetime, timedelta  # Работа с датой и временем
import logging
from natal_chart import calculate_natal_chart
from flask import request, jsonify, session
from forecast_utils import generate_daily_forecast, create_weekly_forecast, generate_month_forecast,generate_year_forecast
from astro_utils import get_timezone, local_birth_datetime
from astro_events import get_daily_astr_events



app = Flask(__name__)
app.secret_key = 'cheredinova'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Конфигурация подключения к БД
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'database': 'astro',
    'autocommit': False
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        logger.info("Успешное подключение к БД")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Ошибка подключения к БД: {err}")
        raise

@app.route('/')  
def index():
    user = None
    sun_sign = moon_sign = ascendant_sign = 'неизвестно'
    ZODIAC_TRANSLATIONS = {
        'ARIES': 'Овен',
        'TAURUS': 'Телец',
        'GEMINI': 'Близнецы',
        'CANCER': 'Рак',
        'LEO': 'Лев',
        'VIRGO': 'Дева',
        'LIBRA': 'Весы',
        'SCORPIO': 'Скорпион',
        'SAGITTARIUS': 'Стрелец',
        'CAPRICORN': 'Козерог',
        'AQUARIUS': 'Водолей',
        'PISCES': 'Рыбы'
    }
    if 'user_id' in session:
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute('SELECT name FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()

            if user:
                user_id = session['user_id']

                # Солнце
                cursor.execute("""
                    SELECT zs.name AS sun_sign
                    FROM celestial_body_in_sign cbis
                    JOIN zodiac_signs zs ON cbis.zodiac_sign_id = zs.id
                    JOIN celestial_bodies cb ON cbis.body_id = cb.id
                    WHERE cb.name = 'Sun' AND cbis.user_id = %s
                """, (user_id,))
                sun = cursor.fetchone()
                if sun:
                    sun_sign = ZODIAC_TRANSLATIONS.get(sun['sun_sign'], sun['sun_sign'])

                # Луна
                cursor.execute("""
                    SELECT zs.name AS moon_sign
                    FROM celestial_body_in_sign cbis
                    JOIN zodiac_signs zs ON cbis.zodiac_sign_id = zs.id
                    JOIN celestial_bodies cb ON cbis.body_id = cb.id
                    WHERE cb.name = 'Moon' AND cbis.user_id = %s
                """, (user_id,))
                moon = cursor.fetchone()
                if moon:
                    moon_sign = ZODIAC_TRANSLATIONS.get(moon['moon_sign'], moon['moon_sign'])

                # Асцендент
                cursor.execute("""
                    SELECT zs.name AS ascendant_sign
                    FROM doma_v_znake dvz
                    JOIN zodiac_signs zs ON dvz.zodiac_sign_id = zs.id
                    WHERE dvz.user_id = %s AND dvz.house_id = 1
                """, (user_id,))
                asc = cursor.fetchone()
                if asc:
                    ascendant_sign = ZODIAC_TRANSLATIONS.get(asc['ascendant_sign'], asc['ascendant_sign'])

        except Exception as e:
            logger.error(f"Ошибка получения данных пользователя: {str(e)}")
            flash('Ошибка загрузки данных', 'error')
        finally:
            if conn:
                cursor.close()
                conn.close()
    try:
        daily_events = get_daily_astr_events()
    except Exception as e:
        logger.error(f"Ошибка при вычислении астрологических событий: {str(e)}")


    return render_template('index.html', user=user, sun_sign=sun_sign, moon_sign=moon_sign, ascendant_sign=ascendant_sign)

YANDEX_API_KEY = '2021542f-8e14-40cb-9ac2-a555348e2ff1'  # Ключ API Яндекса
# Получаем координаты города (широту и долготу) через Яндекс Геокодер
@app.route('/api/coordinates')
def get_coordinates():
    city = request.args.get('city')
    region = request.args.get('region')
    if not city or not region:
        return jsonify({'error': 'City and region parameters are required'}), 400

    query = f'Россия, {region}, {city}'
    url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': YANDEX_API_KEY,
        'format': 'json',
        'geocode': query,
        'results': 1,
        'lang': 'ru_RU'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        geo_object = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
        pos = geo_object['Point']['pos']
        lon, lat = map(float, pos.split())
        return jsonify({'latitude': lat, 'longitude': lon})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        errors = {}

        # Получаем данные из формы
        email = form.get('email', '').strip()
        password = form.get('password', '')
        name = form.get('name', '').strip()
        gender = form.get('gender', '')
        birth_date = form.get('birthDate', '')
        birth_time = form.get('birthTime', '').strip()
        unknown_time = form.get('unknownTime') == 'on'
        region = form.get('region', '').strip()
        city = form.get('city', '').strip()
        birth_latitude = form.get('birth_latitude')
        birth_longitude = form.get('birth_longitude')

        try:
            birth_latitude = float(birth_latitude) if birth_latitude else None
            birth_longitude = float(birth_longitude) if birth_longitude else None
        except ValueError:
            errors['general'] = 'Некорректные координаты места рождения'

        # Валидация данных
        if not email or '@' not in email:
            errors['email'] = 'Введите корректный email'
        if len(password) < 8:
            errors['password'] = 'Пароль должен быть минимум 8 символов'
        if not name or not all(ch.isalpha() or ch in "Ёё" for ch in name):
            errors['name'] = 'Введите корректное имя'
        if gender not in ['male', 'female']:
            errors['gender'] = 'Выберите пол'
        if not birth_date:
            errors['birthDate'] = 'Укажите дату рождения'
        else:
            try:
                datetime.strptime(birth_date, '%Y-%m-%d')
            except ValueError:
                errors['birthDate'] = 'Неверный формат даты'
        if not region:
            errors['region'] = 'Выберите область'
        if not city:
            errors['city'] = 'Выберите город'

        # Проверка уникальности email
        if not errors:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
                if cursor.fetchone():
                    errors['email'] = 'Этот email уже зарегистрирован'
                cursor.close()
            except Exception as e:
                logger.error(f"Ошибка при проверке email: {str(e)}")
                errors['general'] = 'Ошибка сервера. Попробуйте позже.'
            finally:
                if conn:
                    conn.close()

        if not errors:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                birth_place = f"{region}, {city}" if region and city else ""

                timezone = None
                try:
                    if birth_latitude is not None and birth_longitude is not None:
                        timezone = get_timezone(birth_latitude, birth_longitude)
                except Exception as tz_error:
                    logger.warning(f"Не удалось определить часовой пояс: {tz_error}")
                    timezone = None

                user_data = (
                    email,
                    generate_password_hash(password),
                    name,
                    gender,
                    birth_date,
                    None if unknown_time else birth_time if birth_time else None,
                    birth_place,
                    birth_latitude,
                    birth_longitude,
                    timezone
                )

                cursor.execute("""
                    INSERT INTO users
                    (email, password_hash, name, gender, birth_date, birth_time, birth_place, birth_latitude, birth_longitude, timezone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, user_data)

                conn.commit()
                user_id = cursor.lastrowid
                # Вызов расчета натальной карты
                calculate_natal_chart(user_id)
                logger.info(f"Успешная регистрация пользователя {email}")
                flash('Регистрация прошла успешно! Войдите в систему.', 'success')
                return redirect(url_for('login'))

            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Ошибка при регистрации: {str(e)}")
                errors['general'] = 'Ошибка при регистрации. Попробуйте позже.'

            finally:
                if conn:
                    cursor.close()
                    conn.close()

        return render_template('register.html', form=form, errors=errors, yandex_api_key=YANDEX_API_KEY)

    return render_template('register.html', form={}, errors={}, yandex_api_key=YANDEX_API_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = None
        try:
            conn = get_db_connection()  # Подключаемся к БД
            cursor = conn.cursor(dictionary=True)

            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))  # Ищем пользователя по email
            user = cursor.fetchone()

            if not user:
                flash('Пользователь с таким email не найден', 'error')  # Если нет пользователя — ошибка
                return redirect(url_for('login'))

            if not check_password_hash(user['password_hash'], password):
                flash('Неверный пароль', 'error')  # Если пароль неверный — ошибка
                return redirect(url_for('login'))

            # Успешная авторизация — записываем данные в сессию
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f'Добро пожаловать, {user["name"]}!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            logger.error(f"Ошибка авторизации: {str(e)}", exc_info=True)  # Логируем с подробностями
            flash('Ошибка сервера при авторизации', 'error')  # Сообщаем пользователю об ошибке
            return redirect(url_for('login'))

        finally:
            if conn:
                cursor.close()
                conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()  
    flash('Вы вышли из системы.', 'success')  
    return redirect(url_for('login'))  

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = session.get('user_id')  # Получаем ID пользователя из сессии
    if not user_id:
        return redirect(url_for('login'))  # Если не авторизован — перенаправляем на вход

    conn = get_db_connection()  # Подключаемся к базе данных
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        birth_date = request.form.get('birth_date')
        birth_time_str = request.form.get('birth_time')
        region = request.form.get('region')
        city = request.form.get('city')

        birth_place = f"{region}, {city}" if region and city else None
        birth_lat = request.form.get('birth_latitude') or None
        birth_lon = request.form.get('birth_longitude') or None

        timezone = None
        if birth_lat and birth_lon:
           try:
               timezone = get_timezone(float(birth_lat), float(birth_lon))
           except Exception as e:
               logger.warning(f"Ошибка определения часового пояса: {e}")

        if birth_time_str:
            hours, minutes = map(int, birth_time_str.split(":"))
            birth_time = timedelta(hours=hours, minutes=minutes)
        else:
            birth_time = None

        cursor.execute("""
            UPDATE users
            SET name = %s,
                gender = %s,
                birth_date = %s,
                birth_time = %s,
                birth_place = %s,
                birth_latitude = %s,
                birth_longitude = %s,
                timezone = %s
            WHERE id = %s
        """, (
            name, gender, birth_date, birth_time,
            birth_place, birth_lat, birth_lon, timezone, user_id
        ))
        conn.commit()
        user_id = cursor.lastrowid
        # Вызов расчета натальной карты
        calculate_natal_chart(user_id)
        flash('Данные успешно обновлены', 'success')
        return redirect(url_for('settings'))

    cursor.execute("""
        SELECT name, gender, birth_date, birth_time, birth_place, birth_latitude, birth_longitude, timezone
        FROM users WHERE id = %s
    """, (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        flash("Пользователь не найден", "error")
        return redirect(url_for('login'))
    user = dict(user)

    if user['birth_time'] and isinstance(user['birth_time'], timedelta):
        total_seconds = int(user['birth_time'].total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        user['birth_time'] = f"{hours:02d}:{minutes:02d}"

    region = ""
    city = ""
    if user.get('birth_place'):
        parts = user['birth_place'].split(', ')
        if len(parts) == 2:
            region, city = parts

    return render_template(
        'settings.html',
        user=user,
        region=region,
        city=city
    )

@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    if request.method == 'GET':
        return render_template('forecast.html')

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    forecast_date = data.get('date')
    category = data.get('category')

    if not forecast_date or not category:
        return jsonify({'error': 'Missing data'}), 400

    try:
        forecast_text = generate_daily_forecast(user_id, forecast_date, category)
    except Exception as e:
        print(f'Ошибка прогноза: {e}')
        return jsonify({'error': 'Ошибка генерации прогноза'}), 500


@app.route('/api/week-transits')
def api_week_transits():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if not start_str or not end_str:
        return jsonify({'error': 'Start and end date parameters are required'}), 400

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        if start_date > end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    query = """
        SELECT 
            tcs.date AS transit_date,
            cb.name AS celestial_body_name,
            zs.name AS sign_name,
            h.number AS house_number,
            a.name AS aspect_name
        FROM forecast f
        LEFT JOIN transit_celestial_in_sign tcs ON f.transit_sign_id = tcs.id
        LEFT JOIN celestial_bodies cb ON tcs.celestial_body_id = cb.id
        LEFT JOIN zodiac_signs zs ON tcs.zodiac_sign_id = zs.id
        LEFT JOIN transit_house th ON f.transit_house_id = th.id
        LEFT JOIN houses h ON th.house_id = h.id
        LEFT JOIN transit_aspect ta ON f.transit_aspect_id = ta.id
        LEFT JOIN aspects a ON ta.aspect_id = a.id
        WHERE 
            f.user_id = %s 
            AND f.date_from <= %s 
            AND f.date_to >= %s
        ORDER BY tcs.date
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (user_id, end_date, start_date))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    transits_by_date = {}
    for row in rows:
        transit_date = row.get('transit_date')
        if transit_date is None:
            continue

        day = transit_date.strftime('%Y-%m-%d')
        transits_by_date.setdefault(day, []).append({
            'celestial_body': row['celestial_body_name'],
            'sign': row['sign_name'],
            'house': row['house_number'],
            'aspect': row['aspect_name']
        })

    return jsonify({
        'week_start': start_date.strftime('%d %B %Y'),
        'week_end': end_date.strftime('%d %B %Y'),
        'transits_by_date': transits_by_date
    })

@app.route('/week-forecast', methods=['GET', 'POST'])
def week_forecast():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        selected_date_str = request.args.get('date')
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else datetime.today().date()
        except ValueError:
            selected_date = datetime.today().date()

        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        return render_template(
            'week-forecast.html',
            date_from=start_of_week,
            date_to=end_of_week,
            selected_date=selected_date.strftime('%Y-%m-%d')
        )

    # POST
    selected_date_str = request.form.get('selected_date')
    category_id = request.form.get('category_id')

    if not selected_date_str or not category_id:
        return jsonify({'error': 'Missing data'}), 400

    try:
        category_id = int(category_id)
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        start_of_week = selected_date - timedelta(days=selected_date.weekday())

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM transit_celestial_in_sign
            WHERE user_id = %s AND date = %s
            LIMIT 1
        """, (user_id, start_of_week))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        transit_sign_id = row['id'] if row else None

        create_weekly_forecast(user_id, category_id, transit_sign_id, start_of_week)

        return jsonify({'message': 'Прогноз сохранён успешно'})

    except Exception as e:
        print(f'Ошибка при генерации недельного прогноза: {e}')
        return jsonify({'error': 'Ошибка генерации прогноза'}), 500

@app.route('/api/month-forecast', methods=['GET'])
def get_month_forecast():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    year = int(request.args.get('year'))
    month = int(request.args.get('month'))

    from forecast_utils import generate_month_forecast
    forecast_data = generate_month_forecast(user_id, year, month)

    return jsonify(forecast_data)

from datetime import datetime

@app.route('/month-forecast')
def month_forecast():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    current_date = datetime.now()
    month = current_date.month
    year = current_date.year
    natal_data = get_natal_chart_data(user_id)
    forecast_text = generate_month_forecast(natal_data, user_id, month, year)

    return render_template('month-forecast.html', forecast=forecast_text, month=month, year=year)

@app.route('/year-forecast')
def year_forecast():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    year = datetime.now().year

    natal_data = get_natal_chart_data(user_id)

    forecast_text = generate_year_forecast(natal_data, user_id, year)

    return render_template('year-forecast.html', forecast=forecast_text, year=year)

@app.route('/astrologer')
def astrologer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    astrologer_id = 6

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Получаем ID чата или создаём новый
    cursor.execute("""
        SELECT id FROM chat_with_astrologer
        WHERE user_id = %s AND astrologer_id = %s
    """, (user_id, astrologer_id))
    chat = cursor.fetchone()

    if not chat:
        cursor.execute("""
            INSERT INTO chat_with_astrologer (user_id, astrologer_id, start_date)
            VALUES (%s, %s, NOW())
        """, (user_id, astrologer_id))
        conn.commit()
        chat_id = cursor.lastrowid
    else:
        chat_id = chat['id']

    # Загружаем сообщения этого чата
    cursor.execute("""
        SELECT sender, text, sent_at
        FROM messages
        WHERE chat_id = %s
        ORDER BY sent_at ASC
    """, (chat_id,))
    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('astrologer.html', messages=messages, chat_id=chat_id)


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    user_id = session['user_id']
    data = request.get_json()

    chat_id = data.get('chat_id')
    text = data.get('text', '').strip()

    if not chat_id or not text:
        return jsonify({'error': 'Missing chat_id or text'}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id FROM chat_with_astrologer
        WHERE id = %s AND user_id = %s
    """, (chat_id, user_id))
    chat = cursor.fetchone()
    if not chat:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Chat not found or access denied'}), 403

    cursor.execute("""
        INSERT INTO messages (chat_id, sender, text, sent_at)
        VALUES (%s, %s, %s, %s)
    """, (chat_id, 'user', text, datetime.utcnow()))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'ok'})

@app.route('/handbook')
def handbook():
    return render_template('handbook.html')

if __name__ == '__main__':
    app.run(debug=True)
