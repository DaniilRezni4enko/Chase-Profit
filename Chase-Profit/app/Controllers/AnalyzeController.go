package Controllers

import (
	"Chase-Profit/app/Controllers/base"
	"Chase-Profit/config"
	"Chase-Profit/database"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"strings"
	"text/template"
	"time"
)

func ShowAnalyzeSettings(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	tmpl, err := template.ParseFiles(path+"analyze.html", path+"templates/alerts.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
	get_cookie, _ := r.Cookie("user")
	email := get_cookie.Value

	if email != "" {
		//go AlertProcessing(w, r)
	}
}

// Структуры для парсинга JSON результатов

// Результат для одной стратегии
type SingleStrategyResult struct {
	Strategy     string                 `json:"strategy"`
	Direction    string                 `json:"direction"`
	Confidence   string                 `json:"confidence"`
	TakeProfit   float64                `json:"take_profit"`
	StopLoss     float64                `json:"stop_loss"`
	CurrentPrice float64                `json:"current_price"`
	Details      map[string]interface{} `json:"details"`
}

// Результат для всех стратегий (общая вероятность)
type OverallResult struct {
	Overall struct {
		Direction     string  `json:"direction"`
		Confidence    string  `json:"confidence"`
		TakeProfit    float64 `json:"take_profit"`
		StopLoss      float64 `json:"stop_loss"`
		CurrentPrice  float64 `json:"current_price"`
		Probabilities struct {
			Bullish float64 `json:"bullish"`
			Bearish float64 `json:"bearish"`
			Neutral float64 `json:"neutral"`
		} `json:"probabilities"`
	} `json:"overall"`
	Strategies map[string]struct {
		Direction  string  `json:"direction"`
		Confidence string  `json:"confidence"`
		TakeProfit float64 `json:"take_profit"`
		StopLoss   float64 `json:"stop_loss"`
	} `json:"strategies"`
}

// Базовый ответ от Python скрипта
type AnalysisResponse struct {
	Success    bool            `json:"success"`
	Symbol     string          `json:"symbol"`
	Timeframe  string          `json:"timeframe"`
	Timestamp  string          `json:"timestamp"`
	DataPoints int             `json:"data_points"`
	Result     json.RawMessage `json:"result"`
	Error      string          `json:"error,omitempty"`
}

// CryptoAnalyzer основной класс для анализа
type CryptoAnalyzer struct {
	pythonScriptPath string
}

// NewCryptoAnalyzer создает новый анализатор
func NewCryptoAnalyzer(pythonScriptPath string) *CryptoAnalyzer {
	return &CryptoAnalyzer{
		pythonScriptPath: pythonScriptPath,
	}
}

// Analyze выполняет анализ криптовалюты
func (ca *CryptoAnalyzer) Analyze(symbol, timeframe, strategy string) (*AnalysisResponse, error) {
	// Проверяем наличие Python скрипта
	if _, err := os.Stat(ca.pythonScriptPath); os.IsNotExist(err) {
		return nil, fmt.Errorf("Python script not found: %s", ca.pythonScriptPath)
	}

	// Вызов Python скрипта
	cmd := exec.Command("python3", ca.pythonScriptPath, symbol, timeframe, strategy)

	// Получаем вывод
	output, err := cmd.Output()
	if err != nil {
		// Пытаемся получить stderr для лучшей диагностики
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("Python script error: %s\n%s", err, exitErr.Stderr)
		}
		return nil, fmt.Errorf("Failed to execute Python script: %v", err)
	}

	// Парсим JSON ответ
	var response AnalysisResponse
	if err := json.Unmarshal(output, &response); err != nil {
		return nil, fmt.Errorf("Failed to parse JSON response: %v\nOutput: %s", err, string(output))
	}

	if !response.Success {
		return &response, fmt.Errorf("Analysis failed: %s", response.Error)
	}

	return &response, nil
}

// ParseSingleStrategy парсит результат для одной стратегии
func (ca *CryptoAnalyzer) ParseSingleStrategy(response *AnalysisResponse) (*SingleStrategyResult, error) {
	var result SingleStrategyResult
	if err := json.Unmarshal(response.Result, &result); err != nil {
		return nil, fmt.Errorf("Failed to parse single strategy result: %v", err)
	}
	return &result, nil
}

// ParseOverallResult парсит результат для всех стратегий
func (ca *CryptoAnalyzer) ParseOverallResult(response *AnalysisResponse) (*OverallResult, error) {
	var result OverallResult
	if err := json.Unmarshal(response.Result, &result); err != nil {
		return nil, fmt.Errorf("Failed to parse overall result: %v", err)
	}
	return &result, nil
}

// GetAnalysisSummary возвращает краткую сводку анализа
func (ca *CryptoAnalyzer) GetAnalysisSummary(response *AnalysisResponse) (string, error) {
	var summary strings.Builder

	summary.WriteString(fmt.Sprintf("Analysis for %s (%s timeframe):\n",
		response.Symbol, response.Timeframe))
	summary.WriteString(fmt.Sprintf("Time: %s\n", response.Timestamp))
	summary.WriteString(fmt.Sprintf("Data points: %d\n", response.DataPoints))

	// Определяем тип результата
	if strings.Contains(string(response.Result), "overall") {
		// Это результат для всех стратегий
		overallResult, err := ca.ParseOverallResult(response)
		if err != nil {
			return "", err
		}

		summary.WriteString(fmt.Sprintf("\nOverall Analysis:\n"))
		summary.WriteString(fmt.Sprintf("  Direction: %s\n", overallResult.Overall.Direction))
		summary.WriteString(fmt.Sprintf("  Confidence: %s\n", overallResult.Overall.Confidence))
		summary.WriteString(fmt.Sprintf("  Current Price: $%.2f\n", overallResult.Overall.CurrentPrice))
		summary.WriteString(fmt.Sprintf("  Take Profit: $%.2f\n", overallResult.Overall.TakeProfit))
		summary.WriteString(fmt.Sprintf("  Stop Loss: $%.2f\n", overallResult.Overall.StopLoss))
		summary.WriteString(fmt.Sprintf("  Probabilities:\n"))
		summary.WriteString(fmt.Sprintf("    Bullish: %.1f%%\n", overallResult.Overall.Probabilities.Bullish))
		summary.WriteString(fmt.Sprintf("    Bearish: %.1f%%\n", overallResult.Overall.Probabilities.Bearish))
		summary.WriteString(fmt.Sprintf("    Neutral: %.1f%%\n", overallResult.Overall.Probabilities.Neutral))

		summary.WriteString(fmt.Sprintf("\nIndividual Strategies:\n"))
		for strategyName, strategy := range overallResult.Strategies {
			summary.WriteString(fmt.Sprintf("  %s: %s (%s) TP: $%.2f SL: $%.2f\n",
				strategyName, strategy.Direction, strategy.Confidence,
				strategy.TakeProfit, strategy.StopLoss))
		}
	} else {
		// Это результат для одной стратегии
		singleResult, err := ca.ParseSingleStrategy(response)
		if err != nil {
			return "", err
		}

		summary.WriteString(fmt.Sprintf("\nStrategy: %s\n", singleResult.Strategy))
		summary.WriteString(fmt.Sprintf("  Direction: %s\n", singleResult.Direction))
		summary.WriteString(fmt.Sprintf("  Confidence: %s\n", singleResult.Confidence))
		summary.WriteString(fmt.Sprintf("  Current Price: $%.2f\n", singleResult.CurrentPrice))
		summary.WriteString(fmt.Sprintf("  Take Profit: $%.2f\n", singleResult.TakeProfit))
		summary.WriteString(fmt.Sprintf("  Stop Loss: $%.2f\n", singleResult.StopLoss))

		// Детали стратегии
		if len(singleResult.Details) > 0 {
			summary.WriteString(fmt.Sprintf("  Details:\n"))
			for key, value := range singleResult.Details {
				summary.WriteString(fmt.Sprintf("    %s: %v\n", key, value))
			}
		}
	}

	return summary.String(), nil
}

// GetTradeSignal возвращает торговый сигнал для использования в торговых системах
func (ca *CryptoAnalyzer) GetTradeSignal(response *AnalysisResponse) (*TradeSignal, error) {
	var signal TradeSignal

	signal.Symbol = response.Symbol
	signal.Timeframe = response.Timeframe
	signal.Timestamp = response.Timestamp

	if strings.Contains(string(response.Result), "overall") {
		// Используем общий результат
		overallResult, err := ca.ParseOverallResult(response)
		if err != nil {
			return nil, err
		}

		signal.Direction = overallResult.Overall.Direction
		signal.Confidence = overallResult.Overall.Confidence
		signal.TakeProfit = overallResult.Overall.TakeProfit
		signal.StopLoss = overallResult.Overall.StopLoss
		signal.CurrentPrice = overallResult.Overall.CurrentPrice
		signal.Strategy = "ALL"

		// Определяем силу сигнала на основе вероятности
		if overallResult.Overall.Probabilities.Bullish > 60 {
			signal.Strength = "STRONG"
		} else if overallResult.Overall.Probabilities.Bullish > 40 {
			signal.Strength = "MODERATE"
		} else {
			signal.Strength = "WEAK"
		}

	} else {
		// Используем результат одной стратегии
		singleResult, err := ca.ParseSingleStrategy(response)
		if err != nil {
			return nil, err
		}

		signal.Direction = singleResult.Direction
		signal.Confidence = singleResult.Confidence
		signal.TakeProfit = singleResult.TakeProfit
		signal.StopLoss = singleResult.StopLoss
		signal.CurrentPrice = singleResult.CurrentPrice
		signal.Strategy = singleResult.Strategy

		// Определяем силу сигнала на основе confidence
		switch singleResult.Confidence {
		case "HIGH":
			signal.Strength = "STRONG"
		case "MEDIUM":
			signal.Strength = "MODERATE"
		default:
			signal.Strength = "WEAK"
		}
	}

	return &signal, nil
}

// TradeSignal структура для торговых сигналов
type TradeSignal struct {
	Symbol       string  `json:"symbol"`
	Timeframe    string  `json:"timeframe"`
	Timestamp    string  `json:"timestamp"`
	Direction    string  `json:"direction"`
	Confidence   string  `json:"confidence"`
	Strength     string  `json:"strength"`
	Strategy     string  `json:"strategy"`
	CurrentPrice float64 `json:"current_price"`
	TakeProfit   float64 `json:"take_profit"`
	StopLoss     float64 `json:"stop_loss"`
	RiskReward   float64 `json:"risk_reward"`
}

// CalculateRiskReward рассчитывает соотношение риск/прибыль
func (ts *TradeSignal) CalculateRiskReward() {
	if ts.StopLoss > 0 && ts.CurrentPrice > 0 {
		risk := abs(ts.CurrentPrice - ts.StopLoss)
		reward := abs(ts.TakeProfit - ts.CurrentPrice)
		if risk > 0 {
			ts.RiskReward = reward / risk
		}
	}
}

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

// Пример использования
func main() {
	// Путь к Python скрипту (можно передавать как аргумент)
	pythonScript := "./crypto_analyzer.py"

	// Создаем анализатор
	analyzer := NewCryptoAnalyzer(pythonScript)

	// Пример 1: Анализ одной стратегии
	fmt.Println("=== Пример 1: Анализ MA стратегии ===")
	response1, err := analyzer.Analyze("BTC", "5", "MA")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	summary1, err := analyzer.GetAnalysisSummary(response1)
	if err != nil {
		fmt.Printf("Error getting summary: %v\n", err)
	} else {
		fmt.Println(summary1)
	}

	// Получаем торговый сигнал
	signal1, err := analyzer.GetTradeSignal(response1)
	if err != nil {
		fmt.Printf("Error getting trade signal: %v\n", err)
	} else {
		signal1.CalculateRiskReward()
		fmt.Printf("\nTrade Signal:\n")
		fmt.Printf("  %s: %s (Strength: %s, Confidence: %s)\n",
			signal1.Symbol, signal1.Direction, signal1.Strength, signal1.Confidence)
		fmt.Printf("  Price: $%.2f, TP: $%.2f, SL: $%.2f\n",
			signal1.CurrentPrice, signal1.TakeProfit, signal1.StopLoss)
		fmt.Printf("  Risk/Reward: 1:%.2f\n", signal1.RiskReward)
	}

	// Пример 2: Анализ всех стратегий
	fmt.Println("\n=== Пример 2: Анализ ALL стратегий ===")
	response2, err := analyzer.Analyze("ETH", "D", "ALL")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	summary2, err := analyzer.GetAnalysisSummary(response2)
	if err != nil {
		fmt.Printf("Error getting summary: %v\n", err)
	} else {
		fmt.Println(summary2)
	}

	// Получаем торговый сигнал для ALL
	signal2, err := analyzer.GetTradeSignal(response2)
	if err != nil {
		fmt.Printf("Error getting trade signal: %v\n", err)
	} else {
		signal2.CalculateRiskReward()
		fmt.Printf("\nTrade Signal (ALL strategies):\n")
		fmt.Printf("  %s: %s (Strength: %s, Confidence: %s)\n",
			signal2.Symbol, signal2.Direction, signal2.Strength, signal2.Confidence)
		fmt.Printf("  Price: $%.2f, TP: $%.2f, SL: $%.2f\n",
			signal2.CurrentPrice, signal2.TakeProfit, signal2.StopLoss)
		fmt.Printf("  Risk/Reward: 1:%.2f\n", signal2.RiskReward)
	}

	// Пример 3: Сохранение результатов в JSON файл
	fmt.Println("\n=== Пример 3: Сохранение результатов ===")
	saveResultsToFile(response1, "btc_analysis.json")
	saveResultsToFile(response2, "eth_analysis.json")

	// Пример 4: Пакетный анализ нескольких криптовалют
	fmt.Println("\n=== Пример 4: Пакетный анализ ===")
	analyzeMultipleCryptos(analyzer)
}

// Функция для сохранения результатов в файл
func saveResultsToFile(response *AnalysisResponse, filename string) {
	data, err := json.MarshalIndent(response, "", "  ")
	if err != nil {
		fmt.Printf("Error marshaling response: %v\n", err)
		return
	}

	if err := os.WriteFile(filename, data, 0644); err != nil {
		fmt.Printf("Error writing file %s: %v\n", filename, err)
		return
	}

	fmt.Printf("Results saved to %s\n", filename)
}

// Функция для пакетного анализа нескольких криптовалют
func analyzeMultipleCryptos(analyzer *CryptoAnalyzer) {
	cryptos := []struct {
		symbol    string
		timeframe string
		strategy  string
	}{
		{"BTC", "5", "ALL"},
		{"ETH", "15", "RSI_MACD"},
		{"ADA", "60", "BREAKOUT"},
		{"SOL", "D", "MA"},
	}

	for _, crypto := range cryptos {
		fmt.Printf("\nAnalyzing %s (%s, %s)...\n",
			crypto.symbol, crypto.timeframe, crypto.strategy)

		response, err := analyzer.Analyze(crypto.symbol, crypto.timeframe, crypto.strategy)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}

		signal, err := analyzer.GetTradeSignal(response)
		if err != nil {
			fmt.Printf("  Error getting signal: %v\n", err)
			continue
		}

		signal.CalculateRiskReward()
		fmt.Printf("  Signal: %s (Confidence: %s, Strength: %s)\n",
			signal.Direction, signal.Confidence, signal.Strength)
		fmt.Printf("  Price: $%.2f, TP: $%.2f, SL: $%.2f, R/R: 1:%.2f\n",
			signal.CurrentPrice, signal.TakeProfit, signal.StopLoss, signal.RiskReward)

		// Принимаем решение на основе сигнала
		decision := makeTradingDecision(signal)
		fmt.Printf("  Decision: %s\n", decision)
	}
}

// Функция для принятия торгового решения
func makeTradingDecision(signal *TradeSignal) string {
	if signal.Direction == "NO_DATA" || signal.Confidence == "LOW" {
		return "HOLD (no clear signal)"
	}

	// Проверяем соотношение риск/прибыль
	if signal.RiskReward < 1.5 {
		return "HOLD (poor risk/reward)"
	}

	// Принимаем решение на основе силы сигнала
	switch signal.Strength {
	case "STRONG":
		if signal.Direction == "BULLISH" {
			return "BUY (strong bullish signal)"
		} else if signal.Direction == "BEARISH" {
			return "SELL/SHORT (strong bearish signal)"
		}
	case "MODERATE":
		if signal.Direction == "BULLISH" {
			return "CONSIDER BUY (moderate bullish signal)"
		} else if signal.Direction == "BEARISH" {
			return "CONSIDER SELL (moderate bearish signal)"
		}
	case "WEAK":
		return "HOLD (weak signal)"
	}

	return "HOLD (neutral signal)"
}

// Утилитарные функции

// ValidateSymbol проверяет валидность символа криптовалюты
func ValidateSymbol(symbol string) bool {
	if len(symbol) < 2 || len(symbol) > 10 {
		return false
	}

	// Простая проверка - символ должен состоять из букв
	for _, char := range symbol {
		if (char < 'A' || char > 'Z') && (char < 'a' || char > 'z') {
			return false
		}
	}

	return true
}

// ValidateTimeframe проверяет валидность таймфрейма
func ValidateTimeframe(timeframe string) bool {
	validTimeframes := map[string]bool{
		"1": true, "5": true, "15": true, "60": true,
		"D": true, "W": true, "M": true,
	}
	return validTimeframes[timeframe]
}

// ValidateStrategy проверяет валидность стратегии
func ValidateStrategy(strategy string) bool {
	validStrategies := map[string]bool{
		"RSI_MACD": true, "MA": true, "BB": true,
		"STOCH_EMA": true, "SAR_ADX": true, "BREAKOUT": true,
		"ALL": true,
	}
	return validStrategies[strategy]
}

// GetAvailableStrategies возвращает список доступных стратегий
func GetAvailableStrategies() []string {
	return []string{
		"RSI_MACD", "MA", "BB", "STOCH_EMA", "SAR_ADX", "BREAKOUT", "ALL",
	}
}

// GetAvailableTimeframes возвращает список доступных таймфреймов
func GetAvailableTimeframes() []string {
	return []string{"1", "5", "15", "60", "D", "W", "M"}
}

// AnalysisSettings структура для хранения настроек анализа
type AnalysisSettings struct {
	Timeframe     string   `json:"timeframe"`
	Strategy      string   `json:"strategy"`
	FrequencyType string   `json:"frequency_type"`
	IntervalValue int      `json:"interval_value"`
	IntervalUnit  string   `json:"interval_unit"`
	SpecificTimes []string `json:"specific_times,omitempty"`
}

// AnalysisStatus структура для статуса анализа
type AnalysisStatus struct {
	Active   bool              `json:"active"`
	Settings *AnalysisSettings `json:"settings,omitempty"`
	Started  time.Time         `json:"started,omitempty"`
}

func StartAnalyze(w http.ResponseWriter, r *http.Request) {
	for {
		time.Sleep(30 * time.Second)
		type Settings struct {
			Timeframe     string `json:"timeframe"`
			Strategies    string `json:"strategies"`
			FrequencyType string `json:"frequency_type"`
			IntervalValue string `json:"interval_value"`
			IntervalUnit  string `json:"interval_unit"`
			SpecificTime  string `json:"specific_time"`
		}
		cookie, _ := r.Cookie("analyzer_settings")
		cookieStr := cookie.Value
		// Декодируем
		decoded, _ := url.QueryUnescape(cookieStr)

		// Парсим
		var s Settings
		json.Unmarshal([]byte(decoded), &s)

		// Выводим
		fmt.Printf("JSON: %s\n\n", decoded)
		fmt.Printf("Структура: %+v\n\n", s)

		// Разделяем стратегии
		strategies := strings.Split(strings.Trim(s.Strategies, `"`), ",")
		fmt.Println("Стратегии:")
		for i, strat := range strategies {
			fmt.Printf("  %d. %s\n", i+1, strat)
		}
		cookie_em, _ := r.Cookie("user")
		cookie_email := cookie_em.Value
		currency := base.SelectCurrencyPreference(database.MySQLConnect(), cookie_email)
		currency_mass := strings.Split(currency[:len(currency)-1], ",")
		for i, j := range currency_mass {
			callWithCookieSettings(j, s.Timeframe, s.Strategies, cookie_email)
			if len(currency_mass)-i == 1 {
				break
			}
		}

	}
	// Извлечение данных из куки analysis_settings

}

// Простой вызов вашего Python скрипта из Go
func callPythonAnalyzer() {
	// Подготовка команды
	cmd := exec.Command("python3", "/Users/reznicenkodaniivsevolodovic/GolandProjects/Chase-Profit/python_scripts/analyze_script.py", "BTC", "5", "ALL")

	// Запуск и получение результата
	output, err := cmd.CombinedOutput()
	if err != nil {
		log.Printf("Ошибка запуска Python скрипта: %v", err)
		return
	}

	// Парсинг JSON результата
	var result map[string]interface{}
	if err := json.Unmarshal(output, &result); err != nil {
		log.Printf("Ошибка парсинга JSON: %v", err)
		return
	}

	// Использование результатов
	fmt.Printf("Результат анализа: %+v\n", result)
}

// Вызов с параметрами из cookie
func callWithCookieSettings(symbol, timeframe, strategies, email string) {
	strategyToUse := "ALL"
	if !strings.Contains(strategies, ",") && strings.TrimSpace(strategies) != "ALL" {
		strategyToUse = strings.TrimSpace(strategies)
	}

	cmd := exec.Command("python3", "/Users/reznicenkodaniivsevolodovic/GolandProjects/Chase-Profit/python_scripts/analyze_script.py",
		symbol, timeframe, strategyToUse)

	output, err := cmd.Output()
	if err != nil {
		log.Printf("Ошибка: %v", err)
		return
	}
	//quickAlert(symbol, timeframe, string(output))
	fmt.Println(string(output))
	get_info(string(output), email)
}

type Response struct {
	Success    bool   `json:"success"`
	Symbol     string `json:"symbol"`
	Timeframe  string `json:"timeframe"`
	Timestamp  string `json:"timestamp"`
	DataPoints int    `json:"data_points"`
	Result     Result `json:"result"`
}

type Result struct {
	Overall    Overall             `json:"overall"`
	Strategies map[string]Strategy `json:"strategies"`
}

type Overall struct {
	Direction     string        `json:"direction"`
	Confidence    string        `json:"confidence"`
	TakeProfit    float64       `json:"take_profit"`
	StopLoss      float64       `json:"stop_loss"`
	CurrentPrice  float64       `json:"current_price"`
	Probabilities Probabilities `json:"probabilities"`
}

type Probabilities struct {
	Bullish float64 `json:"bullish"`
	Bearish float64 `json:"bearish"`
	Neutral float64 `json:"neutral"`
}

type Strategy struct {
	Direction  string  `json:"direction"`
	Confidence string  `json:"confidence"`
	TakeProfit float64 `json:"take_profit"`
	StopLoss   float64 `json:"stop_loss"`
}

func get_info(jsonStr string, email string) {
	// Исходная JSON строка
	// Преобразование JSON строки в структуру
	var response Response
	err := json.Unmarshal([]byte(jsonStr), &response)
	if err != nil {
		log.Fatal("Ошибка парсинга JSON:", err)
	}

	// Создание массива (среза) стратегий
	strategiesArray := make([]Strategy, 0, len(response.Result.Strategies))

	// Переменные для подсчета средних значений
	var totalTakeProfit, totalStopLoss float64
	var strategyCount int

	for name, strategy := range response.Result.Strategies {
		// Можно добавить имя стратегии в структуру, если нужно
		fmt.Printf("Стратегия: %s\n", name)
		fmt.Printf("  Направление: %s\n", strategy.Direction)
		fmt.Printf("  Уверенность: %s\n", strategy.Confidence)
		fmt.Printf("  Take Profit: %.2f\n", strategy.TakeProfit)
		fmt.Printf("  Stop Loss: %.2f\n\n", strategy.StopLoss)

		strategiesArray = append(strategiesArray, strategy)

		// Суммируем значения для подсчета среднего
		totalTakeProfit += strategy.TakeProfit
		totalStopLoss += strategy.StopLoss
		strategyCount++
	}

	// Вычисляем средние значения
	averageTakeProfit := 0.0
	averageStopLoss := 0.0

	if strategyCount > 0 {
		averageTakeProfit = totalTakeProfit / float64(strategyCount)
		averageStopLoss = totalStopLoss / float64(strategyCount)
	}

	// Вывод общей информации
	fmt.Printf("\nОбщая информация:\n")
	fmt.Printf("Символ: %s\n", response.Symbol)
	fmt.Printf("Таймфрейм: %s\n", response.Timeframe)
	fmt.Printf("Текущая цена: %.2f\n", response.Result.Overall.CurrentPrice)
	fmt.Printf("Вероятности - Бычий: %.1f%%, Медвежий: %.1f%%, Нейтральный: %.1f%%\n",
		response.Result.Overall.Probabilities.Bullish,
		response.Result.Overall.Probabilities.Bearish,
		response.Result.Overall.Probabilities.Neutral)

	// Вывод статистики по стратегиям
	//fmt.Printf("\nСтатистика по стратегиям:\n")
	//fmt.Printf("Всего стратегий: %d\n", strategyCount)
	fmt.Printf("Средний Take Profit: %.2f\n", averageTakeProfit)
	fmt.Printf("Средний Stop Loss: %.2f\n", averageStopLoss)

	// Вывод размера массива
	//fmt.Printf("\nВсего стратегий в массиве: %d\n", len(strategiesArray))

	// Пример работы с массивом
	if len(strategiesArray) > 0 {
		//fmt.Printf("\nПервая стратегия в массиве: %+v\n", strategiesArray[0])
	}

	fmt.Printf("Вероятность бычьего сценария: %.1f%%\n", response.Result.Overall.Probabilities.Bullish)
	tp := float64(response.Result.Overall.TakeProfit)
	sl := float64(response.Result.Overall.StopLoss)
	bull := int(response.Result.Overall.Probabilities.Bullish)
	bear := int(response.Result.Overall.Probabilities.Bearish)
	alert := ""
	sub := false
	if bull >= 80 {
		alert = "📈 БЫЧИЙ | " + response.Symbol + " | Вероятность: " + fmt.Sprint(bull) + " | ЦЕНА: " + fmt.Sprint(response.Result.Overall.CurrentPrice) + " | TP: " + fmt.Sprint(tp) + " | SL: " + fmt.Sprint(sl)
		sub = true
	}
	if bear >= 80 {
		alert = "📉 МЕДВЕЖИЙ | " + response.Symbol + " | Вероятность: " + fmt.Sprint(bear) + " | ЦЕНА: " + fmt.Sprint(response.Result.Overall.CurrentPrice) + " | TP: " + fmt.Sprint(tp) + " | SL: " + fmt.Sprint(sl)
		sub = true
	}
	if sub {

		UpdateJson(alert, email)
	}

}

type Alert struct {
	ID      int    `json:"id"`
	UserID  string `json:"userId"`
	Title   string `json:"title"`
	Message string `json:"message"`
	Type    string `json:"type"`
	Silent  bool   `json:"silent"`
}

type AlertsData struct {
	Alerts []Alert `json:"alerts"`
}

func getNextID(filename string) (int, error) {
	// Если файл не существует, начинаем с 1000
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		return 1000, nil
	}

	// Читаем существующий файл
	file, err := os.ReadFile(filename)
	if err != nil {
		return 1000, fmt.Errorf("ошибка чтения файла: %v", err)
	}

	var data AlertsData
	err = json.Unmarshal(file, &data)
	if err != nil {
		return 1000, fmt.Errorf("ошибка парсинга JSON: %v", err)
	}

	// Находим максимальный ID
	maxID := 1000
	for _, alert := range data.Alerts {
		if alert.ID > maxID {
			maxID = alert.ID
		}
	}

	return maxID + 1, nil
}

// readExistingAlerts читает существующие алерты из файла
func readExistingAlerts(filename string) (AlertsData, error) {
	var data AlertsData

	// Если файл не существует, возвращаем пустую структуру
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		return data, nil
	}

	file, err := os.ReadFile(filename)
	if err != nil {
		return data, fmt.Errorf("ошибка чтения файла: %v", err)
	}

	err = json.Unmarshal(file, &data)
	if err != nil {
		return data, fmt.Errorf("ошибка парсинга JSON: %v", err)
	}

	return data, nil
}

func UpdateJson(message string, email string) {
	filename := "/Users/reznicenkodaniivsevolodovic/GolandProjects/Chase-Profit/resources/alert.json"

	// Читаем существующие алерты
	existingData, err := readExistingAlerts(filename)
	if err != nil {
		fmt.Printf("Предупреждение: %v\n", err)
		fmt.Println("Будет создан новый файл")
	}

	// Получаем следующий доступный ID
	nextID, err := getNextID(filename)
	if err != nil {
		fmt.Printf("Предупреждение: %v\n", err)
		fmt.Println("Начинаем ID с 1000")
		nextID = 1000
	}

	fmt.Printf("Следующий доступный ID: %d\n", nextID)
	fmt.Printf("Существует %d оповещений в файле\n\n", len(existingData.Alerts))

	// Получение данных от пользователя
	newAlerts := []Alert{}

	for {
		currentID := nextID

		// Создание нового оповещения
		alert := Alert{
			ID:      currentID,
			UserID:  email,
			Title:   "New Alerts!",
			Message: message,
			Type:    "alerts",
			Silent:  false,
		}

		newAlerts = append(newAlerts, alert)
		nextID++ // увеличиваем ID для следующего алерта

		// Проверка, хочет ли пользователь добавить еще оповещения

		break
		fmt.Println()
	}

	// Объединяем существующие и новые алерты
	allAlerts := append(existingData.Alerts, newAlerts...)

	// Создание структуры данных
	data := AlertsData{
		Alerts: allAlerts,
	}

	// Преобразование в JSON с красивым форматированием
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		fmt.Printf("Ошибка при создании JSON: %v\n", err)
		return
	}

	// Запись в файл
	err = os.WriteFile(filename, jsonData, 0644)
	if err != nil {
		fmt.Printf("Ошибка при записи в файл: %v\n", err)
		return
	}

	fmt.Printf("\n✅ Данные успешно записаны в файл '%s'\n", filename)
	fmt.Printf("   Добавлено новых оповещений: %d\n", len(newAlerts))
	fmt.Printf("   Всего оповещений в файле: %d\n", len(allAlerts))

	// Вывод только новых алертов для проверки
	if len(newAlerts) > 0 {
		fmt.Println("\n📝 Добавленные оповещения:")
		for _, alert := range newAlerts {
			fmt.Printf("   ID: %d, User: %s, Title: %s\n", alert.ID, alert.UserID, alert.Title)
		}
	}
}

// readLine читает строку с пробелами
func readLine() (string, error) {
	var input string
	_, err := fmt.Scanln(&input)
	return input, err
}
