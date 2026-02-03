package routes

import (
	"Chase-Profit/app/Controllers"
	"net/http"
)

func Routes() {
	//path := config.GetAbsolutePath() + "/resources/views/"
	fs := http.FileServer(http.Dir("./resources"))
	http.Handle("/resources/", http.StripPrefix("/resources/", fs))
	http.HandleFunc("/submit-cryptos", Controllers.HandleCryptoForm)

	http.HandleFunc("/", Controllers.ShowMainPage)

	http.HandleFunc("/auth", Controllers.ShowAuthPage)

	http.HandleFunc("/about_us", Controllers.ShowAboutUsPage)

	http.HandleFunc("/register", Controllers.ShowRegisterPage)

	http.HandleFunc("/auth-process", Controllers.AuthProcess)

	http.HandleFunc("/register-process", Controllers.RegisterProcess)

	http.HandleFunc("/vallets", Controllers.ShowValletChangeStr)

	http.HandleFunc("/deals", Controllers.ShowUserDeals)

	http.HandleFunc("/trades", Controllers.ShowUserTrade)

	http.HandleFunc("/alerts", Controllers.ShowAllAlerts)

	http.HandleFunc("/profile", Controllers.ShowUserProfile)

	http.HandleFunc("/user_alerts", Controllers.ShowUserAlerts)

	http.HandleFunc("/analyze_settings", Controllers.ShowAnalyzeSettings)

}
