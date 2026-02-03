package Controllers

import (
	"Chase-Profit/app/Controllers/base"
	"Chase-Profit/app/Models"
	"Chase-Profit/config"
	"Chase-Profit/database"
	"fmt"
	"golang.org/x/crypto/bcrypt"
	"html/template"
	"net/http"
)

func ShowAuthPage(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	// Парсинг HTML шаблона
	tmpl, err := template.ParseFiles(path + "auth.html")
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

func ShowRegisterPage(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Title string
	}{
		Title: "Мой сайт",
	}
	path := config.GetAbsolutePath() + "/resources/views/"
	// Парсинг HTML шаблона
	tmpl, err := template.ParseFiles(path + "register.html")
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

func AuthProcess(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		// Парсим форму
		err := r.ParseForm()
		if err != nil {
			http.Error(w, "Error parsing form", http.StatusBadRequest)
		}

		// Получаем данные из формы
		loginData := Models.User{
			Email:         r.FormValue("email"),
			Password_hash: r.FormValue("password"),
		}

		// Валидация
		if loginData.Email == "" || loginData.Password_hash == "" {
			http.Error(w, "Email and password are required", http.StatusBadRequest)
		}
		// Здесь должна быть логика аутентификации
		//fmt.Printf("Login attempt: %+v\n", loginData)

		// Редирект после успешной авторизации
		pass_in_base := base.ChekUserAccount(database.MySQLConnect(), loginData)
		fmt.Println(pass_in_base)
		fmt.Println(loginData.Password_hash)
		if bcrypt.CompareHashAndPassword([]byte(pass_in_base), []byte(loginData.Password_hash)) == nil {
			http.SetCookie(w, &http.Cookie{
				Name:  "user",
				Value: loginData.Email,
				Path:  "/",
			})
			base.UpdateLastLogin(database.MySQLConnect(), loginData.Email)
			http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
		}
	}

}

func RegisterProcess(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		// Парсим форму
		err := r.ParseForm()
		if err != nil {
			http.Error(w, "Error parsing form", http.StatusBadRequest)
		}

		// Получаем данные из формы
		RegisterData := Models.User{
			Password_hash: base.HashPassword(r.FormValue("password")),
			Email:         r.FormValue("email"),
			Username:      r.FormValue("email"),
			Date_of_birth: r.FormValue("date_of_birth"),
			First_name:    r.FormValue("first_name"),
			Last_name:     r.FormValue("last_name"),
			Phone:         r.FormValue("phone_number"),
		}
		// Валидация
		if RegisterData.Username == "" || RegisterData.Password_hash == "" {
			http.Error(w, "Email and password are required", http.StatusBadRequest)
			return
		}

		// Здесь должна быть логика аутентификации
		//fmt.Printf("Login attempt: %+v\n", RegisterData)
		base.CreateUserAccount(database.MySQLConnect(), RegisterData)
		base.UpdateLastLogin(database.MySQLConnect(), RegisterData.Email)
		// Редирект после успешной авторизации
		http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
		return
	}
}
