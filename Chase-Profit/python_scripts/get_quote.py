import yfinance as yf
import pandas as pd
from datetime import datetime


def get_currency_quote(currency_symbol):
    """
    Получает котировку валюты/криптовалюты по отношению к доллару
    """
    try:
        # Формируем тикер для Yahoo Finance
        if currency_symbol.upper() in ['BTC', 'ETH', 'ADA', 'DOT', 'LTC', 'XRP', 'DOGE']:
            # Для криптовалют используем формат BTC-USD
            ticker = f"{currency_symbol.upper()}-USD"
        else:
            # Для фиатных валют используем формат EURUSD=X
            ticker = f"{currency_symbol.upper()}USD=X"

        # Получаем данные
        currency_data = yf.Ticker(ticker)
        info = currency_data.info

        # Получаем исторические данные за последний день
        hist = currency_data.history(period="1d")

        if hist.empty:
            return None, "Не удалось получить данные для указанной валюты"

        # Текущая цена (последняя доступная)
        current_price = hist['Close'].iloc[-1]

        # Изменение цены
        price_change = hist['Close'].iloc[-1] - hist['Open'].iloc[0]
        price_change_percent = (price_change / hist['Open'].iloc[0]) * 100

        result = {
            'symbol': currency_symbol.upper(),
            'current_price': current_price,
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'open': hist['Open'].iloc[0],
            'high': hist['High'].iloc[0],
            'low': hist['Low'].iloc[0],
            'volume': hist['Volume'].iloc[0] if 'Volume' in hist.columns else None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return result, None

    except Exception as e:
        return None, f"Ошибка при получении данных: {str(e)}"


def print_currency_info(currency_data):
    """
    Красиво выводит информацию о валюте
    """
    if not currency_data:
        return

    print(f"\n{'=' * 50}")
    print(f"КОТИРОВКА: {currency_data['symbol']}/USD")
    print(f"{'=' * 50}")
    print(f"Текущая цена: ${currency_data['current_price']:.6f}")

    # Цвет для изменения цены (зеленый для роста, красный для падения)
    change_color = "\033[92m" if currency_data['price_change'] >= 0 else "\033[91m"
    reset_color = "\033[0m"

    print(
        f"Изменение: {change_color}{currency_data['price_change']:+.6f} ({currency_data['price_change_percent']:+.2f}%){reset_color}")
    print(f"Открытие: ${currency_data['open']:.6f}")
    print(f"Максимум: ${currency_data['high']:.6f}")
    print(f"Минимум: ${currency_data['low']:.6f}")

    if currency_data['volume']:
        print(f"Объем: {currency_data['volume']:,.0f}")

    print(f"Время обновления: {currency_data['timestamp']}")
    print(f"{'=' * 50}")


def show_available_currencies():
    """
    Показывает список доступных валют
    """
    print("\nДоступные валюты:")
    print("-" * 30)

    print("Фиатные валюты:")
    fiat_currencies = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'RUB']
    for i, currency in enumerate(fiat_currencies, 1):
        print(f"  {i}. {currency}")

    print("\nКриптовалюты:")
    crypto_currencies = ['BTC', 'ETH', 'ADA', 'DOT', 'LTC', 'XRP', 'DOGE', 'BNB']
    for i, currency in enumerate(crypto_currencies, 1):
        print(f"  {i}. {currency}")

    print("\nВы можете вводить код валюты (например: EUR, BTC)")


def main():
    """
    Основная функция программы
    """
    print("💰 КОТИРОВКИ ВАЛЮТ И КРИПТОВАЛЮТ 💰")
    print("Получение данных через Yahoo Finance API")

    while True:
        print("\n" + "=" * 50)
        print("1. Получить котировку валюты")
        print("2. Показать список доступных валют")
        print("3. Выход")

        choice = input("\nВыберите действие (1-3): ").strip()

        if choice == '1':
            currency_symbol = input("\nВведите код валюты (например: EUR, BTC): ").strip()

            if not currency_symbol:
                print("❌ Пожалуйста, введите код валюты")
                continue

            print(f"\n🔄 Получение данных для {currency_symbol.upper()}...")

            currency_data, error = get_currency_quote(currency_symbol)

            if error:
                print(f"❌ {error}")
                print("Проверьте правильность кода валюты и попробуйте снова")
            else:
                print_currency_info(currency_data)

        elif choice == '2':
            show_available_currencies()

        elif choice == '3':
            print("👋 До свидания!")
            break

        else:
            print("❌ Неверный выбор. Пожалуйста, выберите 1, 2 или 3")


if __name__ == "__main__":
    # Установите библиотеку yfinance если еще не установлена:
    # pip install yfinance pandas
    main()