document.addEventListener('DOMContentLoaded', () => {
    // Инициализация Telegram Web App
    const tg = window.Telegram?.WebApp || {
        initDataUnsafe: { user: { id: "test_user_" + Math.floor(Math.random() * 1000) } },
        showPopup: (params) => alert(params.title + "\n" + params.message),
        close: () => window.close()
    };

    // Игровое состояние
    let gameState = {
        coins: 222566074,
        clicksCount: 5,
        maxClicks: 10,
        clickPower: 1000,
        hourlyIncome: 4570000,
        progress: 8450,
        maxProgress: 8500,
        upgrades: {
            clickPower: { level: 1, cost: 100 },
            clicksCapacity: { level: 1, cost: 200 },
            hourlyIncome: { level: 1, cost: 500 },
            autoMine: { level: 0, cost: 1000 }
        },
        boostActive: false,
        boostEndTime: 0,
        friends: [
            { name: "Иван Иванов", level: 15, coins: 150000000 },
            { name: "Мария Петрова", level: 12, coins: 120000000 },
            { name: "Алексей Смирнов", level: 10, coins: 100000000 },
            { name: "Елена Кузнецова", level: 8, coins: 80000000 },
            { name: "Дмитрий Попов", level: 5, coins: 50000000 }
        ]
    };

    // Элементы интерфейса
    const elements = {
        username: document.getElementById('username'),
        mainScore: document.getElementById('main-score'),
        clicksCount: document.getElementById('clicks-count'),
        maxClicks: document.getElementById('max-clicks'),
        progressText: document.getElementById('progress-text'),
        progressFill: document.getElementById('progress-fill'),
        boostBtn: document.getElementById('boost-btn'),
        hourlyIncome: document.getElementById('hourly-income'),
        profileBtn: document.getElementById('profile-btn'),
        settingsBtn: document.getElementById('settings-btn'),
        referralLink: document.getElementById('referral-link'),
        leaderboardBody: document.getElementById('leaderboard-body'),
        copyBtn: document.getElementById('copy-btn'),
        navBtns: document.querySelectorAll('.nav-btn'),
        screens: document.querySelectorAll('.screen')
    };

    // Установка имени пользователя из Telegram
    if (tg.initDataUnsafe?.user) {
        const user = tg.initDataUnsafe.user;
        const username = user.username
            ? `@${user.username}`
            : `${user.first_name || 'User'}${user.last_name ? ' ' + user.last_name : ''}`;
        elements.username.textContent = username;

        // Генерация реферальной ссылки
        elements.referralLink.textContent =
            `https://t.me/kybnkshow_bot?start=ref_${user.id}`;
    }

    // Форматирование чисел
    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(2) + 'M';
        }
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Обновление интерфейса
    function updateUI() {
        // Обновление основной информации
        elements.mainScore.textContent = formatNumber(gameState.coins);
        elements.clicksCount.textContent = gameState.clicksCount;
        elements.maxClicks.textContent = gameState.maxClicks;
        elements.hourlyIncome.textContent = formatNumber(gameState.hourlyIncome);

        // Обновление прогресс-бара
        const progressPercent = (gameState.progress / gameState.maxProgress) * 100;
        elements.progressFill.style.width = `${progressPercent}%`;
        elements.progressText.textContent =
            `${gameState.progress}/${gameState.maxProgress}`;

        // Обновление кнопки Boost
        if (gameState.boostActive) {
            const timeLeft = Math.ceil((gameState.boostEndTime - Date.now()) / 1000);
            if (timeLeft > 0) {
                elements.boostBtn.innerHTML = `<i class="fas fa-bolt"></i> BOOST (${timeLeft}s)`;
                elements.boostBtn.classList.add('disabled');
            } else {
                gameState.boostActive = false;
                elements.boostBtn.innerHTML = '<i class="fas fa-bolt"></i> BOOST';
                elements.boostBtn.classList.remove('disabled');
            }
        }

        // Обновление таблицы лидеров
        updateLeaderboard();

        // Обновление улучшений
        updateUpgradesUI();
    }

    // Обновление таблицы лидеров
    function updateLeaderboard() {
        elements.leaderboardBody.innerHTML = '';

        gameState.friends.sort((a, b) => b.coins - a.coins)
            .forEach(friend => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${friend.name}</td>
                    <td>${friend.level}</td>
                    <td>${formatNumber(friend.coins)}</td>
                `;
                elements.leaderboardBody.appendChild(row);
            });
    }

    // Обновление UI улучшений
    function updateUpgradesUI() {
        document.getElementById('click-power-level').textContent =
            gameState.upgrades.clickPower.level;
        document.getElementById('click-power-cost').textContent =
            gameState.upgrades.clickPower.cost;

        document.getElementById('clicks-capacity-level').textContent =
            gameState.upgrades.clicksCapacity.level;
        document.getElementById('clicks-capacity-cost').textContent =
            gameState.upgrades.clicksCapacity.cost;

        document.getElementById('hourly-income-level').textContent =
            gameState.upgrades.hourlyIncome.level;
        document.getElementById('hourly-income-cost').textContent =
            gameState.upgrades.hourlyIncome.cost;

        document.getElementById('auto-mine-level').textContent =
            gameState.upgrades.autoMine.level;
        document.getElementById('auto-mine-cost').textContent =
            gameState.upgrades.autoMine.cost;
    }

    // Обработка кликов по экрану
    document.querySelector('.home-screen').addEventListener('click', (e) => {
        if (gameState.clicksCount <= 0) return;
        if (e.target.closest('.progress-container') || e.target.closest('.btn')) return;

        // Уменьшаем счетчик кликов
        gameState.clicksCount--;

        // Добавляем монеты
        const coinsEarned = gameState.boostActive
            ? gameState.clickPower * 2
            : gameState.clickPower;
        gameState.coins += coinsEarned;

        // Создаем эффект
        createClickEffect(e, `+${formatNumber(coinsEarned)}`);

        // Обновляем UI
        updateUI();
    });

    // Создание эффекта клика
    function createClickEffect(event, text) {
        const effect = document.createElement('div');
        effect.className = 'click-effect';
        effect.textContent = text;
        effect.style.position = 'absolute';
        effect.style.left = `${event.clientX}px`;
        effect.style.top = `${event.clientY}px`;
        effect.style.color = gameState.boostActive ? '#f97316' : '#4ade80';
        effect.style.fontWeight = 'bold';
        effect.style.fontSize = '1.2rem';
        effect.style.animation = 'floatUp 1s forwards';
        document.querySelector('.home-screen').appendChild(effect);

        setTimeout(() => effect.remove(), 1000);
    }

    // Обработка кнопки Boost
    elements.boostBtn.addEventListener('click', () => {
        if (gameState.boostActive || elements.boostBtn.classList.contains('disabled')) return;

        gameState.boostActive = true;
        gameState.boostEndTime = Date.now() + 30000; // 30 секунд

        elements.boostBtn.innerHTML = '<i class="fas fa-bolt"></i> BOOST (30s)';
        elements.boostBtn.classList.add('disabled');

        // Запускаем таймер обратного отсчета
        const boostTimer = setInterval(() => {
            const timeLeft = Math.ceil((gameState.boostEndTime - Date.now()) / 1000);

            if (timeLeft > 0) {
                elements.boostBtn.innerHTML = `<i class="fas fa-bolt"></i> BOOST (${timeLeft}s)`;
            } else {
                clearInterval(boostTimer);
                gameState.boostActive = false;
                elements.boostBtn.innerHTML = '<i class="fas fa-bolt"></i> BOOST';
                elements.boostBtn.classList.remove('disabled');
            }
        }, 1000);
    });

    // Обработка кнопки Profile
    elements.profileBtn.addEventListener('click', () => {
        tg.showPopup({
            title: "Ваш профиль",
            message: `Уровень: ${Math.floor(gameState.progress/1000)}\nМонеты: ${formatNumber(gameState.coins)}`
        });
    });

    // Обработка кнопки Settings
    elements.settingsBtn.addEventListener('click', () => {
        tg.showPopup({
            title: "Настройки",
            message: "Звук: Вкл\nУведомления: Вкл\nЯзык: Русский"
        });
    });

    // Обработка кнопки Copy
    elements.copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(elements.referralLink.textContent)
            .then(() => {
                tg.showPopup({
                    title: "Скопировано!",
                    message: "Реферальная ссылка скопирована в буфер обмена"
                });
            });
    });

    // Обработка навигации
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Обновление активной кнопки
            elements.navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Показ активного экрана
            const screenId = btn.dataset.screen;
            elements.screens.forEach(screen => screen.classList.remove('active'));
            document.querySelector(`.${screenId}`).classList.add('active');
        });
    });

    // Обработка улучшений
    document.querySelectorAll('.upgrade-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const upgradeType = btn.dataset.type;
            const upgrade = gameState.upgrades[upgradeType];

            // Проверка наличия средств
            if (gameState.coins < upgrade.cost) {
                tg.showPopup({
                    title: "Недостаточно монет",
                    message: `Нужно ещё ${upgrade.cost - gameState.coins} монет`
                });
                return;
            }

            // Покупка улучшения
            gameState.coins -= upgrade.cost;

            // Применение улучшения
            switch (upgradeType) {
                case 'click-power':
                    gameState.clickPower += 100;
                    break;
                case 'clicks-capacity':
                    gameState.maxClicks += 5;
                    gameState.clicksCount = gameState.maxClicks;
                    break;
                case 'hourly-income':
                    gameState.hourlyIncome += 1000000;
                    break;
                case 'auto-mine':
                    // Автоматическая добыча работает даже когда приложение закрыто
                    break;
            }

            // Увеличение уровня и стоимости
            upgrade.level++;
            upgrade.cost = Math.round(upgrade.cost * 1.5);

            // Обновление UI
            updateUI();

            tg.showPopup({
                title: "Улучшение куплено!",
                message: `Уровень ${upgradeType} увеличен до ${upgrade.level}`
            });
        });
    });

    // Обработка кнопки закрытия
    document.querySelector('.close-btn').addEventListener('click', () => {
        tg.showConfirm("Вы уверены, что хотите выйти?", (confirmed) => {
            if (confirmed) {
                saveGameState();
                tg.close();
            }
        });
    });

    // Автоматическая добыча (работает даже когда приложение закрыто)
    function processAutoMine() {
        const now = Date.now();
        const lastPlayed = localStorage.getItem('lastPlayed');

        if (lastPlayed) {
            const timePassed = now - parseInt(lastPlayed);
            const hoursPassed = timePassed / (1000 * 60 * 60);
            const coinsEarned = hoursPassed * gameState.hourlyIncome;

            if (coinsEarned > 0) {
                gameState.coins += Math.floor(coinsEarned);
                tg.showPopup({
                    title: "Автоматическая добыча",
                    message: `За время вашего отсутствия добыто: ${formatNumber(Math.floor(coinsEarned))} монет!`
                });
            }
        }

        localStorage.setItem('lastPlayed', now.toString());
    }

    // Сохранение состояния игры
    function saveGameState() {
        localStorage.setItem('gameState', JSON.stringify(gameState));
        localStorage.setItem('lastPlayed', Date.now().toString());
    }

    // Загрузка состояния игры
    function loadGameState() {
        const savedState = localStorage.getItem('gameState');
        if (savedState) {
            gameState = JSON.parse(savedState);
        }

        // Восстановление буста
        if (gameState.boostActive && gameState.boostEndTime < Date.now()) {
            gameState.boostActive = false;
        }

        // Обработка автоматической добычи
        processAutoMine();
    }

    // Инициализация игры
    function initGame() {
        // Загрузка состояния
        loadGameState();

        // Обновление UI
        updateUI();

        // Автосохранение каждые 30 секунд
        setInterval(saveGameState, 30000);

        // Восстановление кликов каждые 5 минут
        setInterval(() => {
            if (gameState.clicksCount < gameState.maxClicks) {
                gameState.clicksCount = Math.min(
                    gameState.clicksCount + 1,
                    gameState.maxClicks
                );
                updateUI();
            }
        }, 300000); // 5 минут

        // Тестовое сообщение в Telegram
        tg.ready();
    }

    // Запуск игры
    initGame();
});