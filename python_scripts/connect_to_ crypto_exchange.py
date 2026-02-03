import os
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Загружаем переменные окружения
load_dotenv()


class UniversalChaseProfit:
    def __init__(self):
        self.exchanges = {}
        self.setup_exchanges()

    def setup_exchanges(self):
        """
        Настройка подключения ко всем биржам
        """
        exchange_configs = {
            'bybit': {
                'api_key': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
                'sandbox': os.getenv('BYBIT_TESTNET', 'True').lower() == 'true'
            },
            'binance': {
                'api_key': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_API_SECRET'),
                'sandbox': False
            },
            'okx': {
                'api_key': os.getenv('OKX_API_KEY'),
                'secret': os.getenv('OKX_API_SECRET'),
                'password': os.getenv('OKX_PASSWORD'),
                'sandbox': False
            },
            'kucoin': {
                'api_key': os.getenv('KUCOIN_API_KEY'),
                'secret': os.getenv('KUCOIN_API_SECRET'),
                'password': os.getenv('KUCOIN_PASSWORD'),
                'sandbox': False
            },
            'huobi': {
                'api_key': os.getenv('HUOBI_API_KEY'),
                'secret': os.getenv('HUOBI_API_SECRET'),
                'sandbox': False
            },
            'gateio': {
                'api_key': os.getenv('GATEIO_API_KEY'),
                'secret': os.getenv('GATEIO_API_SECRET'),
                'sandbox': False
            },
            'mexc': {
                'api_key': os.getenv('MEXC_API_KEY'),
                'secret': os.getenv('MEXC_API_SECRET'),
                'sandbox': False
            }
        }

        for exchange_name, config in exchange_configs.items():
            if config['api_key'] and config['secret']:
                try:
                    exchange_class = getattr(ccxt, exchange_name)
                    exchange_config = {
                        'apiKey': config['api_key'],
                        'secret': config['secret'],
                        'sandbox': config.get('sandbox', False),
                        'enableRateLimit': True
                    }

                    # Специфичные настройки для некоторых бирж
                    if exchange_name == 'okx' and config.get('password'):
                        exchange_config['password'] = config['password']
                    if exchange_name == 'kucoin' and config.get('password'):
                        exchange_config['password'] = config['password']

                    self.exchanges[exchange_name] = exchange_class(exchange_config)
                    print(f"✅ {exchange_name.upper()} подключен")

                except Exception as e:
                    print(f"❌ Ошибка подключения к {exchange_name}: {e}")
            else:
                print(f"⚠️  Пропущена {exchange_name} - нет API ключей")

    def get_closed_trades(self, exchange_name: str, symbol: str = None, since: int = None, limit: int = 100) -> List[
        Dict]:
        """
        Получить закрытые сделки
        """
        try:
            exchange = self.exchanges[exchange_name]

            if exchange.has['fetchMyTrades']:
                params = {'limit': limit}
                if since:
                    params['since'] = since

                trades = exchange.fetch_my_trades(symbol, since, limit, params)
                return trades
            else:
                print(f"❌ {exchange_name} не поддерживает fetchMyTrades")
                return []

        except Exception as e:
            print(f"❌ Ошибка получения сделок на {exchange_name}: {e}")
            return []

    def get_open_positions(self, exchange_name: str, symbol: str = None) -> List[Dict]:
        """
        Получить открытые позиции
        """
        try:
            exchange = self.exchanges[exchange_name]

            if exchange.has['fetchPositions']:
                positions = exchange.fetch_positions(symbols=[symbol] if symbol else None)
                # Фильтруем только позиции с ненулевым размером
                open_positions = [pos for pos in positions if pos.get('contracts', 0) > 0 or pos.get('size', 0) > 0]
                return open_positions
            else:
                print(f"❌ {exchange_name} не поддерживает fetchPositions")
                return []

        except Exception as e:
            print(f"❌ Ошибка получения позиций на {exchange_name}: {e}")
            return []

    def get_open_orders(self, exchange_name: str, symbol: str = None) -> List[Dict]:
        """
        Получить активные ордера
        """
        try:
            exchange = self.exchanges[exchange_name]

            if exchange.has['fetchOpenOrders']:
                orders = exchange.fetch_open_orders(symbol)
                return orders
            else:
                print(f"❌ {exchange_name} не поддерживает fetchOpenOrders")
                return []

        except Exception as e:
            print(f"❌ Ошибка получения ордеров на {exchange_name}: {e}")
            return []

    def get_balance(self, exchange_name: str) -> Dict:
        """
        Получить баланс
        """
        try:
            exchange = self.exchanges[exchange_name]
            balance = exchange.fetch_balance()
            return balance
        except Exception as e:
            print(f"❌ Ошибка получения баланса на {exchange_name}: {e}")
            return {}

    def get_all_trading_data(self, exchange_name: str, symbol: str = None, days: int = 30) -> Dict:
        """
        Получить все торговые данные с биржи
        """
        print(f"\n📊 Получение данных с {exchange_name.upper()}...")

        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        closed_trades = self.get_closed_trades(exchange_name, symbol, since, 500)
        open_positions = self.get_open_positions(exchange_name, symbol)
        open_orders = self.get_open_orders(exchange_name, symbol)
        balance = self.get_balance(exchange_name)

        return {
            'exchange': exchange_name,
            'closed_trades': closed_trades,
            'open_positions': open_positions,
            'open_orders': open_orders,
            'balance': balance,
            'timestamp': datetime.now().isoformat()
        }

    def format_trades_dataframe(self, data: Dict) -> pd.DataFrame:
        """
        Форматирование сделок в DataFrame
        """
        trades = data['closed_trades']
        if not trades:
            return pd.DataFrame()

        df_data = []
        for trade in trades:
            df_data.append({
                'exchange': data['exchange'],
                'symbol': trade.get('symbol', ''),
                'side': trade.get('side', ''),
                'amount': trade.get('amount', 0),
                'price': trade.get('price', 0),
                'cost': trade.get('cost', 0),
                'fee': trade.get('fee', {}).get('cost', 0) if trade.get('fee') else 0,
                'fee_currency': trade.get('fee', {}).get('currency', '') if trade.get('fee') else '',
                'datetime': trade.get('datetime', ''),
                'timestamp': trade.get('timestamp', 0)
            })

        return pd.DataFrame(df_data)

    def format_positions_dataframe(self, data: Dict) -> pd.DataFrame:
        """
        Форматирование позиций в DataFrame
        """
        positions = data['open_positions']
        if not positions:
            return pd.DataFrame()

        df_data = []
        for position in positions:
            df_data.append({
                'exchange': data['exchange'],
                'symbol': position.get('symbol', ''),
                'side': position.get('side', ''),
                'contracts': position.get('contracts', 0),
                'contract_size': position.get('contractSize', 0),
                'entry_price': position.get('entryPrice', 0),
                'mark_price': position.get('markPrice', 0),
                'notional': position.get('notional', 0),
                'leverage': position.get('leverage', 1),
                'unrealized_pnl': position.get('unrealizedPnl', 0),
                'liquidation_price': position.get('liquidationPrice', 0)
            })

        return pd.DataFrame(df_data)

    def calculate_exchange_statistics(self, data: Dict) -> Dict:
        """
        Расчет статистики по бирже
        """
        trades = data['closed_trades']
        positions = data['open_positions']

        stats = {
            'exchange': data['exchange'],
            'total_trades': len(trades),
            'open_positions': len(positions),
            'open_orders': len(data['open_orders']),
            'total_pnl': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }

        if trades:
            # Для расчета PnL нужно учитывать специфику каждой биржи
            winning_trades = 0
            for trade in trades:
                # Простой расчет PnL на основе цены и комиссий
                if trade.get('cost') and trade.get('fee'):
                    fee_cost = trade['fee']['cost'] if isinstance(trade['fee'], dict) else trade['fee']
                    stats['total_pnl'] += trade.get('cost', 0) - fee_cost

                    if trade.get('side') == 'buy':
                        winning_trades += 1

            stats['winning_trades'] = winning_trades
            stats['losing_trades'] = len(trades) - winning_trades
            stats['win_rate'] = (winning_trades / len(trades)) * 100 if trades else 0

        return stats

    def generate_report(self, all_data: Dict):
        """
        Генерация общего отчета
        """
        print("\n" + "=" * 80)
        print("📈 ОБЩИЙ ОТЧЕТ ПО ВСЕМ БИРЖАМ")
        print("=" * 80)

        total_stats = {
            'total_trades': 0,
            'total_open_positions': 0,
            'total_open_orders': 0,
            'total_pnl': 0
        }

        for exchange_name, data in all_data.items():
            stats = self.calculate_exchange_statistics(data)

            print(f"\n🏦 {exchange_name.upper()}:")
            print(f"   Закрытых сделок: {stats['total_trades']}")
            print(f"   Открытых позиций: {stats['open_positions']}")
            print(f"   Активных ордеров: {stats['open_orders']}")
            print(f"   Винрейт: {stats.get('win_rate', 0):.1f}%")
            print(f"   Прибыль: ${stats['total_pnl']:.2f}")

            # Суммируем общую статистику
            total_stats['total_trades'] += stats['total_trades']
            total_stats['total_open_positions'] += stats['open_positions']
            total_stats['total_open_orders'] += stats['open_orders']
            total_stats['total_pnl'] += stats['total_pnl']

        print(f"\n🎯 ИТОГО:")
        print(f"   Всего сделок: {total_stats['total_trades']}")
        print(f"   Всего позиций: {total_stats['total_open_positions']}")
        print(f"   Всего ордеров: {total_stats['total_open_orders']}")
        print(f"   Общая прибыль: ${total_stats['total_pnl']:.2f}")

    def save_combined_data(self, all_data: Dict, filename: str = None):
        """
        Сохранение всех данных в файл
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_exchanges_data_{timestamp}.json"

        # Конвертируем данные в JSON-совместимый формат
        json_data = {}
        for exchange, data in all_data.items():
            json_data[exchange] = data

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 Все данные сохранены в файл: {filename}")

    def export_to_excel(self, all_data: Dict, filename: str = None):
        """
        Экспорт данных в Excel
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_exchanges_report_{timestamp}.xlsx"

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Лист со сделками
            trades_dfs = []
            for exchange, data in all_data.items():
                df = self.format_trades_dataframe(data)
                if not df.empty:
                    trades_dfs.append(df)

            if trades_dfs:
                all_trades_df = pd.concat(trades_dfs, ignore_index=True)
                all_trades_df.to_excel(writer, sheet_name='Все сделки', index=False)

            # Лист с позициями
            positions_dfs = []
            for exchange, data in all_data.items():
                df = self.format_positions_dataframe(data)
                if not df.empty:
                    positions_dfs.append(df)

            if positions_dfs:
                all_positions_df = pd.concat(positions_dfs, ignore_index=True)
                all_positions_df.to_excel(writer, sheet_name='Открытые позиции', index=False)

            # Лист со статистикой
            stats_data = []
            for exchange, data in all_data.items():
                stats = self.calculate_exchange_statistics(data)
                stats_data.append(stats)

            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Статистика', index=False)

        print(f"📊 Данные экспортированы в Excel: {filename}")


def main():
    """
    Основная функция
    """
    try:
        # Инициализация универсального клиента
        client = UniversalChaseProfit()

        if not client.exchanges:
            print("❌ Не подключено ни одной биржи. Проверьте API ключи в .env файле")
            return

        print(f"\n✅ Успешно подключено бирж: {len(client.exchanges)}")

        # Получение данных со всех бирж
        all_data = {}
        for exchange_name in client.exchanges.keys():
            try:
                data = client.get_all_trading_data(exchange_name, days=30)
                all_data[exchange_name] = data
            except Exception as e:
                print(f"❌ Ошибка при получении данных с {exchange_name}: {e}")

        # Генерация отчета
        client.generate_report(all_data)

        # Сохранение данных
        client.save_combined_data(all_data)
        client.export_to_excel(all_data)

        print(f"\n🎉 Скрипт успешно завершен! Обработано бирж: {len(all_data)}")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()

# Bybit
BYBIT_API_KEY = your_bybit_api_key
BYBIT_API_SECRET = your_bybit_api_secret
BYBIT_TESTNET = True

# Binance
BINANCE_API_KEY = your_binance_api_key
BINANCE_API_SECRET = your_binance_api_secret

# OKX
OKX_API_KEY = your_okx_api_key
OKX_API_SECRET = your_okx_api_secret
OKX_PASSWORD = your_okx_password

# KuCoin
KUCOIN_API_KEY = your_kucoin_api_key
KUCOIN_API_SECRET = your_kucoin_api_secret
KUCOIN_PASSWORD = your_kucoin_password

# Huobi
HUOBI_API_KEY = your_huobi_api_key
HUOBI_API_SECRET = your_huobi_api_secret

# Gate.io
GATEIO_API_KEY = your_gateio_api_key
GATEIO_API_SECRET = your_gateio_api_secret

# MEXC
MEXC_API_KEY = your_mexc_api_key
MEXC_API_SECRET = your_mexc_api_secret
```

Дополнительные
утилиты

Скрипт
для
мониторинга
в
реальном
времени:

```python


def real_time_monitor(self, exchange_names: List[str], symbols: List[str] = None):
    """
    Мониторинг в реальном времени
    """
    import time

    while True:
        print(f"\n🔄 Обновление данных... {datetime.now().strftime('%H:%M:%S')}")

        for exchange_name in exchange_names:
            if exchange_name in self.exchanges:
                try:
                    data = self.get_all_trading_data(exchange_name, days=1)

                    print(f"\n{exchange_name.upper()}:")
                    print(f"  Позиций: {len(data['open_positions'])}")
                    print(f"  Ордеров: {len(data['open_orders'])}")

                    # Проверка важных событий
                    if data['open_positions']:
                        for pos in data['open_positions']:
                            unrealized_pnl = pos.get('unrealizedPnl', 0)
                            if abs(unrealized_pnl) > 100:  # Большие PnL
                                print(f"  ⚠️  Большой PnL: {pos['symbol']} - ${unrealized_pnl:.2f}")

                except Exception as e:
                    print(f"❌ Ошибка {exchange_name}: {e}")

        time.sleep(60)  # Обновление каждую минуту


# ```
#
# Скрипт
# для
# алертов:
#
# ```python


def setup_alerts(self, conditions: Dict):
    """
    Настройка алертов
    """
    # conditions example:
    # {'max_drawdown': -100, 'min_win_rate': 60, 'position_size_limit': 1000}
    pass


# ```
#
# Особенности
# работы
# с
# разными
# биржами:
#
# 1.
# Bybit - лучшая
# поддержка
# фьючерсов
# 2.
# Binance - самая
# ликвидная, много
# пар
# 3.
# OKX - хорошие
# API
# лимиты
# 4.
# KuCoin - много
# альткойнов
# 5.
# Huobi - сильна
# в
# Азии
# 6.
# Gate.io - быстрая
# поддержка
# новых
# монет
# 7.
# MEXC - эксклюзивные
# листинги
#
# Запуск:
#
# ```bash
# python
# universal_crypto_tracker.py
# ```
#
# Скрипт
# автоматически:
#
# · ✅ Подключится
# ко
# всем
# настроенным
# биржам
# · ✅ Соберет
# данные
# о
# сделках, позициях
# и
# ордерах
# · ✅ Сгенерирует
# детальный
# отчет
# · ✅ Сохранит
# данные
# в
# JSON
# и
# Excel
# · ✅ Покажет
# общую
# статистику
# по
# всем
# счетам