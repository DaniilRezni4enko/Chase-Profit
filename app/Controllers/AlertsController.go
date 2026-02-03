package Controllers

import (
	//"Chase-Profit/app/Controllers/base"
	//"Chase-Profit/database"
	//"fmt"
	//"time"

	"Chase-Profit/app/Controllers/base"
	"Chase-Profit/database"
	"fmt"
	"time"

	//"Chase-Profit/app/Controllers/base"
	"Chase-Profit/config"
	//"Chase-Profit/database"
	"html/template"
	"net/http"
)

func ShowAllAlerts(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	// Парсинг HTML шаблона
	tmpl, err := template.ParseFiles(path + "alerts.html")
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

func AlertProcessing(w http.ResponseWriter, r *http.Request) {
	get_cookie, _ := r.Cookie("user")
	email := get_cookie.Value
	if email != " " {
		user_id := base.SelectIDFromEmail(database.MySQLConnect(), email)
		go ProcessAlertsSelect(w, r, user_id)
	}
}

func ProcessAlertsSelect(w http.ResponseWriter, r *http.Request, user_id int) []int {
	for {
		time.Sleep(30 * time.Second)
		user_alerts, err := base.GetUserAlert(database.MySQLConnect(), user_id)
		if err != nil {
		}
		fmt.Println(user_alerts)
		for key, value := range user_alerts {
			InsertAlerts(key, value)
		}
	}
}

func InsertAlerts(key int, alerts_id int) {

}

func ShowUserAlerts(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	// Парсинг HTML шаблона
	tmpl, err := template.ParseFiles(path + "user_alerts.html")
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
