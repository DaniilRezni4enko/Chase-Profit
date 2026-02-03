package routes

import (
	"Chase-Profit/config"
	"html/template"
	"net/http"
)

func ErrorRoutes() {
	path := config.GetAbsolutePath() + "/resources/views/error_print/"
	http.HandleFunc("/error_404", func(w http.ResponseWriter, r *http.Request) {
		tpl := template.Must(template.ParseFiles(path + "404.views"))
		tpl.Execute(w, nil)
	})
	http.HandleFunc("/error_db", func(w http.ResponseWriter, r *http.Request) {
		tpl := template.Must(template.ParseFiles(path + "error_db.views"))
		tpl.Execute(w, nil)
	})
}
