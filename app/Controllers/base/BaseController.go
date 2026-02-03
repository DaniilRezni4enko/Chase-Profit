package base

import (
	"Chase-Profit/app/Models"
	"database/sql"
	"fmt"
)

func CreateUserAccount(db *sql.DB, user Models.User) error {
	fmt.Println("Creating user account...")

	query := `INSERT INTO users (username, email, phone, password_hash, two_factor_enabled, first_name, last_name, date_of_birth) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`

	result, err := db.Exec(query,
		user.Username,
		user.Email,
		user.Phone,
		user.Password_hash,
		false,
		user.First_name,
		user.Last_name,
		user.Date_of_birth,
	)

	if err != nil {
		fmt.Printf("Database error: %v\n", err)
		return err
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		fmt.Printf("Error getting rows affected: %v\n", err)
		return err
	}

	lastID, err := result.LastInsertId()
	if err != nil {
		fmt.Printf("Error getting last insert ID: %v\n", err)
	} else {
		fmt.Printf("User created successfully with ID: %d\n", lastID)
	}

	fmt.Printf("Rows affected: %d\n", rowsAffected)
	fmt.Printf("User data: %+v\n", user)

	return nil
}

func ChekUserAccount(db *sql.DB, user Models.User) string {
	//fmt.Println("Creating user account...")

	query := `SELECT password_hash FROM users WHERE username = ?`
	var password_in_base string
	fmt.Println(user.Email)
	err := db.QueryRow(query, user.Email).Scan(&password_in_base)
	if err != nil {
		return "error"
	}
	return password_in_base
}

func SelectUsername(db *sql.DB, user Models.User) string {
	query := `SELECT username FROM users WHERE email = ?`
	var username_in_base string
	err := db.QueryRow(query, user.Username).Scan(&username_in_base)
	if err != nil {
		return "error"
	}
	return username_in_base
}

func SelectIDFromEmail(db *sql.DB, email string) int {
	query := `SELECT id FROM users WHERE email = ?`
	var id int
	err := db.QueryRow(query, email).Scan(&id)
	if err != nil {
		return 0
	}
	return id
}

func SelectUserDeal(db *sql.DB, email string) string {
	id := SelectIDFromEmail(db, email)
	var deals_id string
	query := `SELECT id FROM crypto_deals WHERE user_id = ?`
	err := db.QueryRow(query, id).Scan(&deals_id)
	if err != nil {
		return "error"
	}
	return deals_id
}

func UpdateLastLogin(db *sql.DB, email string) {
	query := `UPDATE users SET last_login = NOW() WHERE email = ?`
	_, err := db.Exec(query, email)
	if err != nil {
	}
}

func GetUserAlert(db *sql.DB, user_id int) ([]int, error) {
	query := `SELECT id FROM alerts WHERE user_id = ?`
	rows, err := db.Query(query, user_id)
	if err != nil {
		return nil, nil
	}
	defer rows.Close()
	var alertIDs []int
	for rows.Next() {
		var id int
		if err := rows.Scan(&id); err != nil {
			return nil, nil
		}
		alertIDs = append(alertIDs, id)
	}
	if err := rows.Err(); err != nil {
		return nil, nil
	}
	return alertIDs, nil
}

func CreateUserAlerts(db *sql.DB, alert Models.Alert) error {
	fmt.Println("Creating user account...")

	query := `INSERT INTO alerts (user_id, created_at, text, currency, strategy) VALUES (?, ?, ?, ?, ?)`

	result, err := db.Exec(query,
		alert.UserID,
		alert.CreatedAt,
		alert.Text,
		alert.Currency,
		alert.Strategy,
	)
	if err != nil {
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		fmt.Printf("Error getting rows affected: %v\n", err)
		return err
	}

	lastID, err := result.LastInsertId()
	if err != nil {
		fmt.Printf("Error getting last insert ID: %v\n", err)
	} else {
		fmt.Printf("User created successfully with ID: %d\n", lastID)
	}

	fmt.Printf("Rows affected: %d\n", rowsAffected)
	fmt.Printf("User data: %+v\n", alert)
	return err
}

func UpdateCurrencyPreference(db *sql.DB, email, cryptoStr string) error {
	// Подключение к MySQL
	// Для MySQL используем знаки ? вместо $1, $2
	fmt.Println(cryptoStr)
	query := "UPDATE users SET currency_preference = ? WHERE email = ?"
	result, err := db.Exec(query, cryptoStr, email)
	if err != nil {
		return err
	}
	fmt.Println("qwqwqwqwqwqwqwqwqdfdfdfdf")
	rowsAffected, _ := result.RowsAffected()
	fmt.Printf("Обновлено %d записей\n", rowsAffected)
	return nil
}

func SelectCurrencyPreference(db *sql.DB, email string) string {
	var currency_preference string
	query := `SELECT currency_preference FROM users WHERE email = ?`
	err := db.QueryRow(query, email).Scan(&currency_preference)
	if err != nil {
	}
	fmt.Println(currency_preference)
	return currency_preference
}
