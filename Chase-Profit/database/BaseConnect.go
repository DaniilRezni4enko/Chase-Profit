package database

import (
	"database/sql"
	_ "github.com/go-sql-driver/mysql"
)

func MySQLConnect() *sql.DB {
	// Параметры подключения
	connStr := "root:sKSxQiKF81q-_3kf@tcp(localhost:3306)/chase_profit"
	db, err := sql.Open("mysql", connStr)
	if err != nil {
		//log.Fatal(err)
		//return false
	}
	//defer db.Close()

	err = db.Ping()
	//if err != nil {
	//	//log.Fatal(err)
	//	return false
	//}
	return db
}
