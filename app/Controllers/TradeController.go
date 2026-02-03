package Controllers

import (
	"Chase-Profit/config"
	"html/template"
	"net/http"
)

func ShowUserTrade(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	tmpl, err := template.ParseFiles(path + "trades.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
