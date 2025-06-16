from flatlib import const
from typing import List, Dict
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from datetime import date

# Перечень аспектов и планет
ASPECTS = [const.CONJUNCTION, const.SEXTILE, const.SQUARE, const.TRINE, const.OPPOSITION]
PLANETS = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]

# Интерпретации
ASPECT_MEANINGS = {
    # Солнце
    (const.SUN, const.MOON, const.CONJUNCTION): 'Гармония между разумом и чувствами.',
    (const.SUN, const.MERCURY, const.CONJUNCTION): 'Повышенное внимание и ясность мысли.',
    (const.SUN, const.VENUS, const.TRINE): 'Любовь к жизни, обаяние и привлекательность.',
    (const.SUN, const.MARS, const.SQUARE): 'Импульсивность и желание доминировать.',
    (const.SUN, const.JUPITER, const.OPPOSITION): 'Чрезмерный оптимизм, склонность к преувеличениям.',
    (const.SUN, const.SATURN, const.SEXTILE): 'Ответственность и зрелый подход к делу.',

    # Луна
    (const.MOON, const.MERCURY, const.SQUARE): 'Эмоциональные реакции мешают логике.',
    (const.MOON, const.VENUS, const.TRINE): 'Мягкость, романтичность, хорошее настроение.',
    (const.MOON, const.MARS, const.CONJUNCTION): 'Эмоциональная активность и раздражительность.',
    (const.MOON, const.JUPITER, const.SEXTILE): 'Подъём настроения и желание помогать другим.',
    (const.MOON, const.SATURN, const.OPPOSITION): 'Одиночество и эмоциональные ограничения.',

    # Меркурий
    (const.MERCURY, const.VENUS, const.SEXTILE): 'Изысканная речь и дипломатичность.',
    (const.MERCURY, const.MARS, const.SQUARE): 'Резкость в общении, конфликты на словах.',
    (const.MERCURY, const.JUPITER, const.CONJUNCTION): 'Широкий кругозор и стремление к обучению.',
    (const.MERCURY, const.SATURN, const.OPPOSITION): 'Возможны трудности в коммуникации.',

    # Венера
    (const.VENUS, const.MARS, const.SQUARE): 'Напряжённость в любви и страсти.',
    (const.VENUS, const.JUPITER, const.TRINE): 'Гармония в отношениях и щедрость.',
    (const.VENUS, const.SATURN, const.CONJUNCTION): 'Серьёзное отношение к чувствам и партнёрству.',

    # Марс
    (const.MARS, const.JUPITER, const.SEXTILE): 'Энергия для роста и достижений.',
    (const.MARS, const.SATURN, const.SQUARE): 'Сопротивление, требующее усилий и терпения.',

    # Юпитер и Сатурн
    (const.JUPITER, const.SATURN, const.TRINE): 'Баланс между расширением и структурой.',
    (const.JUPITER, const.SATURN, const.OPPOSITION): 'Конфликт между свободой и обязанностями.'
}

def get_daily_astr_events() -> List[Dict[str, str]]:
    today = date.today()
    dt = Datetime(str(today), '12:00', '+00:00')  # В полдень по UTC
    chart = Chart(dt, pos=None, IDs=PLANETS)

    events = []
    for i, body1 in enumerate(PLANETS):
        for body2 in PLANETS[i+1:]:
            if len(events) >= 3:  # Ограничение до 3 аспектов
                break
            aspect = chart.getAspect(body1, body2, ASPECTS)
            if aspect:
                key = (body1, body2, aspect.type)
                key_rev = (body2, body1, aspect.type)

                desc = ASPECT_MEANINGS.get(key) or ASPECT_MEANINGS.get(key_rev) or 'Значимое взаимодействие планет.'

                events.append({
                    'planet1': body1,
                    'planet2': body2,
                    'aspect': aspect.type,
                    'description': desc
                })
        if len(events) >= 3:
            break

    return events
