document.addEventListener('DOMContentLoaded', function () {
    let currentDate = new Date();
    let selectedDate = new Date();
    let weekDates = [];

    const currentMonthYearEl = document.getElementById('currentMonthYear');
    const calendarGridEl = document.getElementById('calendarGrid');
    const weekStartDateEl = document.getElementById('weekStartDate');
    const weekEndDateEl = document.getElementById('weekEndDate');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    const weekForecastDaysEl = document.querySelector('.week-forecast-days');

    function initCalendar() {
    selectedDate = new Date(currentDate);
    updateWeekDates(); 
    generateCalendar(currentDate.getMonth(), currentDate.getFullYear());
    renderWeekForecast();
    setupMenuHandlers();
}


    function setupMenuHandlers() {
        const dayButton = document.querySelector('.forecast-menu li:nth-child(1)');
        if (dayButton) {
            dayButton.addEventListener('click', function (e) {
                e.preventDefault();
                const dateParam = formatDateForURL(selectedDate);
                window.location.href = `forecast?date=${dateParam}`;
            });
        }

        const monthButton = document.querySelector('.forecast-menu li:nth-child(3)');
        if (monthButton) {
            monthButton.addEventListener('click', function () {
                window.location.href = `month-forecast?date=${selectedDate.toISOString().split('T')[0]}`;
            });
        }

        const yearButton = document.querySelector('.forecast-menu li:nth-child(4)');
        if (yearButton) {
            yearButton.addEventListener('click', function () {
                window.location.href = `year-forecast?year=${selectedDate.getFullYear()}`;
            });
        }
    }

    function formatDateForURL(date) {
        return date.toISOString().split('T')[0];
    }

    function generateCalendar(month, year) {
        calendarGridEl.innerHTML = '';
        currentDate = new Date(year, month, 1);
        currentMonthYearEl.textContent = `${getMonthName(month)} ${year}`;

        const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
        days.forEach((day) => {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day-header';
            dayEl.textContent = day;
            calendarGridEl.appendChild(dayEl);
        });

        const firstDay = new Date(year, month, 1);
        const startingDay = firstDay.getDay() || 7;
        const monthLength = new Date(year, month + 1, 0).getDate();
        const prevMonthLength = new Date(year, month, 0).getDate();

        for (let i = 1; i < 43; i++) {
            const dayEl = document.createElement('div');
            let day, isCurrentMonth;

            if (i < startingDay) {
                day = prevMonthLength - (startingDay - i - 1);
                isCurrentMonth = false;
            } else if (i - startingDay + 1 > monthLength) {
                day = i - startingDay - monthLength + 1;
                isCurrentMonth = false;
            } else {
                day = i - startingDay + 1;
                isCurrentMonth = true;
            }

            dayEl.className = `calendar-day ${isCurrentMonth ? '' : 'other-month'}`;
            dayEl.textContent = day;

            if (isCurrentMonth) {
                const date = new Date(year, month, day);

                if (isDateInCurrentWeek(date)) {
                    applyWeekSelectionStyles(dayEl, date, true);
                }

                dayEl.addEventListener('click', function () {
                    selectedDate = new Date(year, month, day);
                    updateWeekDates();
                    generateCalendar(month, year);
                    renderWeekForecast();;
                });
            }

            calendarGridEl.appendChild(dayEl);
        }
    }
    updateWeekDates();
    function applyWeekSelectionStyles(element, date, initial = false) {
    element.classList.add('week-selected');
    element.style.transition = 'all 0.3s ease';

    const dayIndex = (date.getDay() + 6) % 7; // Пн = 0, Вс = 6


    if (dayIndex === 0) {
        element.classList.add('week-start');
        element.style.backgroundColor = '#5A4ACD';
        element.style.color = 'white';
        element.style.borderRadius = '8px 0 0 8px';
    } else if (dayIndex === 6) {
        element.classList.add('week-end');
        element.style.backgroundColor = '#5A4ACD';
        element.style.color = 'white';
        element.style.borderRadius = '0 8px 8px 0';
    } else {
        element.style.backgroundColor = '#9370DB';
        element.style.color = 'white';
        element.style.borderRadius = '0';
    }

    if (initial) {
        // Задержка нужна, чтобы анимация применялась после отрисовки
        setTimeout(() => {
            element.classList.add('pulse-animation');
        }, 10); // минимальная задержка
    } else {
        element.classList.add('pulse-animation');
        setTimeout(() => {
            element.classList.remove('pulse-animation');
        }, 500);
    }
}



    function isDateInCurrentWeek(date) {
        return weekDates.some(
            (weekDate) =>
                weekDate.getDate() === date.getDate() &&
                weekDate.getMonth() === date.getMonth() &&
                weekDate.getFullYear() === date.getFullYear()
        );
    }

    function updateWeekDates() {
        weekDates = [];
        const startOfWeek = new Date(selectedDate);
        startOfWeek.setDate(selectedDate.getDate() - (selectedDate.getDay() || 7) + 1);

        for (let i = 0; i < 7; i++) {
            const date = new Date(startOfWeek);
            date.setDate(startOfWeek.getDate() + i);
            weekDates.push(date);
        }

        weekStartDateEl.textContent = formatDateForDisplay(weekDates[0]);
        weekEndDateEl.textContent = formatDateForDisplay(weekDates[6]);
    }

    function formatDateForDisplay(date) {
        const day = date.getDate();
        const month = getMonthName(date.getMonth());
        const year = date.getFullYear();
        return `${day} ${month} ${year}`;
    }

    function getMonthName(month) {
        const months = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ];
        return months[month];
    }

    function loadWeekTransits() {
    const start = weekDates[0].toISOString().split('T')[0];
    const end = weekDates[6].toISOString().split('T')[0];

    fetch(`/api/week-transits?start=${start}&end=${end}`)
        .then(response => response.json())
        .then(data => {
            const interpBlock = document.getElementById('week-forecast-interpretation');
            if (!interpBlock) return;

            if (data.error) {
                interpBlock.innerHTML = `<p class="error">${data.error}</p>`;
                return;
            }

            const transits = data.transits_by_date;
            if (!transits || Object.keys(transits).length === 0) {
                interpBlock.innerHTML = '<p>Транзитов на эту неделю не найдено.</p>';
                return;
            }

            let html = '';
            for (const [date, dayTransits] of Object.entries(transits)) {
                html += `<div class="transit-day"><strong>${formatDisplayDate(date)}</strong>:</div>`;
                dayTransits.forEach(tr => {
                    const parts = [];
                    if (tr.celestial_body && tr.sign) {
                        parts.push(`${tr.celestial_body} в знаке ${tr.sign}`);
                    }
                    if (tr.house) {
                        parts.push(`в доме ${tr.house}`);
                    }
                    if (tr.aspect) {
                        parts.push(`аспект: ${tr.aspect}`);
                    }
                    html += `<div class="transit-item">– ${parts.join(', ')}</div>`;
                });
            }
            interpBlock.innerHTML = html;
            ;
        })
        .catch(err => {
            console.error('Ошибка при загрузке транзитов:', err);
        });
}

function formatDisplayDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getDate()} ${getMonthName(date.getMonth())}`;
}

    function renderWeekForecast() {
    weekForecastDaysEl.innerHTML = '';
    weekDates.forEach((date) => {
        const dayEl = document.createElement('div');
        dayEl.className = 'week-forecast-day';
        const dayName = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.getDay() === 0 ? 6 : date.getDay() - 1];
        const formattedDate = `${date.getDate()} ${getMonthName(date.getMonth())}`;
        dayEl.innerHTML = `<strong>${dayName}</strong><br>${formattedDate}`;
        weekForecastDaysEl.appendChild(dayEl);
    });

    loadWeekTransits();
}


prevMonthBtn.addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    selectedDate = new Date(currentDate);
    updateWeekDates();
    generateCalendar(currentDate.getMonth(), currentDate.getFullYear());
    renderWeekForecast();
});

nextMonthBtn.addEventListener('click', () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    selectedDate = new Date(currentDate);
    updateWeekDates();
    generateCalendar(currentDate.getMonth(), currentDate.getFullYear());
    renderWeekForecast();
});

prevYearBtn.addEventListener('click', () => {
    currentDate.setFullYear(currentDate.getFullYear() - 1);
    selectedDate = new Date(currentDate);
    updateWeekDates();
    generateCalendar(currentDate.getMonth(), currentDate.getFullYear());
    renderWeekForecast();
});

nextYearBtn.addEventListener('click', () => {
    currentDate.setFullYear(currentDate.getFullYear() + 1);
    selectedDate = new Date(currentDate);
    updateWeekDates();
    generateCalendar(currentDate.getMonth(), currentDate.getFullYear());
    renderWeekForecast();
});


    initCalendar();
});
