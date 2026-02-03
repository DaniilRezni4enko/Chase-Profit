package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"path/filepath"
)

// Структура для алерта
type Alert struct {
	ID      int    `json:"id"`
	UserID  string `json:"userId"`
	Title   string `json:"title"`
	Message string `json:"message"`
	Type    string `json:"type"`
	Silent  bool   `json:"silent"`
}

// Структура для запроса
type UpdateRequest struct {
	AlertID int    `json:"alertId"`
	Silent  bool   `json:"silent"`
	UserID  string `json:"userId"`
}

// Структура для ответа
type UpdateResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// Обработчик обновления поля silent
func HandleUpdateSilent(w http.ResponseWriter, r *http.Request) {
	// Настраиваем CORS
	setupCORS(&w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Читаем тело запроса
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		sendError(w, "Failed to read request body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Парсим JSON запрос
	var req UpdateRequest
	err = json.Unmarshal(body, &req)
	if err != nil {
		sendError(w, "Invalid JSON format", http.StatusBadRequest)
		return
	}

	// Проверяем обязательные поля
	if req.AlertID == 0 {
		sendError(w, "alertId is required", http.StatusBadRequest)
		return
	}

	// Загружаем текущий JSON файл
	alerts, err := loadAlerts()
	if err != nil {
		sendError(w, "Failed to load alerts", http.StatusInternalServerError)
		return
	}

	// Ищем и обновляем алерт
	found := false
	for i := range alerts {
		if alerts[i].ID == req.AlertID {
			// Проверяем userId если указан
			if req.UserID != "" && alerts[i].UserID != req.UserID && alerts[i].UserID != "all" {
				sendError(w, "Alert doesn't belong to this user", http.StatusForbidden)
				return
			}

			alerts[i].Silent = req.Silent
			found = true
			break
		}
	}

	if !found {
		sendError(w, fmt.Sprintf("Alert with ID %d not found", req.AlertID), http.StatusNotFound)
		return
	}

	// Сохраняем обновленный JSON
	err = saveAlerts(alerts)
	if err != nil {
		sendError(w, "Failed to save alerts", http.StatusInternalServerError)
		return
	}

	// Отправляем успешный ответ
	resp := UpdateResponse{
		Success: true,
		Message: fmt.Sprintf("Alert %d updated successfully (silent: %v)", req.AlertID, req.Silent),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)

	fmt.Printf("Updated alert %d: silent=%v\n", req.AlertID, req.Silent)
}

// Обработчик сброса всех silent полей
func HandleResetSilent(w http.ResponseWriter, r *http.Request) {
	setupCORS(&w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Загружаем текущий JSON файл
	alerts, err := loadAlerts()
	if err != nil {
		sendError(w, "Failed to load alerts", http.StatusInternalServerError)
		return
	}

	// Сбрасываем все silent на false
	resetCount := 0
	for i := range alerts {
		if alerts[i].Silent {
			alerts[i].Silent = false
			resetCount++
		}
	}

	// Сохраняем обновленный JSON
	err = saveAlerts(alerts)
	if err != nil {
		sendError(w, "Failed to save alerts", http.StatusInternalServerError)
		return
	}

	// Отправляем успешный ответ
	resp := UpdateResponse{
		Success: true,
		Message: fmt.Sprintf("Reset %d alerts to silent=false", resetCount),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)

	fmt.Printf("Reset %d alerts to silent=false\n", resetCount)
}

// Обработчик получения всех алертов
func HandleGetAlerts(w http.ResponseWriter, r *http.Request) {
	setupCORS(&w, r)

	alerts, err := loadAlerts()
	if err != nil {
		sendError(w, "Failed to load alerts", http.StatusInternalServerError)
		return
	}

	// Структура для ответа
	type AlertsResponse struct {
		Alerts []Alert `json:"alerts"`
	}

	resp := AlertsResponse{Alerts: alerts}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// Вспомогательные функции
func loadAlerts() ([]Alert, error) {
	// Пробуем разные пути к файлу
	possiblePaths := []string{
		"resources/alert.json",
		"./resources/alert.json",
		"alert.json",
		"./alert.json",
	}

	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			data, err := ioutil.ReadFile(path)
			if err != nil {
				return nil, fmt.Errorf("failed to read file %s: %v", path, err)
			}

			var result struct {
				Alerts []Alert `json:"alerts"`
			}

			err = json.Unmarshal(data, &result)
			if err != nil {
				return nil, fmt.Errorf("failed to parse JSON from %s: %v", path, err)
			}

			fmt.Printf("Loaded %d alerts from %s\n", len(result.Alerts), path)
			return result.Alerts, nil
		}
	}

	return nil, fmt.Errorf("alert.json not found in any location")
}

func saveAlerts(alerts []Alert) error {
	// Структура для сохранения
	data := struct {
		Alerts []Alert `json:"alerts"`
	}{
		Alerts: alerts,
	}

	// Преобразуем в JSON
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %v", err)
	}

	// Сохраняем в resources/alert.json
	path := "resources/alert.json"

	// Создаем директорию если её нет
	dir := filepath.Dir(path)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		err = os.MkdirAll(dir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create directory %s: %v", dir, err)
		}
	}

	// Записываем файл
	err = ioutil.WriteFile(path, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write file %s: %v", path, err)
	}

	fmt.Printf("Saved %d alerts to %s\n", len(alerts), path)
	return nil
}

func setupCORS(w *http.ResponseWriter, r *http.Request) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
	(*w).Header().Set("Access-Control-Allow-Headers", "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")
}

func sendError(w http.ResponseWriter, message string, statusCode int) {
	resp := UpdateResponse{
		Success: false,
		Message: message,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(resp)
}
