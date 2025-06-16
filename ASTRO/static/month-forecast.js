document.addEventListener('DOMContentLoaded', function () {
    const currentDate = new Date();

    const elements = {
        monthSelect: document.getElementById('monthSelect'),
        yearSelect: document.getElementById('yearSelect'),
        monthYear: document.getElementById('currentMonthYear'),
        sunSign: document.getElementById('sunSign'),
        eventsList: document.getElementById('monthEventsList'),
        categoryButtons: document.querySelectorAll('.interpretation-categories button'),
        forecastMonthYearText: document.getElementById('forecastMonthYearText'),
        forecastTextBlock: document.getElementById('forecastTextBlock'),
        forecastTitle: document.getElementById('generalForecastTitle')
    };

    const categoryTitles = [
        'Общий прогноз',       // 6
        'Любовный прогноз',    // 7
        'Прогноз карьеры',     // 8
        'Финансовый прогноз',  // 9
        'Прогноз здоровья'     // 10
    ];

    function init() {
        elements.monthSelect.value = currentDate.getMonth();
        elements.yearSelect.value = currentDate.getFullYear();

        updateMonthInfo();
        setupEventListeners();
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return `${date.getDate()} ${getMonthName(date.getMonth())}`;
    }

    function updateMonthInfo() {
        const month = parseInt(elements.monthSelect.value);
        const year = parseInt(elements.yearSelect.value);

        const monthName = getMonthName(month);
        elements.monthYear.textContent = `${monthName} ${year}`;
        elements.forecastMonthYearText.textContent = `${monthName} ${year}`;
        elements.forecastTitle.textContent = `${categoryTitles[0]} на ${monthName} ${year}`;

        // Обновление списка событий
        fetch(`/api/month-forecast?year=${year}&month=${month}`)
            .then(response => response.json())
            .then(data => {
                elements.sunSign.textContent = data.sunSign;

                elements.eventsList.innerHTML = '';
                data.events.forEach(event => {
                    const li = document.createElement('li');
                    li.textContent = `${formatDate(event.date)} — ${event.event}`;
                    elements.eventsList.appendChild(li);
                });
            });

        // Загрузка прогноза по умолчанию (общий = категория 6)
        loadForecast(month, year, 6, 0);
    }

    function loadForecast(month, year, categoryId, titleIndex) {
        fetch(`/api/month-forecast?month=${month + 1}&year=${year}&category_id=${categoryId}`)
            .then(response => response.json())
            .then(data => {
                elements.forecastTextBlock.innerHTML = '';

                if (data.interpretation && data.interpretation.length > 0) {
                    data.interpretation.forEach(item => {
                        const p = document.createElement('p');
                        p.textContent = item;
                        elements.forecastTextBlock.appendChild(p);
                    });
                } else {
                    elements.forecastTextBlock.innerHTML = '<p>Нет данных прогноза для выбранной категории.</p>';
                }

                const monthName = getMonthName(month);
                const yearText = year;
                elements.forecastTitle.textContent = `${categoryTitles[titleIndex]} на ${monthName} ${yearText}`;
                elements.forecastMonthYearText.textContent = `${monthName} ${yearText}`;
            })
            .catch(error => {
                console.error('Ошибка при загрузке прогноза:', error);
                elements.forecastTextBlock.innerHTML = '<p>Ошибка загрузки прогноза.</p>';
            });
    }

    function getMonthName(monthIndex) {
        const months = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ];
        return months[monthIndex];
    }

    function setupEventListeners() {
        elements.monthSelect.addEventListener('change', updateMonthInfo);
        elements.yearSelect.addEventListener('change', updateMonthInfo);

        elements.categoryButtons.forEach((button, index) => {
            button.addEventListener('click', function () {
                elements.categoryButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                const selectedMonth = parseInt(elements.monthSelect.value);
                const selectedYear = parseInt(elements.yearSelect.value);
                const categoryId = 6 + index;
                

                loadForecast(selectedMonth, selectedYear, categoryId, index);
            });
        });
    }

    init();
});
