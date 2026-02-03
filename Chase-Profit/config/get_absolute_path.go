package config

import (
	"fmt"
	"os"
)

func GetAbsolutePath() string {
	currentDir, err := os.Getwd()
	if err != nil {
		fmt.Println("Ошибка:", err)
	}
	return currentDir
}
