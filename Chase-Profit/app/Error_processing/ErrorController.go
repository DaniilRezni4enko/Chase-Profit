package Error_processing

import (
	"Chase-Profit/routes"
	"net/http"
)

func ErrorProc(error_type string) {
	switch error_type {
	case "404":
		http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/" {
				http.Redirect(w, r, "/error_404", http.StatusFound)
			}

		})

		routes.ErrorRoutes()
	}
}
