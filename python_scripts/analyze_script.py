
#!/usr/bin/env python3
import sys
import subprocess

# === АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ===
def install_dependencies():
    """Устанавливает необходимые пакеты если они отсутствуют"""
    deps = ['pandas', 'numpy', 'requests', 'ta']

    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            print(f"Установка {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

# Проверяем аргументы командной строки
if "--no-auto-install" not in sys.argv:
    install_dependencies()
else:
    sys.argv.remove("--no-auto-install")

# === ИМПОРТ БИБЛИОТЕК ===
import pandas as pd
import numpy as np
import requests
import ta
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# ... остальной ваш код без изменений ...
# ... остальной ваш код без изменений ...

class CryptoDataFetcher:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.session = requests.Session()

        # Bybit поддерживаемые интервалы: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, M, W
        self.timeframes = {
            '1': {'interval': '1', 'name': '1 минута', 'max_candles': 200, 'limit': 200},
            '5': {'interval': '5', 'name': '5 минут', 'max_candles': 200, 'limit': 200},
            '15': {'interval': '15', 'name': '15 минут', 'max_candles': 200, 'limit': 200},
            '60': {'interval': '60', 'name': '1 час', 'max_candles': 200, 'limit': 200},
            'D': {'interval': 'D', 'name': '1 день', 'max_candles': 200, 'limit': 200},
            'W': {'interval': 'W', 'name': '1 неделя', 'max_candles': 100, 'limit': 100},
            'M': {'interval': 'M', 'name': '1 месяц', 'max_candles': 50, 'limit': 50}
        }

    def _format_symbol(self, symbol):
        """Форматирует символ для Bybit API"""
        symbol = symbol.upper().replace('-', '')
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        return symbol

    def validate_crypto_symbol(self, symbol):
        """Проверяет существование криптовалюты на Bybit"""
        try:
            symbol = self._format_symbol(symbol)
            url = f"{self.base_url}/v5/market/tickers"
            params = {'category': 'spot', 'symbol': symbol}
            response = self.session.get(url, params=params)
            data = response.json()
            return data['retCode'] == 0 and len(data['result']['list']) > 0
        except:
            return False

    def get_kline_data(self, symbol, interval, limit=200):
        """Получает исторические данные (K-line) с Bybit"""
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
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
                ])

                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)

                df = df.sort_values('timestamp').reset_index(drop=True)
                return df
        except Exception as e:
            sys.stderr.write(f"Error getting kline data: {str(e)}\n")
        return None

    def get_current_price(self, crypto_symbol):
        """Получает текущую цену криптовалюты"""
        try:
            symbol = self._format_symbol(crypto_symbol)
            url = f"{self.base_url}/v5/market/tickers"
            params = {'category': 'spot', 'symbol': symbol}

            response = self.session.get(url, params=params)
            data = response.json()

            if data['retCode'] == 0 and len(data['result']['list']) > 0:
                ticker = data['result']['list'][0]
                current_price = float(ticker['lastPrice'])
                return current_price, datetime.now(), None
        except Exception as e:
            return None, None, str(e)
        return None, None, "Unknown error"

    def get_crypto_data_with_current(self, crypto_symbol, timeframe_key):
        """Получает данные с актуальной ценой"""
        if timeframe_key not in self.timeframes:
            return None, f"Invalid timeframe: {timeframe_key}"

        timeframe = self.timeframes[timeframe_key]
        symbol = self._format_symbol(crypto_symbol)

        # Получаем исторические данные
        hist = self.get_kline_data(symbol, timeframe['interval'], timeframe['limit'])
        if hist is None or hist.empty:
            return None, "Failed to get historical data"

        # Получаем текущую цену
        current_price, current_timestamp, error = self.get_current_price(crypto_symbol)
        if error:
            current_price = hist['close'].iloc[-1]
            current_timestamp = datetime.now()

        # Форматируем и обновляем данные
        hist['Timestamp'] = hist['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Обновляем последнюю свечу актуальной ценой
        if len(hist) > 0:
            hist.loc[hist.index[-1], 'close'] = current_price
            hist.loc[hist.index[-1], 'high'] = max(hist.loc[hist.index[-1], 'high'], current_price)
            hist.loc[hist.index[-1], 'low'] = min(hist.loc[hist.index[-1], 'low'], current_price)
            hist.loc[hist.index[-1], 'Timestamp'] = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # Переименовываем колонки
        result_data = hist.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Ограничиваем количество свечей
        max_candles = timeframe['max_candles']
        if len(result_data) > max_candles:
            result_data = result_data.tail(max_candles)

        return result_data, None


class TradingStrategyAnalyzer:
    def __init__(self, data_frame):
        self.data = data_frame
        self.strategies = {
            'RSI_MACD': {'name': 'RSI + MACD', 'function': self.rsi_macd_strategy},
            'MA': {'name': 'Скользящие средние', 'function': self.moving_averages_strategy},
            'BB': {'name': 'Bollinger Bands', 'function': self.bollinger_bands_strategy},
            'STOCH_EMA': {'name': 'Stochastic + EMA', 'function': self.stochastic_ema_strategy},
            'SAR_ADX': {'name': 'Parabolic SAR + ADX', 'function': self.parabolic_sar_strategy},
            'BREAKOUT': {'name': 'Пробой уровня', 'function': self.breakout_strategy}
        }

    def prepare_data(self):
        """Подготовка данных для анализа"""
        try:
            required_columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in self.data.columns:
                    return False

            self.data = self.data.sort_values('Timestamp').reset_index(drop=True)
            return True
        except Exception as e:
            sys.stderr.write(f"Error preparing data: {str(e)}\n")
            return False

    def calculate_technical_indicators(self):
        """Расчет всех технических индикаторов"""
        df = self.data.copy()

        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()

        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()

        # Скользящие средние
        df['sma_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
        df['sma_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()
        df['ema_12'] = ta.trend.EMAIndicator(df['Close'], window=12).ema_indicator()
        df['ema_26'] = ta.trend.EMAIndicator(df['Close'], window=26).ema_indicator()

        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_lower'] = bollinger.bollinger_lband()
        df['bb_middle'] = bollinger.bollinger_mavg()

        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()

        # Parabolic SAR
        df['parabolic_sar'] = ta.trend.PSARIndicator(df['High'], df['Low'], df['Close']).psar()

        # ADX
        df['adx'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()

        # ATR
        df['atr'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()

        # Уровни поддержки и сопротивления
        df = self.calculate_support_resistance(df)

        self.data = df

    def calculate_support_resistance(self, df, window=20):
        """Расчет уровней поддержки и сопротивления"""
        if len(df) == 0:
            return df

        # Локальные максимумы и минимумы
        df['resistance'] = df['High'].rolling(window=window, center=True).max()
        df['support'] = df['Low'].rolling(window=window, center=True).min()

        # Ближайшие уровни
        current_high = df['High'].iloc[-1]
        current_low = df['Low'].iloc[-1]

        resistance_levels = df['resistance'].unique()
        resistance_levels = sorted([r for r in resistance_levels if r > current_high and not np.isnan(r)])

        support_levels = df['support'].unique()
        support_levels = sorted([s for s in support_levels if s < current_low and not np.isnan(s)], reverse=True)

        df['nearest_resistance'] = resistance_levels[0] if resistance_levels else np.nan
        df['nearest_support'] = support_levels[0] if support_levels else np.nan

        return df

    def detect_breakout(self, df, lookback_period=10):
        """Обнаружение пробоев уровней"""
        if len(df) == 0:
            return False, False, 0, 0

        current = df.iloc[-1]
        current_close = current['Close']
        current_high = current['High']
        current_low = current['Low']

        recent_data = df.tail(min(lookback_period, len(df)))
        consolidation_high = recent_data['High'].max()
        consolidation_low = recent_data['Low'].min()

        # Проверяем пробой сопротивления
        resistance_break = False
        if not np.isnan(current['nearest_resistance']):
            if (current_close > current['nearest_resistance'] and
                    current_high > consolidation_high and
                    'Volume' in current and current['Volume'] > recent_data['Volume'].mean()):
                resistance_break = True

        # Проверяем пробой поддержки
        support_break = False
        if not np.isnan(current['nearest_support']):
            if (current_close < current['nearest_support'] and
                    current_low < consolidation_low and
                    'Volume' in current and current['Volume'] > recent_data['Volume'].mean()):
                support_break = True

        return resistance_break, support_break, consolidation_high, consolidation_low

    def breakout_strategy(self):
        """Стратегия пробоя уровней"""
        if len(self.data) == 0:
            return self._empty_result("BREAKOUT")

        current = self.data.iloc[-1]
        current_price = current['Close']

        resistance_break, support_break, consolidation_high, consolidation_low = self.detect_breakout(self.data)

        # Определение направления
        if resistance_break:
            direction = "BULLISH"
            confidence = "HIGH"
            breakout_type = "RESISTANCE_BREAKOUT"
            breakout_level = current['nearest_resistance']
        elif support_break:
            direction = "BEARISH"
            confidence = "HIGH"
            breakout_type = "SUPPORT_BREAKOUT"
            breakout_level = current['nearest_support']
        else:
            direction = "NEUTRAL"
            confidence = "LOW"
            breakout_type = "CONSOLIDATION"
            breakout_level = None

        # Расчет целей
        consolidation_range = consolidation_high - consolidation_low

        if direction == "BULLISH" and breakout_level:
            tp = breakout_level + consolidation_range
            sl = min(consolidation_low, breakout_level - (consolidation_range * 0.1))
        elif direction == "BEARISH" and breakout_level:
            tp = breakout_level - consolidation_range
            sl = max(consolidation_high, breakout_level + (consolidation_range * 0.1))
        else:
            if 'atr' in current:
                tp = current_price + (2 * current['atr'])
                sl = current_price - (2 * current['atr'])
            else:
                tp = current_price * 1.02
                sl = current_price * 0.98

        return {
            'strategy': 'BREAKOUT',
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 6),
            'stop_loss': round(sl, 6),
            'current_price': round(current_price, 6),
            'details': {
                'breakout_type': breakout_type,
                'breakout_level': round(breakout_level, 6) if breakout_level else None,
                'consolidation_range': round(consolidation_range, 6),
                'nearest_support': round(current['nearest_support'], 6) if not np.isnan(current['nearest_support']) else None,
                'nearest_resistance': round(current['nearest_resistance'], 6) if not np.isnan(current['nearest_resistance']) else None
            }
        }

    def rsi_macd_strategy(self):
        """Стратегия RSI + MACD"""
        if len(self.data) < 2:
            return self._empty_result("RSI_MACD")

        current = self.data.iloc[-1]
        prev = self.data.iloc[-2]
        current_price = current['Close']

        # Сигналы RSI
        rsi_signal = "NEUTRAL"
        if current['rsi'] < 30:
            rsi_signal = "OVERSOLD_BULLISH"
        elif current['rsi'] > 70:
            rsi_signal = "OVERBOUGHT_BEARISH"

        # Сигналы MACD
        macd_signal = "NEUTRAL"
        if current['macd'] > current['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            macd_signal = "CROSS_UP_BULLISH"
        elif current['macd'] < current['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            macd_signal = "CROSS_DOWN_BEARISH"

        # Общий сигнал
        if "BULLISH" in rsi_signal and "BULLISH" in macd_signal:
            direction = "BULLISH"
            confidence = "HIGH"
        elif "BEARISH" in rsi_signal and "BEARISH" in macd_signal:
            direction = "BEARISH"
            confidence = "HIGH"
        else:
            direction = "NEUTRAL"
            confidence = "LOW"

        # Расчет TP/SL
        atr = current['atr']

        if direction == "BULLISH":
            tp = current_price + (2 * atr)
            sl = current_price - (1 * atr)
        elif direction == "BEARISH":
            tp = current_price - (2 * atr)
            sl = current_price + (1 * atr)
        else:
            tp = sl = current_price

        return {
            'strategy': 'RSI_MACD',
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 6),
            'stop_loss': round(sl, 6),
            'current_price': round(current_price, 6),
            'details': {
                'rsi_value': round(current['rsi'], 2),
                'rsi_signal': rsi_signal,
                'macd_signal': macd_signal,
                'atr': round(atr, 6)
            }
        }

    def moving_averages_strategy(self):
        """Стратегия скользящих средних"""
        if len(self.data) < 2:
            return self._empty_result("MA")

        current = self.data.iloc[-1]
        prev = self.data.iloc[-2]
        current_price = current['Close']

        # Сигналы от SMA
        sma_signal = "NEUTRAL"
        if current['sma_20'] > current['sma_50'] and prev['sma_20'] <= prev['sma_50']:
            sma_signal = "GOLDEN_CROSS_BULLISH"
        elif current['sma_20'] < current['sma_50'] and prev['sma_20'] >= prev['sma_50']:
            sma_signal = "DEATH_CROSS_BEARISH"

        # Сигналы от EMA
        ema_signal = "BULLISH" if current['ema_12'] > current['ema_26'] else "BEARISH"

        # Общий сигнал
        if "BULLISH" in sma_signal and ema_signal == "BULLISH":
            direction = "BULLISH"
            confidence = "HIGH"
        elif "BEARISH" in sma_signal and ema_signal == "BEARISH":
            direction = "BEARISH"
            confidence = "HIGH"
        else:
            direction = "NEUTRAL"
            confidence = "MEDIUM"

        # Расчет TP/SL
        atr = current['atr']

        if direction == "BULLISH":
            tp = current_price + (3 * atr)
            sl = current_price - (1.5 * atr)
        elif direction == "BEARISH":
            tp = current_price - (3 * atr)
            sl = current_price + (1.5 * atr)
        else:
            tp = sl = current_price

        return {
            'strategy': 'MA',
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 6),
            'stop_loss': round(sl, 6),
            'current_price': round(current_price, 6),
            'details': {
                'sma_signal': sma_signal,
                'ema_signal': ema_signal,
                'sma_20': round(current['sma_20'], 6),
                'sma_50': round(current['sma_50'], 6),
                'atr': round(atr, 6)
            }
        }

    def bollinger_bands_strategy(self):
        """Стратегия Bollinger Bands"""
        if len(self.data) == 0:
            return self._empty_result("BB")

        current = self.data.iloc[-1]
        current_price = current['Close']

        # Анализ положения цены относительно полос
        if current_price <= current['bb_lower']:
            bb_signal = "LOWER_BAND_OVERSOLD"
            direction = "BULLISH"
            confidence = "HIGH"
        elif current_price >= current['bb_upper']:
            bb_signal = "UPPER_BAND_OVERBOUGHT"
            direction = "BEARISH"
            confidence = "HIGH"
        else:
            bb_signal = "INSIDE_BANDS"
            direction = "NEUTRAL"
            confidence = "LOW"

        # Расчет TP/SL на основе ширины полос
        bb_range = current['bb_upper'] - current['bb_lower']

        if direction == "BULLISH":
            tp = current_price + (0.5 * bb_range)
            sl = current_price - (0.25 * bb_range)
        elif direction == "BEARISH":
            tp = current_price - (0.5 * bb_range)
            sl = current_price + (0.25 * bb_range)
        else:
            tp = sl = current_price

        return {
            'strategy': 'BB',
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 6),
            'stop_loss': round(sl, 6),
            'current_price': round(current_price, 6),
            'details': {
                'bb_signal': bb_signal,
                'bb_upper': round(current['bb_upper'], 6),
                'bb_lower': round(current['bb_lower'], 6),
                'bb_middle': round(current['bb_middle'], 6),
                'bb_width': round((bb_range / current['bb_middle']) * 100, 2)
            }
        }

    def stochastic_ema_strategy(self):
        """Стратегия Stochastic + EMA"""
        if len(self.data) < 2:
            return self._empty_result("STOCH_EMA")

        current = self.data.iloc[-1]
        prev = self.data.iloc[-2]
        current_price = current['Close']

        # Сигналы Stochastic
        stoch_signal = "NEUTRAL"
        if current['stoch_k'] < 20 and current['stoch_d'] < 20:
            stoch_signal = "OVERSOLD_BULLISH"
        elif current['stoch_k'] > 80 and current['stoch_d'] > 80:
            stoch_signal = "OVERBOUGHT_BEARISH"
        elif current['stoch_k'] > current['stoch_d'] and prev['stoch_k'] <= prev['stoch_d']:
            stoch_signal = "CROSS_UP_BULLISH"
        elif current['stoch_k'] < current['stoch_d'] and prev['stoch_k'] >= prev['stoch_d']:
            stoch_signal = "CROSS_DOWN_BEARISH"

        # Сигналы EMA
        ema_signal = "BULLISH" if current['Close'] > current['ema_12'] else "BEARISH"

        # Общий сигнал
        if "BULLISH" in stoch_signal and ema_signal == "BULLISH":
            direction = "BULLISH"
            confidence = "HIGH"
        elif "BEARISH" in stoch_signal and ema_signal == "BEARISH":
            direction = "BEARISH"
            confidence = "HIGH"
        else:
            direction = "NEUTRAL"
            confidence = "MEDIUM"

        # Расчет TP/SL
        atr = current['atr']

        if direction == "BULLISH":
            tp = current_price + (2.5 * atr)
            sl = current_price - (1.2 * atr)
        elif direction == "BEARISH":
            tp = current_price - (2.5 * atr)
            sl = current_price + (1.2 * atr)
        else:
            tp = sl = current_price

        return {
            'strategy': 'STOCH_EMA',
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 6),
            'stop_loss': round(sl, 6),
            'current_price': round(current_price, 6),
            'details': {
                'stoch_signal': stoch_signal,
                'stoch_k': round(current['stoch_k'], 2),
                'stoch_d': round(current['stoch_d'], 2),
                'ema_signal': ema_signal,
                'atr': round(atr, 6)
            }
        }

    def parabolic_sar_strategy(self):
        """Стратегия Parabolic SAR + ADX"""
        if len(self.data) == 0:
            return self._empty_result("SAR_ADX")

        current = self.data.iloc[-1]
        current_price = current['Close']

        # Сигналы Parabolic SAR
        sar_signal = "BULLISH_TREND" if current_price > current['parabolic_sar'] else "BEARISH_TREND"
        direction = "BULLISH" if current_price > current['parabolic_sar'] else "BEARISH"

        # Сигналы ADX
        adx_strength = "WEAK"
        if current['adx'] > 40:
            adx_strength = "VERY_STRONG"
        elif current['adx'] > 25:
            adx_strength = "STRONG"

        confidence = "HIGH" if adx_strength != "WEAK" else "LOW"

        # Расчет TP/SL
        atr = current['atr']

        if direction == "BULLISH":
            tp = current_price + (4 * atr)
            sl = current['parabolic_sar']
        else:
            tp = current_price - (4 * atr)
            sl = current['parabolic_sar']

        return {
            'strategy': 'SAR_ADX',
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 6),
            'stop_loss': round(sl, 6),
            'current_price': round(current_price, 6),
            'details': {
                'sar_signal': sar_signal,
                'sar_value': round(current['parabolic_sar'], 6),
                'adx': round(current['adx'], 2),
                'adx_strength': adx_strength,
                'atr': round(atr, 6)
            }
        }

    def _empty_result(self, strategy_name):
        """Возвращает пустой результат для стратегии"""
        return {
            'strategy': strategy_name,
            'direction': "NO_DATA",
            'confidence': "LOW",
            'take_profit': 0,
            'stop_loss': 0,
            'current_price': 0,
            'details': {'error': 'Not enough data for analysis'}
        }

    def analyze_strategy(self, strategy_key):
        """Анализ выбранной стратегии"""
        if strategy_key not in self.strategies:
            return None

        # Расчет индикаторов
        self.calculate_technical_indicators()

        # Получение сигналов от стратегии
        return self.strategies[strategy_key]['function']()

    def compare_strategies(self):
        """Сравнение всех стратегий и расчет общей вероятности"""
        self.calculate_technical_indicators()
        current_price = self.data['Close'].iloc[-1]

        results = []
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        total_weight = 0
        total_tp = 0
        total_sl = 0

        # Веса для каждой стратегии (можете настроить)
        strategy_weights = {
            'RSI_MACD': 1.0,
            'MA': 1.2,
            'BB': 0.8,
            'STOCH_EMA': 0.9,
            'SAR_ADX': 1.1,
            'BREAKOUT': 1.3
        }

        # Собираем результаты всех стратегий
        for key, strategy in self.strategies.items():
            result = strategy['function']()
            results.append(result)

            # Подсчет сигналов с учетом веса
            weight = strategy_weights.get(key, 1.0)
            if result['direction'] == "BULLISH":
                bullish_count += weight
            elif result['direction'] == "BEARISH":
                bearish_count += weight
            else:
                neutral_count += weight

            total_weight += weight

            # Суммируем TP и SL для усреднения
            if result['take_profit'] > 0:
                total_tp += result['take_profit'] * weight
                total_sl += result['stop_loss'] * weight

        # Расчет общей вероятности
        total_signals = bullish_count + bearish_count + neutral_count
        if total_signals > 0:
            bullish_probability = (bullish_count / total_signals) * 100
            bearish_probability = (bearish_count / total_signals) * 100
            neutral_probability = (neutral_count / total_signals) * 100
        else:
            bullish_probability = bearish_probability = neutral_probability = 33.33

        # Определение общего направления
        if bullish_probability > bearish_probability and bullish_probability > neutral_probability:
            overall_direction = "BULLISH"
            overall_confidence = "HIGH" if bullish_probability > 60 else "MEDIUM" if bullish_probability > 40 else "LOW"
        elif bearish_probability > bullish_probability and bearish_probability > neutral_probability:
            overall_direction = "BEARISH"
            overall_confidence = "HIGH" if bearish_probability > 60 else "MEDIUM" if bearish_probability > 40 else "LOW"
        else:
            overall_direction = "NEUTRAL"
            overall_confidence = "MEDIUM" if neutral_probability > 50 else "LOW"

        # Усредненные TP/SL
        avg_tp = round(total_tp / total_weight, 6) if total_weight > 0 else current_price
        avg_sl = round(total_sl / total_weight, 6) if total_weight > 0 else current_price

        # Создаем словарь с результатами всех стратегий
        strategy_results = {}
        for result in results:
            strategy_results[result['strategy']] = {
                'direction': result['direction'],
                'confidence': result['confidence'],
                'take_profit': result['take_profit'],
                'stop_loss': result['stop_loss']
            }

        overall_result = {
            'overall': {
                'direction': overall_direction,
                'confidence': overall_confidence,
                'take_profit': avg_tp,
                'stop_loss': avg_sl,
                'current_price': round(current_price, 6),
                'probabilities': {
                    'bullish': round(bullish_probability, 1),
                    'bearish': round(bearish_probability, 1),
                    'neutral': round(neutral_probability, 1)
                }
            },
            'strategies': strategy_results
        }

        return overall_result


def analyze_crypto(symbol, timeframe, strategy):
    """Основная функция анализа"""
    try:
        # Валидация входных данных
        if not symbol:
            return {"error": "Symbol is required"}

        # Инициализация фетчера
        fetcher = CryptoDataFetcher()

        # Проверка символа
        if not fetcher.validate_crypto_symbol(symbol):
            return {"error": f"Symbol {symbol} not found on Bybit"}

        # Получение данных
        data, error = fetcher.get_crypto_data_with_current(symbol, timeframe)
        if error:
            return {"error": f"Failed to get data: {error}"}

        if data is None or data.empty:
            return {"error": "No data received"}

        # Инициализация анализатора
        analyzer = TradingStrategyAnalyzer(data)

        if not analyzer.prepare_data():
            return {"error": "Failed to prepare data for analysis"}

        # Анализ стратегии
        if strategy.upper() == "ALL":
            result = analyzer.compare_strategies()
        else:
            strategy_map = {
                'RSI_MACD': 'RSI_MACD',
                'MA': 'MA',
                'BB': 'BB',
                'STOCH_EMA': 'STOCH_EMA',
                'SAR_ADX': 'SAR_ADX',
                'BREAKOUT': 'BREAKOUT'
            }

            strategy_key = strategy_map.get(strategy.upper())
            if not strategy_key:
                return {"error": f"Unknown strategy: {strategy}"}

            result = analyzer.analyze_strategy(strategy_key)
            if not result:
                return {"error": f"Failed to analyze strategy: {strategy}"}

        return {
            "success": True,
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "data_points": len(data),
            "result": result
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


def main():
    """Точка входа для использования через командную строку"""
    if len(sys.argv) < 4:
        print("Usage: python crypto_analyzer.py <symbol> <timeframe> <strategy|ALL>")
        print("Example: python crypto_analyzer.py BTC 5 MA")
        print("Example: python crypto_analyzer.py ETH D ALL")
        print("\nAvailable timeframes: 1, 5, 15, 60, D, W, M")
        print("Available strategies: RSI_MACD, MA, BB, STOCH_EMA, SAR_ADX, BREAKOUT, ALL")
        sys.exit(1)

    symbol = sys.argv[1]
    timeframe = sys.argv[2]
    strategy = sys.argv[3]

    result = analyze_crypto(symbol, timeframe, strategy)

    # Вывод в формате JSON для удобного парсинга в Go
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()