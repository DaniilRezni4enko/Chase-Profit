package Models

import "time"

type Crypto struct {
	ID          int       `json:"id"`
	Name        string    `json:"name"`
	Data_create time.Time `json:"data_create"`
}
