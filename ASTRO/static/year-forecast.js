document.addEventListener('DOMContentLoaded', function() {
    let currentYear = new Date().getFullYear();

    const elements = {
        yearDisplays: document.querySelectorAll('.currentYear'),
        prevYearBtn: document.getElementById('prevYearBtn'),
        nextYearBtn: document.getElementById('nextYearBtn'),
        mainEvent: document.getElementById('mainEvent'),
        eventsList: document.getElementById('yearEventsList'),
        interpretationYear: document.getElementById('interpretationYear'),
        generalForecast: document.getElementById('generalForecast')
    };

    function updateYearDisplay() {
        elements.yearDisplays.forEach(el => el.textContent = currentYear);
        elements.interpretationYear.textContent = currentYear;
    }

    function updateForecastText() {
        elements.generalForecast.innerHTML = `
            <p>${currentYear} год начнется под влиянием ретроградного Марса, что может внести напряженность в глобальные процессы.</p>
            <p>Юпитер в Тельце в первой половине года создаёт благоприятную атмосферу для финансов. После мая он перейдёт в Близнецы — акцент сместится на коммуникации.</p>
            <p>Сатурн во Водолее продолжит структурные преобразования в обществе. Год — период переосмысления и роста.</p>
        `;
        
    }

    function generateYearEvents() {
        const events = [
            `Ретроградный Меркурий: 3 периода в ${currentYear} году`,
            `Затмения: 2 солнечных и 2 лунных в ${currentYear}`,
            `Юпитер перейдет в новый знак в середине ${currentYear}`,
            `Сатурн завершит цикл в ${currentYear}, открывая новые возможности`,
            `Марс будет особенно активен в конце ${currentYear}`
        ];
        elements.eventsList.innerHTML = '';
        events.forEach(event => {
            const li = document.createElement('li');
            li.textContent = event;
            elements.eventsList.appendChild(li);
        });
    }

    function setupCategoryButtons() {
        const categoryButtons = document.querySelectorAll('.interpretation-categories button');
        categoryButtons.forEach(button => {
            button.addEventListener('click', function() {
                categoryButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                updateCategoryContent(this.textContent);
            });
        });
    }

    function updateCategoryContent(category) {
        console.log(`Загрузка данных для категории: ${category}`);
        // Здесь можно динамически подгружать и отображать контент выбранной категории
    }

    function setupYearNavigation() {
        elements.prevYearBtn.addEventListener('click', () => {
            currentYear--;
            updateYearDisplay();
            updateForecastText();
            generateYearEvents();
        });

        elements.nextYearBtn.addEventListener('click', () => {
            currentYear++;
            updateYearDisplay();
            updateForecastText();
            generateYearEvents();
        });
    }

    function setupNavigationLinks() {
        document.querySelectorAll('.forecast-menu li').forEach((item, index) => {
            item.addEventListener('click', () => {
                const dateStr = `${currentYear}-01-01`;
                if (index === 0) window.location.href = `forecast.html?date=${dateStr}`;
                if (index === 1) window.location.href = `week-forecast.html?date=${dateStr}`;
                if (index === 2) window.location.href = `month-forecast.html?date=${dateStr}`;
                // index 3 — текущая страница "На год"
            });
        });
    }

    function init() {
        updateYearDisplay();
        updateForecastText();
        generateYearEvents();
        setupCategoryButtons();
        setupYearNavigation();
        setupNavigationLinks();
    }

    init();
});
