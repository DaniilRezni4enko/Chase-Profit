package Controllers

import (
	"Chase-Profit/app/Controllers/base"
	"Chase-Profit/database"
	"fmt"
	"net/http"
)

func ShowUserDeals(w http.ResponseWriter, r *http.Request) {
	get_cookie, _ := r.Cookie("user")
	email := get_cookie.Value
	id_deals := base.SelectUserDeal(database.MySQLConnect(), email)
	fmt.Println(id_deals, "qw")
	//data := struct {
	//	Title string
	//}{
	//	Title: "Мой сайт",
	//}
	//path := config.GetAbsolutePath() + "/resources/views/"
	//// Парсинг HTML шаблона
	//tmpl, err := template.ParseFiles(path + "finances.html")
	//if err != nil {
	//	http.Error(w, err.Error(), http.StatusInternalServerError)
	//	return
	//}
	//
	//// Выполнение шаблона
	//err = tmpl.Execute(w, data)
	//if err != nil {
	//	http.Error(w, err.Error(), http.StatusInternalServerError)
	//}

}
