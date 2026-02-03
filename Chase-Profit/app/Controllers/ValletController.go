package Controllers

import (
	"Chase-Profit/app/Controllers/base"
	"Chase-Profit/config"
	"Chase-Profit/database"
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"time"
)

func ShowValletChangeStr(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	// Парсинг HTML шаблона
	tmpl, err := template.ParseFiles(path + "finances.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Выполнение шаблона
	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

type CryptoSubmission struct {
	Timestamp       time.Time `json:"timestamp"`
	UserAgent       string    `json:"userAgent"`
	TotalSelected   int       `json:"totalSelected"`
	SelectedCryptos []struct {
		Symbol    string  `json:"symbol"`
		Name      string  `json:"name"`
		Price     float64 `json:"price"`
		Change    float64 `json:"change"`
		VolumeUSD float64 `json:"volumeUsd"`
	} `json:"selectedCryptos"`
}

func HandleCryptoForm(w http.ResponseWriter, r *http.Request) {
	// Только POST запросы
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	fmt.Println("qwqwqwqwqwqwqwqw")

	// Декодируем JSON
	var data CryptoSubmission
	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()
	fmt.Println("weeeeee")
	// Валидация
	if len(data.SelectedCryptos) == 0 {
		http.Error(w, "No cryptocurrencies selected", http.StatusBadRequest)
		return
	}

	// Устанавливаем timestamp
	data.Timestamp = time.Now()

	// Ваша бизнес-логика здесь
	// Например: сохранение в БД, отправка уведомлений и т.д.
	processData(data, w, r)
	fmt.Println(data)

	// Отправляем успешный ответ
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Data received successfully",
		"count":   len(data.SelectedCryptos),
	})
}

func processData(data CryptoSubmission, w http.ResponseWriter, r *http.Request) {
	// Пример обработки данных
	var crypto_str string
	for _, crypto := range data.SelectedCryptos {
		// Делайте что-то с каждой выбранной криптовалютой
		_ = crypto // Используйте crypto данные
		fmt.Println(crypto.Name)
		crypto_str += crypto.Symbol + ","
	}
	get_cookie, _ := r.Cookie("user")
	email := get_cookie.Value
	fmt.Println("get_cookie:", get_cookie)
	base.UpdateCurrencyPreference(database.MySQLConnect(), email, crypto_str)
}
