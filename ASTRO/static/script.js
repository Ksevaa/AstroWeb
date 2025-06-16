// Получаем форму входа по ID
const loginForm = document.getElementById('loginForm');

// Функция валидации формы входа при отправке
function validateLoginForm(e) {
    e.preventDefault(); // Отменяем стандартное поведение отправки формы

    const email = document.getElementById('email').value; // Получаем значение email
    const password = document.getElementById('password').value; // Получаем значение пароля
    let isValid = true; // Флаг валидности формы

    // Скрываем все сообщения об ошибках перед новой проверкой
    document.querySelectorAll('.error-message').forEach(el => {
        el.style.display = 'none';
    });

    // Проверяем email: должен быть непустым и содержать '@'
    if (!email || !email.includes('@')) {
        document.getElementById('emailError').style.display = 'block'; // Показываем ошибку email
        isValid = false;
    }

    // Проверяем пароль: должен быть непустым
    if (!password) {
        document.getElementById('passwordError').style.display = 'block'; // Показываем ошибку пароля
        isValid = false;
    }

    // Если форма валидна, снимаем обработчик и отправляем форму, меняем текст кнопки
    if (isValid) {
        loginForm.removeEventListener('submit', validateLoginForm);
        document.querySelector('.login-button').textContent = 'Вход...'; // Изменяем текст кнопки на "Вход..."
        loginForm.submit(); // Отправляем форму
    }
}

// Добавляем обработчик валидации, если форма существует
if (loginForm) {
    loginForm.addEventListener('submit', validateLoginForm);
}

// === Главная страница ===
// Функция установки текущей даты в разные элементы страницы
function setCurrentDate() {
    const date = new Date();
    const optionsDay = { weekday: 'long' }; // Опции для дня недели 
    const optionsDate = { day: 'numeric', month: 'long' }; // Опции для даты 
    const optionsYear = { year: 'numeric' }; // Опции для года 

    const dayWeek = document.getElementById('dayWeek'); // Элемент для дня недели
    const currentDate = document.getElementById('currentDate'); // Элемент для даты
    const year = document.getElementById('year'); // Элемент для года

    // Если элементы существуют, устанавливаем в них текст с локализацией 'ru-RU'
    if (dayWeek) dayWeek.textContent = date.toLocaleDateString('ru-RU', optionsDay);
    if (currentDate) currentDate.textContent = date.toLocaleDateString('ru-RU', optionsDate);
    if (year) year.textContent = date.toLocaleDateString('ru-RU', optionsYear);
}

// Переменная для текущего слайда карусели
let currentSlide = 0;
// Получаем все слайды и точки навигации
const slides = document.querySelectorAll('.interpretation-slide');
const dots = document.querySelectorAll('.dot');

// Функция отображения слайда по индексу
function showSlide(index) {
    // Скрываем все слайды и деактивируем все точки
    slides.forEach(slide => slide.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));

    // Показываем нужный слайд и активируем соответствующую точку
    slides[index].classList.add('active');
    dots[index].classList.add('active');
    currentSlide = index; // Обновляем индекс текущего слайда
}

// Кнопки переключения слайдов
const nextBtn = document.querySelector('.interpretation-next');
const prevBtn = document.querySelector('.interpretation-prev');

// Если кнопки существуют, добавляем обработчики кликов для переключения слайдов
if (nextBtn && prevBtn) {
    nextBtn.addEventListener('click', () => {
        let newIndex = currentSlide + 1;
        if (newIndex >= slides.length) newIndex = 0; // Если дошли до конца — начать с начала
        showSlide(newIndex);
    });

    prevBtn.addEventListener('click', () => {
        let newIndex = currentSlide - 1;
        if (newIndex < 0) newIndex = slides.length - 1; // Если дошли до начала — перейти к последнему
        showSlide(newIndex);
    });

    // Добавляем обработчики на точки навигации, чтобы переключать слайд по клику
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => showSlide(index));
    });
}

// === Модальное окно ===
const modal = document.getElementById('zodiacInfoModal'); // Модальное окно
const modalBtn = document.getElementById('zodiacInfoBtn'); // Кнопка для открытия модального окна
const closeModal = document.querySelector('.close-modal'); // Кнопка закрытия модального окна

// Если все элементы для модального окна существуют, добавляем обработчики
if (modal && modalBtn && closeModal) {
    // Показать модальное окно при клике на кнопку
    modalBtn.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

    // Скрыть модальное окно при клике на крестик
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Скрыть модальное окно при клике вне контента модалки
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// === Инициализация при загрузке страницы ===
window.onload = function () {
    setCurrentDate(); // Установить текущую дату

    // Если есть слайды, показать первый по умолчанию
    if (slides.length) {
        showSlide(0);
    }
};

// Обработчик для ссылки "Забыли пароль?"
document.getElementById('forgotPasswordLink').addEventListener('click', function(e) {
    e.preventDefault(); // Отменяем переход по ссылке
    alert('Для восстановления пароля обратитесь в службу поддержки!'); // Показать сообщение
});

// Обработчик события DOMContentLoaded — для инициализации карусели
document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.interpretation-slide');
    const dots = document.querySelectorAll('.dot');
    const prevBtn = document.querySelector('.interpretation-prev');
    const nextBtn = document.querySelector('.interpretation-next');

    // Если нет слайдов — выходим
    if (slides.length === 0) return;

    let currentSlide = 0;

    // Функция отображения слайда
    function showSlide(index) {
        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));

        slides[index].classList.add('active');
        dots[index].classList.add('active');
        currentSlide = index;
    }

    // Кнопка "Вперед"
    nextBtn.addEventListener('click', () => {
        let newIndex = currentSlide + 1;
        if (newIndex >= slides.length) newIndex = 0;
        showSlide(newIndex);
    });

    // Кнопка "Назад"
    prevBtn.addEventListener('click', () => {
        let newIndex = currentSlide - 1;
        if (newIndex < 0) newIndex = slides.length - 1;
        showSlide(newIndex);
    });

    // Обработчики кликов на точки
    dots.forEach((dot, idx) => {
        dot.addEventListener('click', () => {
            showSlide(idx);
        });
    });

    // Показать первый слайд по умолчанию
    showSlide(0);
});
