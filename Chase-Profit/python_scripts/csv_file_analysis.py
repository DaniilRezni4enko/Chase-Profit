import pandas as pd
import numpy as np
import ta
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class TradingStrategyAnalyzer:
    def __init__(self, csv_file_path):
        """
        Инициализация анализатора торговых стратегий

        Args:
            csv_file_path: путь к CSV файлу с данными
        """
        self.data = self.load_data(csv_file_path)
        self.strategies = {
            '1': {'name': 'RSI + MACD', 'function': self.rsi_macd_strategy},
            '2': {'name': 'Скользящие средние', 'function': self.moving_averages_strategy},
            '3': {'name': 'Bollinger Bands', 'function': self.bollinger_bands_strategy},
            '4': {'name': 'Stochastic + EMA', 'function': self.stochastic_ema_strategy},
            '5': {'name': 'Parabolic SAR + ADX', 'function': self.parabolic_sar_strategy},
            '6': {'name': 'Пробой уровня', 'function': self.breakout_strategy}
        }

    def load_data(self, csv_file_path):
        """Загрузка и подготовка данных из CSV файла"""
        try:
            data = pd.read_csv(csv_file_path)

            # Проверяем необходимые колонки
            required_columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    raise ValueError(f"Отсутствует обязательная колонка: {col}")

            # Конвертируем Timestamp если нужно
            if 'Timestamp' in data.columns:
                try:
                    data['Timestamp'] = pd.to_datetime(data['Timestamp'])
                except:
                    print("Не удалось конвертировать Timestamp, используем как есть")

            # Сортируем по времени
            data = data.sort_values('Timestamp').reset_index(drop=True)

            print(f"✅ Данные успешно загружены: {len(data)} свечей")
            print(f"📅 Период: {data['Timestamp'].iloc[0]} - {data['Timestamp'].iloc[-1]}")

            return data

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return None

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
        df['bb_Lower'] = bollinger.bollinger_lband()
        df['bb_middle'] = bollinger.bollinger_mavg()

        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()

        # Parabolic SAR
        df['parabolic_sar'] = ta.trend.PSARIndicator(df['High'], df['Low'], df['Close']).psar()

        # ADX
        df['adx'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14).adx()

        # ATR для расчета стоп-лосса
        df['atr'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()

        # Уровни поддержки и сопротивления для пробоев
        df = self.calculate_support_resistance(df)

        self.data = df

    def calculate_support_resistance(self, df, window=20):
        """
        Расчет уровней поддержки и сопротивления
        на основе локальных минимумов и максимумов
        """
        # Локальные максимумы (сопротивление)
        df['resistance'] = df['High'].rolling(window=window, center=True).max()

        # Локальные минимумы (поддержка)
        df['support'] = df['Low'].rolling(window=window, center=True).min()

        # Определение ближайших значимых уровней
        current_High = df['High'].iloc[-1]
        current_Low = df['Low'].iloc[-1]

        # Ближайшие уровни сопротивления (выше текущей цены)
        resistance_levels = df['resistance'].unique()
        resistance_levels = sorted([r for r in resistance_levels if r > current_High and not np.isnan(r)])

        # Ближайшие уровни поддержки (ниже текущей цены)
        support_levels = df['support'].unique()
        support_levels = sorted([s for s in support_levels if s < current_Low and not np.isnan(s)], reverse=True)

        # Сохраняем ближайшие уровни
        df['nearest_resistance'] = resistance_levels[0] if resistance_levels else np.nan
        df['nearest_support'] = support_levels[0] if support_levels else np.nan

        return df

    def detect_breakout(self, df, lookback_period=10):
        """
        Обнаружение пробоев уровней поддержки/сопротивления
        """
        current = df.iloc[-1]
        current_Close = current['Close']
        current_High = current['High']
        current_Low = current['Low']

        # Анализируем последние N свечей для определения консолидации
        recent_data = df.tail(lookback_period)

        # Определяем диапазон консолидации
        consolidation_High = recent_data['High'].max()
        consolidation_Low = recent_data['Low'].min()
        consolidation_range = consolidation_High - consolidation_Low

        # Проверяем пробой сопротивления
        resistance_break = False
        if not np.isnan(current['nearest_resistance']):
            # Пробой считается если цена закрылась выше сопротивления
            # и объем выше среднего
            if (current_Close > current['nearest_resistance'] and
                    current_High > consolidation_High and
                    current['Volume'] > recent_data['Volume'].mean()):
                resistance_break = True

        # Проверяем пробой поддержки
        support_break = False
        if not np.isnan(current['nearest_support']):
            # Пробой считается если цена закрылась ниже поддержки
            # и объем выше среднего
            if (current_Close < current['nearest_support'] and
                    current_Low < consolidation_Low and
                    current['Volume'] > recent_data['Volume'].mean()):
                support_break = True

        return resistance_break, support_break, consolidation_High, consolidation_Low

    def breakout_strategy(self):
        """Стратегия пробоя уровней"""
        current = self.data.iloc[-1]
        current_price = current['Close']

        # Обнаружение пробоев
        resistance_break, support_break, consolidation_High, consolidation_Low = self.detect_breakout(self.data)

        # Определение направления
        if resistance_break:
            direction = "ВВЕРХ"
            confidence = "ВЫСОКАЯ"
            breakout_type = "ПРОБОЙ СОПРОТИВЛЕНИЯ"
            breakout_level = current['nearest_resistance']
        elif support_break:
            direction = "ВНИЗ"
            confidence = "ВЫСОКАЯ"
            breakout_type = "ПРОБОЙ ПОДДЕРЖКИ"
            breakout_level = current['nearest_support']
        else:
            direction = "НЕОПРЕДЕЛЕННО"
            confidence = "НИЗКАЯ"
            breakout_type = "КОНСОЛИДАЦИЯ"
            breakout_level = None

        # Расчет целей на основе диапазона консолидации
        consolidation_range = consolidation_High - consolidation_Low

        if direction == "ВВЕРХ" and breakout_level:
            # Цель: уровень пробоя + диапазон консолидации
            tp = breakout_level + consolidation_range
            # Стоп-лосс: ниже уровня консолидации или ниже пробойного уровня
            sl = min(consolidation_Low, breakout_level - (consolidation_range * 0.1))
        elif direction == "ВНИЗ" and breakout_level:
            # Цель: уровень пробоя - диапазон консолидации
            tp = breakout_level - consolidation_range
            # Стоп-лосс: выше уровня консолидации или выше пробойного уровня
            sl = max(consolidation_High, breakout_level + (consolidation_range * 0.1))
        else:
            # Нет пробоя - используем ATR для расчетов
            tp = current_price + (2 * current['atr'])
            sl = current_price - (2 * current['atr'])

        # Дополнительные метрики для анализа
        Volume_analysis = "ВЫСОКИЙ" if current['Volume'] > self.data['Volume'].tail(20).mean() else "СРЕДНИЙ"
        volatility_analysis = "ВЫСОКАЯ" if consolidation_range > current['atr'] else "НОРМАЛЬНАЯ"

        details = {
            'Тип пробоя': breakout_type,
            'Уровень пробоя': f"{breakout_level:.4f}" if breakout_level else "НЕТ",
            'Диапазон консолидации': f"{consolidation_range:.4f}",
            'Объем': f"{Volume_analysis}",
            'Волатильность': f"{volatility_analysis}",
            'Текущая цена': f"{current_price:.4f}",
            'Ближайшая поддержка': f"{current['nearest_support']:.4f}" if not np.isnan(
                current['nearest_support']) else "НЕТ",
            'Ближайшее сопротивление': f"{current['nearest_resistance']:.4f}" if not np.isnan(
                current['nearest_resistance']) else "НЕТ"
        }

        return {
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 4),
            'stop_loss': round(sl, 4),
            'details': details
        }

    def rsi_macd_strategy(self):
        """Стратегия RSI + MACD"""
        current = self.data.iloc[-1]

        # Сигналы RSI
        rsi_signal = "НЕЙТРАЛЬНЫЙ"
        if current['rsi'] < 30:
            rsi_signal = "ПЕРЕПРОДАННОСТЬ (БЫЧИЙ)"
        elif current['rsi'] > 70:
            rsi_signal = "ПЕРЕКУПЛЕННОСТЬ (МЕДВЕЖИЙ)"

        # Сигналы MACD
        macd_signal = "НЕЙТРАЛЬНЫЙ"
        if current['macd'] > current['macd_signal'] and self.data.iloc[-2]['macd'] <= self.data.iloc[-2]['macd_signal']:
            macd_signal = "ПЕРЕСЕЧЕНИЕ ВВЕРХ (БЫЧИЙ)"
        elif current['macd'] < current['macd_signal'] and self.data.iloc[-2]['macd'] >= self.data.iloc[-2][
            'macd_signal']:
            macd_signal = "ПЕРЕСЕЧЕНИЕ ВНИЗ (МЕДВЕЖИЙ)"

        # Общий сигнал
        if "БЫЧИЙ" in rsi_signal and "БЫЧИЙ" in macd_signal:
            direction = "ВВЕРХ"
            confidence = "ВЫСОКАЯ"
        elif "МЕДВЕЖИЙ" in rsi_signal and "МЕДВЕЖИЙ" in macd_signal:
            direction = "ВНИЗ"
            confidence = "ВЫСОКАЯ"
        else:
            direction = "НЕОПРЕДЕЛЕННО"
            confidence = "НИЗКАЯ"

        # Расчет TP/SL
        current_price = current['Close']
        atr = current['atr']

        if direction == "ВВЕРХ":
            tp = current_price + (2 * atr)
            sl = current_price - (1 * atr)
        elif direction == "ВНИЗ":
            tp = current_price - (2 * atr)
            sl = current_price + (1 * atr)
        else:
            tp = sl = current_price

        return {
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 4),
            'stop_loss': round(sl, 4),
            'details': {
                'RSI': f"{current['rsi']:.2f} - {rsi_signal}",
                'MACD': f"{macd_signal}",
                'Текущая цена': f"{current_price:.4f}",
                'ATR': f"{atr:.4f}"
            }
        }

    def moving_averages_strategy(self):
        """Стратегия скользящих средних"""
        current = self.data.iloc[-1]

        # Сигналы от SMA
        sma_signal = "НЕЙТРАЛЬНЫЙ"
        if current['sma_20'] > current['sma_50'] and self.data.iloc[-2]['sma_20'] <= self.data.iloc[-2]['sma_50']:
            sma_signal = "ЗОЛОТОЙ КРЕСТ (БЫЧИЙ)"
        elif current['sma_20'] < current['sma_50'] and self.data.iloc[-2]['sma_20'] >= self.data.iloc[-2]['sma_50']:
            sma_signal = "МЕРТВЫЙ КРЕСТ (МЕДВЕЖИЙ)"

        # Сигналы от EMA
        ema_signal = "НЕЙТРАЛЬНЫЙ"
        if current['ema_12'] > current['ema_26']:
            ema_signal = "БЫЧИЙ"
        else:
            ema_signal = "МЕДВЕЖИЙ"

        # Общий сигнал
        if "БЫЧИЙ" in sma_signal and ema_signal == "БЫЧИЙ":
            direction = "ВВЕРХ"
            confidence = "ВЫСОКАЯ"
        elif "МЕДВЕЖИЙ" in sma_signal and ema_signal == "МЕДВЕЖИЙ":
            direction = "ВНИЗ"
            confidence = "ВЫСОКАЯ"
        else:
            direction = "НЕОПРЕДЕЛЕННО"
            confidence = "СРЕДНЯЯ"

        # Расчет TP/SL
        current_price = current['Close']
        atr = current['atr']

        if direction == "ВВЕРХ":
            tp = current_price + (3 * atr)
            sl = current_price - (1.5 * atr)
        elif direction == "ВНИЗ":
            tp = current_price - (3 * atr)
            sl = current_price + (1.5 * atr)
        else:
            tp = sl = current_price

        return {
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 4),
            'stop_loss': round(sl, 4),
            'details': {
                'SMA 20/50': f"{sma_signal}",
                'EMA 12/26': f"{ema_signal}",
                'Текущая цена': f"{current_price:.4f}",
                'ATR': f"{atr:.4f}"
            }
        }

    def bollinger_bands_strategy(self):
        """Стратегия Bollinger Bands"""
        current = self.data.iloc[-1]
        current_price = current['Close']

        # Анализ положения цены относительно полос
        if current_price <= current['bb_Lower']:
            bb_signal = "ЦЕНА У НИЖНЕЙ ПОЛОСЫ (ПЕРЕПРОДАННОСТЬ)"
            direction = "ВВЕРХ"
            confidence = "ВЫСОКАЯ"
        elif current_price >= current['bb_upper']:
            bb_signal = "ЦЕНА У ВЕРХНЕЙ ПОЛОСЫ (ПЕРЕКУПЛЕННОСТЬ)"
            direction = "ВНИЗ"
            confidence = "ВЫСОКАЯ"
        else:
            bb_signal = "ЦЕНА ВНУТРИ ПОЛОС"
            direction = "НЕОПРЕДЕЛЕННО"
            confidence = "НИЗКАЯ"

        # Анализ ширины полос (волатильность)
        bb_width = (current['bb_upper'] - current['bb_Lower']) / current['bb_middle']
        volatility = "ВЫСОКАЯ" if bb_width > 0.05 else "НИЗКАЯ"

        # Расчет TP/SL на основе ширины полос
        bb_range = current['bb_upper'] - current['bb_Lower']

        if direction == "ВВЕРХ":
            tp = current_price + (0.5 * bb_range)
            sl = current_price - (0.25 * bb_range)
        elif direction == "ВНИЗ":
            tp = current_price - (0.5 * bb_range)
            sl = current_price + (0.25 * bb_range)
        else:
            tp = sl = current_price

        return {
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 4),
            'stop_loss': round(sl, 4),
            'details': {
                'Bollinger Bands': bb_signal,
                'Ширина полос': f"{bb_width:.4f}",
                'Волатильность': volatility,
                'Текущая цена': f"{current_price:.4f}",
                'Верхняя полоса': f"{current['bb_upper']:.4f}",
                'Нижняя полоса': f"{current['bb_Lower']:.4f}"
            }
        }

    def stochastic_ema_strategy(self):
        """Стратегия Stochastic + EMA"""
        current = self.data.iloc[-1]

        # Сигналы Stochastic
        stoch_signal = "НЕЙТРАЛЬНЫЙ"
        if current['stoch_k'] < 20 and current['stoch_d'] < 20:
            stoch_signal = "ПЕРЕПРОДАННОСТЬ (БЫЧИЙ)"
        elif current['stoch_k'] > 80 and current['stoch_d'] > 80:
            stoch_signal = "ПЕРЕКУПЛЕННОСТЬ (МЕДВЕЖИЙ)"
        elif current['stoch_k'] > current['stoch_d'] and self.data.iloc[-2]['stoch_k'] <= self.data.iloc[-2]['stoch_d']:
            stoch_signal = "ПЕРЕСЕЧЕНИЕ ВВЕРХ (БЫЧИЙ)"
        elif current['stoch_k'] < current['stoch_d'] and self.data.iloc[-2]['stoch_k'] >= self.data.iloc[-2]['stoch_d']:
            stoch_signal = "ПЕРЕСЕЧЕНИЕ ВНИЗ (МЕДВЕЖИЙ)"

        # Сигналы EMA
        ema_signal = "БЫЧИЙ" if current['Close'] > current['ema_12'] else "МЕДВЕЖИЙ"

        # Общий сигнал
        if "БЫЧИЙ" in stoch_signal and ema_signal == "БЫЧИЙ":
            direction = "ВВЕРХ"
            confidence = "ВЫСОКАЯ"
        elif "МЕДВЕЖИЙ" in stoch_signal and ema_signal == "МЕДВЕЖИЙ":
            direction = "ВНИЗ"
            confidence = "ВЫСОКАЯ"
        else:
            direction = "НЕОПРЕДЕЛЕННО"
            confidence = "СРЕДНЯЯ"

        # Расчет TP/SL
        current_price = current['Close']
        atr = current['atr']

        if direction == "ВВЕРХ":
            tp = current_price + (2.5 * atr)
            sl = current_price - (1.2 * atr)
        elif direction == "ВНИЗ":
            tp = current_price - (2.5 * atr)
            sl = current_price + (1.2 * atr)
        else:
            tp = sl = current_price

        return {
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 4),
            'stop_loss': round(sl, 4),
            'details': {
                'Stochastic K/D': f"{current['stoch_k']:.2f}/{current['stoch_d']:.2f} - {stoch_signal}",
                'EMA 12': f"{ema_signal}",
                'Текущая цена': f"{current_price:.4f}",
                'ATR': f"{atr:.4f}"
            }
        }

    def parabolic_sar_strategy(self):
        """Стратегия Parabolic SAR + ADX"""
        current = self.data.iloc[-1]
        current_price = current['Close']

        # Сигналы Parabolic SAR
        sar_signal = "НЕЙТРАЛЬНЫЙ"
        if current_price > current['parabolic_sar']:
            sar_signal = "БЫЧИЙ ТРЕНД"
            direction = "ВВЕРХ"
        else:
            sar_signal = "МЕДВЕЖИЙ ТРЕНД"
            direction = "ВНИЗ"

        # Сигналы ADX (сила тренда)
        adx_strength = "СЛАБЫЙ"
        if current['adx'] > 25:
            adx_strength = "СИЛЬНЫЙ"
        elif current['adx'] > 40:
            adx_strength = "ОЧЕНЬ СИЛЬНЫЙ"

        confidence = "ВЫСОКАЯ" if adx_strength != "СЛАБЫЙ" else "НИЗКАЯ"

        # Расчет TP/SL
        atr = current['atr']

        if direction == "ВВЕРХ":
            tp = current_price + (4 * atr)
            sl = current['parabolic_sar']  # Используем SAR как стоп-лосс
        else:
            tp = current_price - (4 * atr)
            sl = current['parabolic_sar']

        return {
            'direction': direction,
            'confidence': confidence,
            'take_profit': round(tp, 4),
            'stop_loss': round(sl, 4),
            'details': {
                'Parabolic SAR': f"{sar_signal} ({current['parabolic_sar']:.4f})",
                'ADX': f"{current['adx']:.2f} - {adx_strength} ТРЕНД",
                'Текущая цена': f"{current_price:.4f}",
                'ATR': f"{atr:.4f}"
            }
        }

    def analyze_strategy(self, strategy_key):
        """Анализ выбранной стратегии"""
        if strategy_key not in self.strategies:
            return None

        print(f"\n🔍 Анализ по стратегии: {self.strategies[strategy_key]['name']}")
        print("=" * 60)

        # Расчет индикаторов
        self.calculate_technical_indicators()

        # Получение сигналов от стратегии
        result = self.strategies[strategy_key]['function']()

        # Вывод результатов
        print(f"🎯 Направление: {result['direction']}")
        print(f"📊 Уверенность: {result['confidence']}")
        print(f"💰 Take Profit: {result['take_profit']}")
        print(f"🛑 Stop Loss: {result['stop_loss']}")

        print("\n📈 Детали анализа:")
        for key, value in result['details'].items():
            print(f"   {key}: {value}")

        # Расчет риска/прибыли
        if result['direction'] != "НЕОПРЕДЕЛЕННО":
            current_price = self.data['Close'].iloc[-1]
            risk = abs(current_price - result['stop_loss'])
            reward = abs(result['take_profit'] - current_price)
            risk_reward = reward / risk if risk > 0 else 0

            print(f"\n⚖️ Соотношение риск/прибыль: 1:{risk_reward:.2f}")

            if risk_reward >= 2:
                print("✅ ХОРОШЕЕ соотношение риск/прибыль")
            elif risk_reward >= 1:
                print("⚠️  СРЕДНЕЕ соотношение риск/прибыль")
            else:
                print("❌ ПЛОХОЕ соотношение риск/прибыль")

        return result

    def compare_strategies(self):
        """Сравнение всех стратегий"""
        print("\n📊 СРАВНЕНИЕ ВСЕХ СТРАТЕГИЙ")
        print("=" * 80)

        self.calculate_technical_indicators()
        current_price = self.data['Close'].iloc[-1]

        results = []
        for key, strategy in self.strategies.items():
            result = strategy['function']()
            results.append({
                'Стратегия': strategy['name'],
                'Направление': result['direction'],
                'Уверенность': result['confidence'],
                'TP': result['take_profit'],
                'SL': result['stop_loss']
            })

        # Создаем DataFrame для красивого вывода
        results_df = pd.DataFrame(results)
        print(results_df.to_string(index=False))

        # Анализ консенсуса
        bullish_count = sum(1 for r in results if r['Направление'] == 'ВВЕРХ')
        bearish_count = sum(1 for r in results if r['Направление'] == 'ВНИЗ')

        print(f"\n🎯 КОНСЕНСУС СТРАТЕГИЙ:")
        print(f"   Бычьих сигналов: {bullish_count}")
        print(f"   Медвежьих сигналов: {bearish_count}")

        if bullish_count > bearish_count:
            consensus = "ВВЕРХ"
        elif bearish_count > bullish_count:
            consensus = "ВНИЗ"
        else:
            consensus = "НЕОПРЕДЕЛЕННО"

        print(f"   ОБЩИЙ СИГНАЛ: {consensus}")

        return results


def main():
    """Основная функция программы"""
    print("🚀 АНАЛИЗАТОР ТОРГОВЫХ СТРАТЕГИЙ")
    print("=" * 50)
    print("📈 Теперь с СТРАТЕГИЕЙ ПРОБОЯ УРОВНЕЙ!")

    # Запрос пути к файлу
    csv_file = input("📁 Введите путь к CSV файлу: ").strip()

    # Создание анализатора
    analyzer = TradingStrategyAnalyzer(csv_file)

    if analyzer.data is None:
        return

    while True:
        print("\n" + "=" * 50)
        print("📊 МЕНЮ АНАЛИЗА:")
        print("1. Анализ RSI + MACD")
        print("2. Анализ Скользящих средних")
        print("3. Анализ Bollinger Bands")
        print("4. Анализ Stochastic + EMA")
        print("5. Анализ Parabolic SAR + ADX")
        print("6. Анализ ПРОБОЯ УРОВНЕЙ")
        print("7. Сравнить все стратегии")
        print("8. Выход")

        choice = input("\nВыберите действие (1-8): ").strip()

        if choice == '1':
            analyzer.analyze_strategy('1')
        elif choice == '2':
            analyzer.analyze_strategy('2')
        elif choice == '3':
            analyzer.analyze_strategy('3')
        elif choice == '4':
            analyzer.analyze_strategy('4')
        elif choice == '5':
            analyzer.analyze_strategy('5')
        elif choice == '6':
            analyzer.analyze_strategy('6')
        elif choice == '7':
            analyzer.compare_strategies()
        elif choice == '8':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()