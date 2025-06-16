document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const dateFromUrl = urlParams.get('date');
    let currentDate = dateFromUrl ? new Date(dateFromUrl) : new Date();
    let selectedDate = new Date(currentDate);
    let selectedCategory = 'general';

    function formatDate(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }

  async function fetchForecast() {
    const dateStr = formatDate(selectedDate);
    const response = await fetch('/forecast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ date: dateStr, category: selectedCategory })
    });

    const data = await response.json();
    const content = document.querySelector('.interpretation-content');
    const currentDateLabel = document.getElementById('currentSelectedDate')

    currentDateLabel.textContent = formatDisplayDate(selectedDate);

    if (data.forecast) {
      content.innerHTML = `
        <h3>${getCategoryName(selectedCategory)} на ${formatDisplayDate(selectedDate)}</h3>
        <p>${data.forecast}</p>
      `;
    } else {
      content.innerHTML = `<p>Прогноз не найден или возникла ошибка.</p>`;
    }
  }

  function getCategoryName(category) {
    switch (category) {
      case 'general': return 'Общий прогноз';
      case 'love': return 'Прогноз любви';
      case 'career': return 'Прогноз карьеры';
      case 'finance': return 'Прогноз финансов';
      case 'health': return 'Прогноз здоровья';
      default: return 'Прогноз';
    }
  }

  function formatDisplayDate(date) {
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric', month: 'long', year: 'numeric'
    });
  }

  // Навешиваем обработчики на категории
  document.querySelectorAll('.interpretation-categories button').forEach((btn, idx) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.interpretation-categories button').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });

      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      selectedCategory = ['general', 'love', 'career', 'finance', 'health'][idx];
      fetchForecast();
    });
  });

    const elements = {
        monthYear: document.getElementById('currentMonthYear'),
        grid: document.getElementById('calendarGrid'),
        selectedDate: document.getElementById('currentSelectedDate'),
        prevMonth: document.getElementById('prevMonth'),
        nextMonth: document.getElementById('nextMonth'),
        prevYear: document.getElementById('prevYear'),
        nextYear: document.getElementById('nextYear'),
        menuItems: document.querySelectorAll('.forecast-menu li'),
    };

    function init() {
        renderCalendar();
        updateSelectedDateText();
        highlightActiveMenu();
        setupEventListeners();
        fetchForecast();
    }

    function renderCalendar() {
        elements.grid.innerHTML = '';
        elements.monthYear.textContent = `${getMonthName(currentDate.getMonth())} ${currentDate.getFullYear()}`;

        ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].forEach(day => {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day-header';
            dayEl.textContent = day;
            elements.grid.appendChild(dayEl);
        });

        const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        let startingDay = firstDay.getDay();
        if (startingDay === 0) startingDay = 7;

        const monthLength = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
        const prevMonthLength = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate();

        for (let i = 1; i <= 42; i++) {
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
                if (
                    currentDate.getFullYear() === selectedDate.getFullYear() &&
                    currentDate.getMonth() === selectedDate.getMonth() &&
                    day === selectedDate.getDate()
                ) {
                    dayEl.classList.add('selected');
                }

                dayEl.addEventListener('click', () => {
                    selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
                    updateSelectedDateText();
                    renderCalendar();
                    fetchForecast();  
                });
            }
            elements.grid.appendChild(dayEl);
        }
    }

    function updateSelectedDateText() {
        const options = { day: 'numeric', month: 'long', year: 'numeric' };
        elements.selectedDate.textContent = selectedDate.toLocaleDateString('ru-RU', options);
    }

    function getMonthName(monthIndex) {
        const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
        return months[monthIndex];
    }

    function highlightActiveMenu() {
        const path = window.location.pathname;
        elements.menuItems.forEach(item => item.classList.remove('active'));

        if (path.includes('week-forecast')) {
            elements.menuItems[1].classList.add('active');
        } else if (path.includes('month-forecast')) {
            elements.menuItems[2].classList.add('active');
        } else if (path.includes('year-forecast')) {
            elements.menuItems[3].classList.add('active');
        } else {
            elements.menuItems[0].classList.add('active'); 
        }
    }

    function setupEventListeners() {
        elements.prevMonth.addEventListener('click', () => {
            currentDate.setMonth(currentDate.getMonth() - 1);
            if (
                selectedDate.getMonth() !== currentDate.getMonth() ||
                selectedDate.getFullYear() !== currentDate.getFullYear()
            ) {
                selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
                updateSelectedDateText();
            }
            renderCalendar();
        });

        elements.nextMonth.addEventListener('click', () => {
            currentDate.setMonth(currentDate.getMonth() + 1);
            if (
                selectedDate.getMonth() !== currentDate.getMonth() ||
                selectedDate.getFullYear() !== currentDate.getFullYear()
            ) {
                selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
                updateSelectedDateText();
            }
            renderCalendar();
        });

        elements.prevYear.addEventListener('click', () => {
            currentDate.setFullYear(currentDate.getFullYear() - 1);
            selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            updateSelectedDateText();
            renderCalendar();
        });

        elements.nextYear.addEventListener('click', () => {
            currentDate.setFullYear(currentDate.getFullYear() + 1);
            selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            updateSelectedDateText();
            renderCalendar();
        });

        // Меню прогноза
        elements.menuItems[0].addEventListener('click', () => {
            window.location.href = `/forecast?date=${selectedDate.toISOString().split('T')[0]}`;
        });
        elements.menuItems[1].addEventListener('click', () => {
            window.location.href = `/week-forecast?date=${selectedDate.toISOString().split('T')[0]}`;
        });
        elements.menuItems[2].addEventListener('click', () => {
            window.location.href = `/month-forecast?date=${selectedDate.toISOString().split('T')[0]}`;
        });
        elements.menuItems[3].addEventListener('click', () => {
            window.location.href = `/year-forecast?year=${selectedDate.getFullYear()}`;
        });

        // Кнопки категорий интерпретации
        document.querySelectorAll('.interpretation-categories button').forEach(button => {
            button.addEventListener('click', function () {
                document.querySelectorAll('.interpretation-categories button').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
            });
        });
    }

    init();
});
