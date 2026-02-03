package Models

import "time"

type User struct {
	Id                  int       `json:"id"`
	Username            string    `json:"username"`
	Email               string    `json:"email"`
	Phone               string    `json:"phone"`
	Password_hash       string    `json:"password_hash"`
	Two_factor_enabled  bool      `json:"two_factor_enabled"`
	First_name          string    `json:"first_name"`
	Last_name           string    `json:"last_name"`
	Date_of_birth       string    `json:"date_of_birth"`
	Country             string    `json:"country"`
	City                string    `json:"city"`
	Address             string    `json:"address"`
	Timezone            string    `json:"timezone"`
	Currency_preference string    `json:"currency_preference"`
	Selected_currencies string    `json:"selected_currencies"`
	User_deals          string    `json:"user_deals"`
	Api_key             string    `json:"api_key"`
	Api_secret_hash     string    `json:"api_secret_hash"`
	Api_enabled         bool      `json:"api_enabled"`
	Created_at          time.Time `json:"created_at"`
	Updated_at          time.Time `json:"updated_at"`
	Last_login          time.Time `json:"last_login"`
	Email_verified_at   string    `json:"email_verified_at"`
}
