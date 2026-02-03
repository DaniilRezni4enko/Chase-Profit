package Models

import "time"

type CryptoDeal struct {
	ID         int       `json:"id"`
	UserID     int       `json:"user_id"`
	Currency   string    `json:"currency"`
	TakeProfit float64   `json:"take_profit"`
	StopLoss   float64   `json:"stop_loss"`
	BuyRate    float64   `json:"buy_rate"`
	SaleRate   float64   `json:"sale_rate"`
	Summ       float64   `json:"summ"`
	PnL        string    `json:"pnl"`
	TimeOpen   time.Time `json:"time_open"`
	TimeClose  time.Time `json:"time_close"`
}
