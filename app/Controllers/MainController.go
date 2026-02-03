package Controllers

import (
	"Chase-Profit/config"
	"fmt"
	"net/http"
	"text/template"
)

func ShowMainPage(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	tmpl, err := template.ParseFiles(path+"templates/header.html", path+"templates/alerts.html")
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
		go StartAnalyze(w, r)
	}
}

func ShowAboutUsPage(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	tmpl, err := template.ParseFiles(path+"about_us.html", path+"templates/alerts.html")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	err = tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
	get_cookie, _ := r.Cookie("analysis")
	email := get_cookie.Value
	if email == "running" {
		fmt.Println("analysis is running")
		go StartAnalyze(w, r)

	}
}
