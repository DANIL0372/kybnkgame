console.log("Script loaded!");

// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;

// Основные элементы
const clickArea = document.getElementById('clickArea');
const balanceElement = document.getElementById('balance');
const usernameElement = document.getElementById('username');
const userTagElement = document.getElementById('userTag');
const clickCounterElement = document.getElementById('clickCounter');
const boostBtn = document.getElementById('boostBtn');
const boostTimerElement = document.getElementById('boostTimer');
const progressBar = document.getElementById('progressBar');
const progressLevel = document.getElementById('progressLevel');
const hourlyIncomeElement = document.getElementById('hourlyIncome');

// Игровые переменные
let coins = 0;
let coinsPerClick = 1;
let maxClicks = 100;
let currentClicks = maxClicks; // Начинаем с полными кликами
let boostActive = false;
let boostMultiplier = 1;
let boostTimeLeft = 0;
let boostTimer = null;
let hourlyIncome = 100000; // Начальный доход
let level = 0;
let levelProgress = 0;
let clickRestoreInterval;

// Уровни и прогресс
const levels = [
    { required: 0,    tag: "NEWBIE",    title: "Новичок" },
    { required: 100,  tag: "BEGINNER",  title: "Начинающий" },
    { required: 200,  tag: "EXPLORER",  title: "Исследователь" },
    { required: 300,  tag: "ADVENTURER", title: "Авантюрист" },
    { required: 400,  tag: "EXPERT",    title: "Эксперт" },
    { required: 500,  tag: "MASTER",    title: "Мастер" },
    { required: 600,  tag: "GRANDMASTER", title: "Гроссмейстер" },
    { required: 700,  tag: "LEGEND",    title: "Легенда" },
    { required: 800,  tag: "MYTHIC",    title: "Мифический" },
    { required: 900,  tag: "GODLIKE",   title: "Богоподобный" },
    { required: 1000, tag: "TITAN",     title: "Титан" },
    { required: 1100, tag: "SUPREME",   title: "Верховный" }
];

// Инициализация приложения
function initApp() {
    console.log("Initializing app...");

    // Проверка загрузки Telegram SDK
    if (!window.Telegram || !window.Telegram.WebApp) {
        console.warn("Telegram WebApp SDK not loaded, retrying...");
        setTimeout(initApp, 500);
        return;
    }

    const tg = window.Telegram.WebApp;
    tg.expand();

    // Основные элементы
    const clickArea = document.getElementById('clickArea');
    const balanceElement = document.getElementById('balance');
    const usernameElement = document.getElementById('username');

    // Проверка элементов
    if (!clickArea || !balanceElement || !usernameElement) {
        console.error("Critical elements missing!");
        return;
    }

    // Уровни
    const levels = [
        { required: 0,    tag: "NEWBIE",    title: "Новичок" },
        { required: 100,  tag: "BEGINNER",  title: "Начинающий" },
        { required: 200,  tag: "EXPLORER",  title: "Исследователь" },
        { required: 300,  tag: "ADVENTURER", title: "Авантюрист" },
        { required: 400,  tag: "EXPERT",    title: "Эксперт" },
        { required: 500,  tag: "MASTER",    title: "Мастер" },
        { required: 600,  tag: "GRANDMASTER", title: "Гроссмейстер" },
        { required: 700,  tag: "LEGEND",    title: "Легенда" },
        { required: 800,  tag: "MYTHIC",    title: "Мифический" },
        { required: 900,  tag: "GODLIKE",   title: "Богоподобный" },
        { required: 1000, tag: "TITAN",     title: "Титан" },
        { required: 1100, tag: "SUPREME",   title: "Верховный" }
    ];

    // Игровые переменные
    let coins = 0;
    let coinsPerClick = 1;
    let maxClicks = 100;
    let currentClicks = maxClicks;
    let level = 0;
    let levelProgress = 0;

    // Загрузка прогресса
    loadProgress();

    // Функция создания анимации
    function createClickEffect(event, amount) {
        const effect = document.createElement('div');
        effect.className = 'click-text-effect';
        effect.textContent = `+${amount}`;
        effect.style.left = `${event.clientX}px`;
        effect.style.top = `${event.clientY}px`;
        document.body.appendChild(effect);

        setTimeout(() => {
            effect.remove();
        }, 1200);
    }

    // Функция обновления тега пользователя
    function updateUserTag() {
        const levelTag = levels[level].tag;
        document.getElementById('userTag').textContent = `${levelTag}=${level}/11`;
    }

    // Функция обновления прогресса уровня
    function updateLevelProgress() {
        let newLevel = 0;
        for (let i = levels.length - 1; i >= 0; i--) {
            if (coins >= levels[i].required) {
                newLevel = i;
                break;
            }
        }

        if (newLevel !== level) {
            level = newLevel;
            updateUserTag();
        }

        const currentLevelMin = levels[level].required;
        const nextLevelMin = level < levels.length - 1 ? levels[level + 1].required : levels[level].required + 100;
        levelProgress = Math.min(100, ((coins - currentLevelMin) / (nextLevelMin - currentLevelMin)) * 100);

        document.documentElement.style.setProperty('--progress', `${levelProgress}%`);
        document.getElementById('progressLevel').textContent = `LEVEL ${level}`;
    }

    // Обработчик клика
    function handleClick(event) {
        if (currentClicks <= 0) return;

        currentClicks--;
        coins += coinsPerClick;

        createClickEffect(event, coinsPerClick);
        updateLevelProgress();
        updateUI();
    }

    // Обновление интерфейса
    function updateUI() {
        balanceElement.textContent = coins.toLocaleString();
        document.getElementById('clickCounter').textContent = `${currentClicks}/${maxClicks}`;
        saveProgress();
    }

    // Сохранение прогресса
    function saveProgress() {
        const progress = {
            coins,
            currentClicks,
            level,
            levelProgress
        };
        localStorage.setItem('kybnkProgress', JSON.stringify(progress));
    }

    function loadProgress() {
        const savedProgress = localStorage.getItem('kybnkProgress');
        if (savedProgress) {
            const progress = JSON.parse(savedProgress);
            coins = progress.coins || 0;
            currentClicks = progress.currentClicks || maxClicks;
            level = progress.level || 0;
            levelProgress = progress.levelProgress || 0;

            // Обновляем UI
            document.documentElement.style.setProperty('--progress', `${levelProgress}%`);
            document.getElementById('progressLevel').textContent = `LEVEL ${level}`;
            updateUserTag();
        }
    }

    // Восстановление кликов
    setInterval(() => {
        if (currentClicks < maxClicks) {
            currentClicks++;
            updateUI();
        }
    }, 3000);

    // Назначаем обработчик
    clickArea.addEventListener('click', handleClick);

    // Настройка редактирования имени
    function setupNameEditing() {
        usernameElement.addEventListener('click', () => {
            const newName = prompt('Введите ваше игровое имя:', usernameElement.textContent);
            if (newName && newName.trim() !== '') {
                const trimmedName = newName.trim();
                usernameElement.textContent = trimmedName;
                localStorage.setItem('playerName', trimmedName);
            }
        });
    }

    // Загрузка сохранённого имени
    const savedName = localStorage.getItem('playerName');
    if (savedName) {
        usernameElement.textContent = savedName;
    }

    // Настраиваем редактирование имени
    setupNameEditing();

    // Инициализация интерфейса
    updateUserTag();
    updateUI();

    console.log("App initialized successfully");

    //Кнопка сброса
    document.getElementById('resetButton').addEventListener('click', function() {
        if (confirm("Вы уверены, что хотите сбросить весь прогресс?")) {
            localStorage.clear();
            location.reload();
        }
    });
}

// Запуск при загрузке
document.addEventListener('DOMContentLoaded', initApp);

// Восстановление кликов
function startClickRestoration() {
    clearInterval(clickRestoreInterval);
    clickRestoreInterval = setInterval(() => {
        if (currentClicks < maxClicks) {
            currentClicks++;
            updateUI();
        }
    }, 3000); // 1 клик каждые 3 секунды
}

// Обновление тега пользователя
function updateUserTag() {
    const levelTag = levels[level].tag;
    userTagElement.textContent = `${levelTag}=${level}/11`;
}

// Обновляем обработчик кликов
// Обработка клика
function handleClick(event) {
    if (currentClicks <= 0) return;

    currentClicks--;
    const earned = coinsPerClick * boostMultiplier;
    coins += earned;

    // Создаем текстовый эффект (отображаем +1, +2 и т.д.)
    createClickTextEffect(event, earned);

    // Обновляем прогресс уровня
    updateLevelProgress();
    updateUI();
}

// Функция для редактирования имени
function setupNameEditing() {
    const usernameElement = document.getElementById('username');
    if (!usernameElement) return;

    usernameElement.addEventListener('click', () => {
        const newName = prompt('Введите ваше игровое имя:', usernameElement.textContent);
        if (newName && newName.trim() !== '') {
            const trimmedName = newName.trim();
            usernameElement.textContent = trimmedName;
            localStorage.setItem('playerName', trimmedName);
        }
    });
}

// Обновление прогресса уровня
function updateLevelProgress() {
    // Определяем текущий уровень
    let newLevel = 0;
    for (let i = levels.length - 1; i >= 0; i--) {
        if (coins >= levels[i].required) {
            newLevel = i;
            break;
        }
    }

     // Если уровень изменился
    if (newLevel !== level) {
        level = newLevel;
        updateUserTag();
    }

    // Рассчитываем прогресс для текущего уровня
    const currentLevelMin = levels[level].required;
    const nextLevelMin = level < levels.length - 1 ? levels[level + 1].required : levels[level].required + 100;
    levelProgress = Math.min(100, ((coins - currentLevelMin) / (nextLevelMin - currentLevelMin)) * 100);

    // Обновляем прогрессбар
    document.documentElement.style.setProperty('--progress', `${levelProgress}%`);
    document.getElementById('progressLevel').textContent = `LEVEL ${level}`;
}

// Функция обновления тега пользователя
function updateUserTag() {
    const levelTag = levels[level].tag;
    document.getElementById('userTag').textContent = `${levelTag}=${level}/11`;
}

// Активация буста
function activateBoost() {
    if (boostActive || currentClicks < 10) return;

    currentClicks -= 10;

    // Активация буста
    boostActive = true;
    boostMultiplier = 2;
    boostTimeLeft = 30;
    boostBtn.classList.add('active');

    // Запускаем таймер
    if (boostTimer) clearInterval(boostTimer);
    boostTimer = setInterval(() => {
        boostTimeLeft--;
        boostTimerElement.textContent = `${boostTimeLeft}s`;

        if (boostTimeLeft <= 0) {
            clearInterval(boostTimer);
            boostActive = false;
            boostMultiplier = 1;
            boostTimerElement.textContent = "BOOST";
            boostBtn.classList.remove('active');
        }
    }, 1000);

    updateUI();
}

// Доход в час
function updateHourlyIncome() {
    // Добавляем доход каждую секунду
    coins += hourlyIncome / 3600;
    updateLevelProgress();
    updateUI();
}

// Проверка перед инициализацией
if (clickArea && balanceElement) {
    'ngrok config add-authtoken 2yxkPDW0n8JzMcIhLKQ2pESFG2N_69Vz7adsuiDLMHpTtHpTf'
} else {
    console.error("Critical elements not found!");
}

// Новая функция для создания текстового эффекта
function createClickTextEffect(event, amount) {
    const effect = document.createElement('div');
    effect.className = 'click-text-effect';
    effect.textContent = `+${amount}`;
    effect.style.left = `${event.offsetX}px`;
    effect.style.top = `${event.offsetY}px`;
    clickArea.appendChild(effect);

    setTimeout(() => {
        effect.remove();
    }, 1200);
}

// Сохранение прогресса
function saveProgress() {
    const progress = {
        coins,
        currentClicks,
        level,
        levelProgress
    };
    localStorage.setItem('kybnkProgress', JSON.stringify(progress));
}

// Форматирование чисел с разделителями
function formatNumber(num) {
    return num.toLocaleString('en-US', {
        maximumFractionDigits: 0
    });
}

// Загрузка прогресса
function loadProgress() {
    const savedProgress = localStorage.getItem('kybnkProgress');
    if (savedProgress) {
        const progress = JSON.parse(savedProgress);
        coins = progress.coins || 0;
        currentClicks = progress.currentClicks || maxClicks;
        level = progress.level || 0;
        levelProgress = progress.levelProgress || 0;

        // Обновляем прогрессбар
        progressBar.style.setProperty('--progress', `${levelProgress}%`);
        progressLevel.textContent = `LEVEL ${level}`;
        userTagElement.textContent = `${levels[level].tag}=9/11`;
    }

    else {
        // Для новых игроков
        level = 0;
        userTagElement.textContent = `${levels[0].tag}=0/11`;
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', initApp);
