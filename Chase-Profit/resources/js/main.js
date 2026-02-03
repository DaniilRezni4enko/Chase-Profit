const sampleTrades = [
    {
        pair: 'BTC/USDT',
        type: 'buy',
        entryPrice: 42500.50,
        exitPrice: 42850.25,
        volume: 0.1,
        profit: 34.98,
        timestamp: '2024-01-15 14:30:25'
    },
    {
        pair: 'ETH/USDT',
        type: 'sell',
        entryPrice: 2550.75,
        exitPrice: 2530.20,
        volume: 2.5,
        profit: -51.38,
        timestamp: '2024-01-15 14:25:10'
    },
    {
        pair: 'SOL/USDT',
        type: 'buy',
        entryPrice: 98.45,
        exitPrice: 102.30,
        volume: 15,
        profit: 57.75,
        timestamp: '2024-01-15 14:20:45'
    },
    {
        pair: 'XRP/USDT',
        type: 'sell',
        entryPrice: 0.578,
        exitPrice: 0.572,
        volume: 1000,
        profit: -6.00,
        timestamp: '2024-01-15 14:15:30'
    },
    {
        pair: 'ADA/USDT',
        type: 'buy',
        entryPrice: 0.512,
        exitPrice: 0.525,
        volume: 2000,
        profit: 26.00,
        timestamp: '2024-01-15 14:10:15'
    }
];

const currencyPairs = [
    { pair: 'BTC/USDT', change: 2.34 },
    { pair: 'ETH/USDT', change: -1.23 },
    { pair: 'SOL/USDT', change: 5.67 },
    { pair: 'XRP/USDT', change: 0.89 },
    { pair: 'ADA/USDT', change: -0.45 },
    { pair: 'DOT/USDT', change: 1.23 },
    { pair: 'LINK/USDT', change: -0.78 },
    { pair: 'LTC/USDT', change: 0.45 }
];

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeDropdowns();
    initializeCurrencySelector();
    initializeTradesTable();
    initializeEventListeners();
});

// Инициализация темы
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.className = savedTheme + '-theme';
    updateThemeIcon(savedTheme);
}

// Обновление иконки темы
function updateThemeIcon(theme) {
    const themeIcon = document.querySelector('#themeToggle i');
    themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// Инициализация выпадающих списков
function initializeDropdowns() {
    const dropdowns = document.querySelectorAll('.currency-selector, .auth-dropdown');

    dropdowns.forEach(dropdown => {
        const button = dropdown.querySelector('button');
        const menu = dropdown.querySelector('.currency-dropdown, .auth-menu');

        button.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllDropdowns();
            menu.classList.toggle('show');
        });
    });

    // Закрытие dropdown при клике вне элемента
    document.addEventListener('click', closeAllDropdowns);
}

function closeAllDropdowns() {
    document.querySelectorAll('.currency-dropdown, .auth-menu').forEach(menu => {
        menu.classList.remove('show');
    });
}

// Инициализация выбора валюты
function initializeCurrencySelector() {
    const currencyItems = document.querySelectorAll('.currency-item');

    currencyItems.forEach(item => {
        item.addEventListener('click', function() {
            const pair = this.getAttribute('data-pair');
            const change = this.querySelector('.price-change').textContent;

            // Обновляем кнопку
            const currencyBtn = document.querySelector('.currency-btn');
            currencyBtn.querySelector('.currency-pair').textContent = pair;

            // Обновляем заголовок графика
            document.querySelector('.chart-header h3').textContent = pair;

            // Снимаем активный класс со всех элементов
            currencyItems.forEach(i => i.classList.remove('active'));
            // Добавляем активный класс к выбранному
            this.classList.add('active');

            closeAllDropdowns();
        });
    });
}

// Инициализация таблицы сделок
function initializeTradesTable() {
    const tableBody = document.getElementById('tradesTable');

    sampleTrades.forEach(trade => {
        const row = createTradeRow(trade);
        tableBody.appendChild(row);
    });
}

// Создание строки сделки
function createTradeRow(trade) {
    const row = document.createElement('div');
    row.className = 'trade-row';

    const profitClass = trade.profit >= 0 ? 'profit-positive' : 'profit-negative';
    const profitSign = trade.profit >= 0 ? '+' : '';
    const typeClass = trade.type === 'buy' ? 'buy' : 'sell';

    row.innerHTML = `
        <span>${trade.pair}</span>
        <span class="trade-type ${typeClass}">${trade.type === 'buy' ? 'Покупка' : 'Продажа'}</span>
        <span>$${trade.entryPrice.toLocaleString()}</span>
        <span>$${trade.exitPrice.toLocaleString()}</span>
        <span>${trade.volume}</span>
        <span class="${profitClass}">${profitSign}$${Math.abs(trade.profit).toFixed(2)}</span>
        <span>${trade.timestamp}</span>
    `;

    return row;
}

// Инициализация обработчиков событий
function initializeEventListeners() {
    // Переключение темы
    const themeToggle = document.getElementById('themeToggle');
    themeToggle.addEventListener('click', toggleTheme);

    // Фильтрация сделок
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterTrades(this.textContent);
        });
    });

    // Таймфреймы графика
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');
    timeframeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            timeframeBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Навигационные ссылки
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Логотип - редирект на главную
    const logo = document.querySelector('.logo');
    logo.addEventListener('click', function(e) {
        e.preventDefault();
        // В реальном приложении здесь был бы переход на главную
        navLinks.forEach(l => l.classList.remove('active'));
        document.querySelector('.nav-link').classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Переключение темы
function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    const newTheme = isDark ? 'light' : 'dark';

    document.body.className = newTheme + '-theme';
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

// Фильтрация сделок
function filterTrades(filter) {
    const tableBody = document.getElementById('tradesTable');
    const rows = tableBody.querySelectorAll('.trade-row');

    rows.forEach(row => {
        const type = row.querySelector('.trade-type').textContent;

        switch(filter) {
            case 'Все':
                row.style.display = 'grid';
                break;
            case 'Покупка':
                row.style.display = type === 'Покупка' ? 'grid' : 'none';
                break;
            case 'Продажа':
                row.style.display = type === 'Продажа' ? 'grid' : 'none';
                break;
        }
    });
}

// Симуляция обновления данных в реальном времени
function simulateLiveUpdates() {
    setInterval(() => {
        // Обновление цен в выпадающем списке
        const currencyItems = document.querySelectorAll('.currency-item');
        currencyItems.forEach(item => {
            const changeElement = item.querySelector('.price-change');
            const currentChange = parseFloat(changeElement.textContent);
            const randomChange = (Math.random() - 0.5) * 2;
            const newChange = currentChange + randomChange;

            changeElement.textContent = (newChange >= 0 ? '+' : '') + newChange.toFixed(2) + '%';
            changeElement.className = `price-change ${newChange >= 0 ? 'positive' : 'negative'}`;
        });

        // Добавление случайной новой сделки
        const pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT'];
        const types = ['buy', 'sell'];
        const randomPair = pairs[Math.floor(Math.random() * pairs.length)];
        const randomType = types[Math.floor(Math.random() * types.length)];

        const newTrade = {
            pair: randomPair,
            type: randomType,
            entryPrice: Math.random() * 1000 + 100,
            exitPrice: Math.random() * 1000 + 100,
            volume: Math.random() * 10,
            profit: (Math.random() - 0.5) * 200,
            timestamp: new Date().toLocaleString('ru-RU')
        };

        const tableBody = document.getElementById('tradesTable');
        const newRow = createTradeRow(newTrade);
        tableBody.insertBefore(newRow, tableBody.firstChild);

        // Ограничение количества отображаемых сделок
        if (tableBody.children.length > 10) {
            tableBody.removeChild(tableBody.lastChild);
        }

    }, 5000); // Обновление каждые 5 секунд
}

// Запуск симуляции обновлений
simulateLiveUpdates();