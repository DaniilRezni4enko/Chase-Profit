package Controllers

import (
	"Chase-Profit/config"
	"net/http"
	"text/template"
)

func ShowUserProfile(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	tmpl, err := template.ParseFiles(path+"/profile.html", path+"templates/alerts.html")
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
		go StartAnalyze(w, r)
	}
}
