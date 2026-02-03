import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import time

warnings.filterwarnings('ignore')


class CryptoDataFetcher:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.session = requests.Session()

        self.popular_cryptos = {
            'BTCUSDT': 'Bitcoin',
            'ETHUSDT': 'Ethereum',
            'ADAUSDT': 'Cardano',
            'DOTUSDT': 'Polkadot',
            'LTCUSDT': 'Litecoin',
            'XRPUSDT': 'Ripple',
            'DOGEUSDT': 'Dogecoin',
            'BNBUSDT': 'Binance Coin',
            'SOLUSDT': 'Solana',
            'MATICUSDT': 'Polygon',
            'AVAXUSDT': 'Avalanche',
            'LINKUSDT': 'Chainlink',
            'USDTUSDT': 'Tether',
            'USDCUSDT': 'USD Coin',
            'ATOMUSDT': 'Cosmos',
            'UNIUSDT': 'Uniswap'
        }

        # Bybit поддерживаемые интервалы: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, M, W
        self.timeframes = {
            '1': {'interval': '1', 'name': '1 минута', 'max_candles': 200, 'limit': 200},
            '2': {'interval': '5', 'name': '5 минут', 'max_candles': 200, 'limit': 200},
            '3': {'interval': '15', 'name': '15 минут', 'max_candles': 200, 'limit': 200},
            '4': {'interval': '60', 'name': '1 час', 'max_candles': 200, 'limit': 200},
            '5': {'interval': 'D', 'name': '1 день', 'max_candles': 200, 'limit': 200},
            '6': {'interval': 'W', 'name': '1 неделя', 'max_candles': 100, 'limit': 100},
            '7': {'interval': 'M', 'name': '1 месяц', 'max_candles': 50, 'limit': 50}
        }

    def validate_crypto_symbol(self, symbol):
        """
        Проверяет, существует ли криптовалюта с таким символом на Bybit
        """
        try:
            # Приводим символ к формату Bybit (добавляем USDT если нужно)
            symbol = self._format_symbol(symbol)

            url = f"{self.base_url}/v5/market/tickers"
            params = {
                'category': 'spot',
                'symbol': symbol
            }

            response = self.session.get(url, params=params)
            data = response.json()

            return data['retCode'] == 0 and len(data['result']['list']) > 0
        except Exception as e:
            print(f"Ошибка при проверке символа: {e}")
            return False

    def _format_symbol(self, symbol):
        """
        Форматирует символ для Bybit API
        """
        symbol = symbol.upper().replace('-', '')
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        return symbol

    def get_crypto_name(self, symbol):
        """
        Получает название криптовалюты по символу
        """
        formatted_symbol = self._format_symbol(symbol)

        if formatted_symbol in self.popular_cryptos:
            return self.popular_cryptos[formatted_symbol]

        # Для Bybit мы используем заранее заданные названия
        # В реальном приложении можно было бы использовать информацию о паре
        base_currency = formatted_symbol.replace('USDT', '')
        return f"{base_currency} (Bybit)"

    def get_kline_data(self, symbol, interval, limit=200):
        """
        Получает исторические данные (K-line) с Bybit
        """
        try:
            symbol = self._format_symbol(symbol)
            url = f"{self.base_url}/v5/market/kline"
            params = {
                'category': 'spot',
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }

            response = self.session.get(url, params=params)
            data = response.json()

            if data['retCode'] == 0:
                klines = data['result']['list']

                # Конвертируем в DataFrame
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
                ])

                # Конвертируем типы данных
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)

                df = df.sort_values('timestamp').reset_index(drop=True)
                return df
            else:
                print(f"Ошибка Bybit API: {data['retMsg']}")
                return None

        except Exception as e:
            print(f"Ошибка при получении данных K-line: {e}")
            return None

    def get_current_price(self, crypto_symbol):
        """
        Получает текущую цену криптовалюты с Bybit
        """
        try:
            symbol = self._format_symbol(crypto_symbol)
            url = f"{self.base_url}/v5/market/tickers"
            params = {
                'category': 'spot',
                'symbol': symbol
            }

            response = self.session.get(url, params=params)
            data = response.json()

            if data['retCode'] == 0 and len(data['result']['list']) > 0:
                ticker = data['result']['list'][0]
                current_price = float(ticker['lastPrice'])
                timestamp = datetime.now()

                return current_price, timestamp, None
            else:
                return None, None, f"Ошибка API: {data.get('retMsg', 'Неизвестная ошибка')}"

        except Exception as e:
            return None, None, f"Ошибка при получении текущей цены: {str(e)}"

    def create_current_candle(self, crypto_symbol, timeframe_key):
        """
        Создает закрытую свечу на текущий момент используя данные Bybit
        """
        try:
            if timeframe_key not in self.timeframes:
                return None, "Неверный таймфрейм"

            timeframe = self.timeframes[timeframe_key]
            symbol = self._format_symbol(crypto_symbol)

            print(f"🔄 Получение актуальных данных для {symbol}...")

            # Получаем исторические данные
            hist = self.get_kline_data(symbol, timeframe['interval'], timeframe['limit'])

            if hist is None or hist.empty:
                return None, "Не удалось получить исторические данные"

            # Получаем текущую цену
            current_price, current_timestamp, error = self.get_current_price(crypto_symbol)
            if error:
                return None, error

            # Форматируем исторические данные
            hist['Timestamp'] = hist['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Создаем текущую свечу
            current_candle = {
                'Timestamp': current_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Open': current_price,
                'High': current_price,
                'Low': current_price,
                'Close': current_price,
                'Volume': 0,
                'Type': 'ТЕКУЩАЯ ЦЕНА'
            }

            # Добавляем текущую цену как отдельную строку
            current_df = pd.DataFrame([current_candle])

            # Форматируем исторические данные
            available_columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            hist_data = hist[available_columns]
            hist_data['Type'] = 'ИСТОРИЧЕСКАЯ'

            # Объединяем исторические данные с текущей ценой
            result_data = pd.concat([hist_data, current_df], ignore_index=True)

            # Ограничиваем количество свечей для удобства просмотра
            max_candles = timeframe['max_candles']
            if len(result_data) > max_candles:
                result_data = result_data.tail(max_candles)

            return result_data, None

        except Exception as e:
            return None, f"Ошибка при создании свечи: {str(e)}"

    def get_crypto_data_with_current(self, crypto_symbol, timeframe_key):
        """
        Получает данные с актуальной ценой на момент запроса с Bybit
        """
        try:
            if timeframe_key not in self.timeframes:
                return None, "Неверный таймфрейм"

            timeframe = self.timeframes[timeframe_key]
            symbol = self._format_symbol(crypto_symbol)

            print(f"🔄 Получение данных для {symbol}...")

            # Получаем исторические данные
            hist = self.get_kline_data(symbol, timeframe['interval'], timeframe['limit'])

            if hist is None or hist.empty:
                return None, "Не удалось получить данные"

            # Получаем текущую цену
            current_price, current_timestamp, error = self.get_current_price(crypto_symbol)
            if error:
                print(f"⚠️ Не удалось получить текущую цену: {error}")
                current_price = hist['close'].iloc[-1]
                current_timestamp = datetime.now()

            # Форматируем исторические данные
            hist['Timestamp'] = hist['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Обновляем последнюю свечу актуальной ценой
            hist.loc[hist.index[-1], 'close'] = current_price
            hist.loc[hist.index[-1], 'high'] = max(hist.loc[hist.index[-1], 'high'], current_price)
            hist.loc[hist.index[-1], 'low'] = min(hist.loc[hist.index[-1], 'low'], current_price)
            hist.loc[hist.index[-1], 'Timestamp'] = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')

            # Переименовываем колонки для совместимости
            result_data = hist.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]

            # Ограничиваем количество свечей для удобства просмотра
            max_candles = timeframe['max_candles']
            if len(result_data) > max_candles:
                result_data = result_data.tail(max_candles)

            return result_data, None

        except Exception as e:
            return None, f"Ошибка: {str(e)}"

    def display_data(self, data, crypto_name, timeframe_name):
        """
        Отображает данные в удобном формате
        """
        if data is None or data.empty:
            print("Нет данных для отображения")
            return

        print(f"\n{'=' * 90}")
        print(f"📊 ДАННЫЕ ПО КРИПТОВАЛЮТЕ: {crypto_name}")
        print(f"⏰ Таймфрейм: {timeframe_name}")
        print(f"🕐 Актуально на: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Период: с {data['Timestamp'].iloc[0]} по {data['Timestamp'].iloc[-1]}")
        print(f"📈 Количество свечей: {len(data)}")
        print(f"🔗 Источник: Bybit API")
        print(f"{'=' * 90}")

        # Форматируем вывод чисел в зависимости от цены
        sample_price = data['Close'].iloc[0]
        if sample_price < 0.001:
            price_format = "{:.8f}"
        elif sample_price < 1:
            price_format = "{:.6f}"
        elif sample_price < 1000:
            price_format = "{:.4f}"
        else:
            price_format = "{:.2f}"

        # Создаем копию данных для красивого отображения
        display_df = data.copy()
        display_df['Open'] = display_df['Open'].apply(lambda x: f"${price_format.format(x)}")
        display_df['High'] = display_df['High'].apply(lambda x: f"${price_format.format(x)}")
        display_df['Low'] = display_df['Low'].apply(lambda x: f"${price_format.format(x)}")
        display_df['Close'] = display_df['Close'].apply(lambda x: f"${price_format.format(x)}")

        if 'Volume' in display_df.columns:
            display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}")

        # Выделяем последнюю (актуальную) свечу
        print("📋 Исторические свечи:")
        if len(display_df) > 1:
            print(display_df.iloc[:-1].tail(10).to_string(index=False))

        print(f"\n🎯 АКТУАЛЬНАЯ ЦЕНА (последняя закрытая свеча):")
        print("─" * 80)
        print(display_df.iloc[-1:].to_string(index=False))
        print("─" * 80)

        # Статистика
        self.show_statistics(data)

    def show_statistics(self, data):
        """
        Показывает статистику по данным
        """
        print(f"\n{'─' * 60}")
        print("📊 СТАТИСТИКА:")
        print(f"{'─' * 60}")
        print(f"Текущая цена: ${data['Close'].iloc[-1]:.6f}")
        print(f"Цена открытия: ${data['Open'].iloc[-1]:.6f}")
        print(f"Максимум свечи: ${data['High'].iloc[-1]:.6f}")
        print(f"Минимум свечи: ${data['Low'].iloc[-1]:.6f}")

        if 'Volume' in data.columns and data['Volume'].iloc[-1] > 0:
            print(f"Объем: {data['Volume'].iloc[-1]:,.0f}")

        # Изменение в текущей свече
        change = data['Close'].iloc[-1] - data['Open'].iloc[-1]
        change_percent = (change / data['Open'].iloc[-1]) * 100

        trend = "🟢 📈 РОСТ" if change >= 0 else "🔴 📉 ПАДЕНИЕ"
        print(f"Изменение в текущей свече: {trend} {change:+.6f} ({change_percent:+.2f}%)")

        # Общая статистика
        print(f"\n📈 Общая статистика за период:")
        print(f"Максимальный High: ${data['High'].max():.6f}")
        print(f"Минимальный Low: ${data['Low'].min():.6f}")
        print(f"Средняя цена: ${data['Close'].mean():.6f}")

    def show_popular_cryptos(self):
        """
        Показывает список популярных криптовалют
        """
        print(f"\n{'🎯 ПОПУЛЯРНЫЕ КРИПТОВАЛЮТЫ':^60}")
        print(f"{'─' * 60}")
        crypto_list = list(self.popular_cryptos.items())

        for i in range(0, len(crypto_list), 3):
            line = ""
            for j in range(3):
                if i + j < len(crypto_list):
                    symbol, name = crypto_list[i + j]
                    line += f"{symbol:12} - {name:15}  "
            print(line)
        print(f"{'─' * 60}")
        print("💡 Вы можете ввести ЛЮБОЙ код криптовалюты (например: BTC, ETH, ADA)")

    def show_timeframes(self):
        """
        Показывает доступные таймфреймы
        """
        print(f"\n{'⏰ ДОСТУПНЫЕ ТАЙМФРЕЙМЫ':^60}")
        print(f"{'─' * 60}")
        for key, tf in self.timeframes.items():
            print(f"{key}. {tf['name']:20} (макс. {tf['max_candles']} свечей)")
        print(f"{'─' * 60}")

    def export_to_csv(self, data, crypto_symbol, timeframe_key):
        """
        Экспортирует данные в CSV файл
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{crypto_symbol}_{self.timeframes[timeframe_key]['name'].replace(' ', '_')}_{timestamp}.csv"
            data.to_csv(filename, index=False)
            print(f"💾 Данные сохранены в файл: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Ошибка при сохранении файла: {e}")
            return None


def main():
    """
    Основная функция программы
    """
    fetcher = CryptoDataFetcher()

    print("🚀 КРИПТОВАЛЮТНЫЙ АНАЛИЗАТОР (Bybit API)")
    print("📊 Получение актуальных данных с закрытой свечой на момент запроса")
    print("🔗 Источник данных: Bybit Exchange")
    print("✨ Теперь можно использовать ЛЮБЫЕ криптовалюты!")

    while True:
        print("\n" + "=" * 70)
        print("1. Получить данные по криптовалюте (с актуальной ценой)")
        print("2. Проверить доступность криптовалюты")
        print("3. Показать популярные криптовалюты")
        print("4. Показать таймфреймы")
        print("5. Получить только текущую цену")
        print("6. Выход")

        choice = input("\nВыберите действие (1-6): ").strip()

        if choice == '1':
            fetcher.show_popular_cryptos()
            crypto_choice = input("\n💰 Введите код криптовалюты: ").strip().upper()

            if not crypto_choice:
                print("❌ Пожалуйста, введите код криптовалюты")
                continue

            print(f"🔍 Проверка доступности {crypto_choice}...")
            if not fetcher.validate_crypto_symbol(crypto_choice):
                print(f"❌ Криптовалюта {crypto_choice} не найдена на Bybit")
                continue

            fetcher.show_timeframes()
            tf_choice = input("\nВыберите таймфрейм (1-7): ").strip()

            if tf_choice not in fetcher.timeframes:
                print("❌ Неверный таймфрейм")
                continue

            crypto_name = fetcher.get_crypto_name(crypto_choice)
            data, error = fetcher.get_crypto_data_with_current(crypto_choice, tf_choice)

            if error:
                print(f"❌ {error}")
            else:
                timeframe_name = fetcher.timeframes[tf_choice]['name']
                fetcher.display_data(data, crypto_name, timeframe_name)

                export_choice = input("\n💾 Экспортировать данные в CSV? (y/n): ").strip().lower()
                if export_choice in ['y', 'yes', 'д', 'да']:
                    fetcher.export_to_csv(data, crypto_choice, tf_choice)

        elif choice == '2':
            crypto_to_check = input("\n🔍 Введите код криптовалюты для проверки: ").strip().upper()
            if fetcher.validate_crypto_symbol(crypto_to_check):
                crypto_name = fetcher.get_crypto_name(crypto_to_check)
                print(f"✅ {crypto_to_check} ({crypto_name}) - доступна на Bybit")
            else:
                print(f"❌ {crypto_to_check} - недоступна на Bybit")

        elif choice == '3':
            fetcher.show_popular_cryptos()

        elif choice == '4':
            fetcher.show_timeframes()

        elif choice == '5':
            crypto_choice = input("\n💰 Введите код криптовалюты для получения текущей цены: ").strip().upper()
            if not crypto_choice:
                print("❌ Пожалуйста, введите код криптовалюты")
                continue

            if not fetcher.validate_crypto_symbol(crypto_choice):
                print(f"❌ Криптовалюта {crypto_choice} не найдена на Bybit")
                continue

            current_price, timestamp, error = fetcher.get_current_price(crypto_choice)
            if error:
                print(f"❌ {error}")
            else:
                crypto_name = fetcher.get_crypto_name(crypto_choice)
                print(f"\n🎯 ТЕКУЩАЯ ЦЕНА {crypto_name} ({crypto_choice}):")
                print(f"💰 ${current_price:.6f}")
                print(f"🕐 Время: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"🔗 Источник: Bybit")

        elif choice == '6':
            print("👋 До свидания!")
            break

        else:
            print("❌ Неверный выбор. Пожалуйста, выберите 1-6")


# Функции для быстрого использования
def get_current_crypto_price(symbol):
    """
    Быстрое получение текущей цены криптовалюты
    """
    fetcher = CryptoDataFetcher()

    if not fetcher.validate_crypto_symbol(symbol):
        print(f"❌ Криптовалюта {symbol} не найдена на Bybit")
        return None

    current_price, timestamp, error = fetcher.get_current_price(symbol)
    if error:
        print(f"Ошибка: {error}")
        return None

    crypto_name = fetcher.get_crypto_name(symbol)
    print(f"🎯 {crypto_name} ({symbol}): ${current_price:.6f} на {timestamp.strftime('%H:%M:%S')} (Bybit)")
    return current_price


def quick_crypto_chart(symbol, timeframe='5'):
    """
    Быстрое получение данных с актуальной ценой
    """
    fetcher = CryptoDataFetcher()

    if not fetcher.validate_crypto_symbol(symbol):
        print(f"❌ Криптовалюта {symbol} не найдена на Bybit")
        return None

    data, error = fetcher.get_crypto_data_with_current(symbol, timeframe)

    if error:
        print(f"Ошибка: {error}")
        return None

    crypto_name = fetcher.get_crypto_name(symbol)
    timeframe_name = fetcher.timeframes[timeframe]['name']

    print(f"\n📊 {crypto_name} ({symbol}) - {timeframe_name} (Bybit)")
    print(f"💰 Актуальная цена: ${data['Close'].iloc[-1]:.6f}")
    print(f"📅 Последние 3 свечи:")
    print(data.tail(3).to_string(index=False))

    return data


if __name__ == "__main__":
    main()

    # Примеры быстрого использования:
    # get_current_crypto_price('BTC')      # Текущая цена Bitcoin
    # quick_crypto_chart('ETH', '4')       # Данные Ethereum с часовым таймфреймом