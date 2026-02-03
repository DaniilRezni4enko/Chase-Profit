package main

import (
	"Chase-Profit/app/Error_processing"
	"Chase-Profit/database"
	"Chase-Profit/routes"
	"fmt"
	"net/http"
)

func main() {
	if database.MySQLConnect() == nil {
		Error_processing.ErrorProc("404")
	} else {
		fmt.Println("qwqwqw")
		routes.Routes()
	}
	http.ListenAndServe(":80", nil)
}

func forAllUrls(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// ВАША ФУНКЦИЯ, КОТОРАЯ ВЫПОЛНЯЕТСЯ ДЛЯ ВСЕХ URL
		fmt.Println("erer")
		// Обязательно вызываем следующий обработчик
		next.ServeHTTP(w, r)
	})
}
