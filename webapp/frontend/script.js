// // Инициализация Telegram WebApp
// const tg = window.Telegram.WebApp;
// tg.expand();
// tg.enableClosingConfirmation();

// Добавьте тестового пользователя
window.Telegram = {
    WebApp: {
        initDataUnsafe: {
            user: { id: 123456789 }
        },
        expand: () => console.log('Expanded'),
        enableClosingConfirmation: () => console.log('Closing confirmation enabled')
    }
};

// Элементы интерфейса
const coinsEl = document.getElementById('coins');
const clickPowerEl = document.getElementById('click-power');
const autoClickersEl = document.getElementById('auto-clickers');
const clickArea = document.getElementById('click-area');
const upgradeCards = document.querySelectorAll('.upgrade-card');

// Проверяем, запущено ли приложение внутри Telegram
let tg;
try {
    tg = window.Telegram.WebApp;
    tg.expand();
    tg.enableClosingConfirmation();
} catch (e) {
    console.warn("Telegram WebApp not detected. Running in browser mode.");

    // Создаем заглушку для локального тестирования
    tg = {
        initDataUnsafe: {
            user: { id: "test_user_" + Math.floor(Math.random() * 1000) }
        },
        expand: () => console.log('Expanded'),
        enableClosingConfirmation: () => console.log('Closing confirmation enabled'),
        showPopup: (params, callback) => {
            alert(params.title + "\n" + params.message);
            if (callback) callback(true);
        }
    };

    window.Telegram = { WebApp: tg };
}

// Игровые переменные
let userData = {
    coins: 0,
    click_power: 1,
    auto_clickers: 0
};

// URL бэкенда (замените на ваш)
const BACKEND_URL = "http://localhost:5000";

// Инициализация игры
async function initGame() {
    console.log("Начало инициализации игры");
    try {
        // Проверяем, есть ли user.id
        const userId = tg.initDataUnsafe?.user?.id;
        if (!userId) {
            throw new Error("User ID not available");
        }

        console.log("User ID:", userId);

        const response = await fetch(`${BACKEND_URL}/api/user`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });

        // ... остальной код без изменений ...
    } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
        tg.showPopup?.({
            title: "Ошибка",
            message: "Не удалось загрузить данные игры: " + error.message
        }, () => {});
    }
}

// Обновление интерфейса
function updateUI() {
    coinsEl.textContent = userData.coins;
    clickPowerEl.textContent = userData.click_power;
    autoClickersEl.textContent = userData.auto_clickers;

    // Обновление цен улучшений
    upgradeCards.forEach(card => {
        const type = card.dataset.type;
        const costEl = card.querySelector('.cost');
        const button = card.querySelector('.upgrade-btn');

        let cost = 0;

        if (type === 'click_power') {
            cost = userData.click_power * 10;
        } else if (type === 'auto_clicker') {
            cost = 100 * (userData.auto_clickers + 1);
        }

        costEl.textContent = cost;
        button.disabled = userData.coins < cost;
    });
}

// Обработка клика по монете
clickArea.addEventListener('click', async () => {
    console.log("Начало обработки клика");
    try {
        const userId = tg.initDataUnsafe?.user?.id || "test_user";
        console.log("User ID:", userId);

        const response = await fetch(`${BACKEND_URL}/api/click`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId
            })
        });

        console.log("Статус ответа:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, text: ${errorText}`);
        }

        const data = await response.json();
        console.log("Данные ответа:", data);

        if (data.success) {
            // Анимация клика
            const effect = document.querySelector('.click-effect');
            effect.textContent = `+${userData.click_power}`;
            effect.style.animation = 'none';
            void effect.offsetWidth; // Сброс анимации
            effect.style.animation = 'floatUp 1s ease-out';

            // Обновление данных
            userData.coins = data.new_balance;
            updateUI();
        }
    } catch (error) {
        console.error('Полная ошибка при клике:', error);
        alert('Не удалось зарегистрировать клик: ' + error.message);
    }
});

// Покупка улучшений
upgradeCards.forEach(card => {
    const button = card.querySelector('.upgrade-btn');
    const type = card.dataset.type;

    button.addEventListener('click', async () => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/upgrade`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: tg.initDataUnsafe.user.id,
                    type: type
                })
            });

            if (!response.ok) {
                throw new Error('Ошибка сети');
            }

            const data = await response.json();

            if (data.success) {
                // Обновление данных
                userData.coins = data.new_balance;

                if (type === 'click_power') {
                    userData.click_power += 1;
                } else if (type === 'auto_clicker') {
                    userData.auto_clickers += 1;
                }

                updateUI();
            } else {
                alert('Недостаточно монет для покупки!');
            }
        } catch (error) {
            console.error('Ошибка при покупке улучшения:', error);
            alert('Не удалось купить улучшение. Попробуйте позже.');
        }
    });
});

// Система автокликеров
function startAutoClickers() {
    setInterval(async () => {
        if (userData.auto_clickers > 0) {
            try {
                const response = await fetch(`${BACKEND_URL}/api/click`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: tg.initDataUnsafe.user.id,
                        amount: userData.auto_clickers * userData.click_power
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    userData.coins = data.new_balance;
                    updateUI();
                }
            } catch (error) {
                console.error('Ошибка при автоклике:', error);
            }
        }
    }, 1000); // Каждую секунду
}

// Запуск игры при загрузке
document.addEventListener('DOMContentLoaded', initGame);