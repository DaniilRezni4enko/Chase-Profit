package Models

import "time"

type Alert struct {
	ID int `json:"id"`
	UserID string `json:"username"`
	CreatedAt time.Time `json:"created_at"`
	Text string `json:"text"`
	Currency string	`json:"currency"`
	Strategy string	`json:"strategy"`
}
