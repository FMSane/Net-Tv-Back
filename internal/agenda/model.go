package agenda

import "time"

type AgendaOption struct {
	Name       string `bson:"name" json:"name"`               // Ej: "Disney+"
	URL        string `bson:"url" json:"url"`                 // El link decodificado
	IsExternal bool   `bson:"is_external" json:"is_external"` // true si es un link directo, false si es ref a canal
}

type SportEvent struct {
	Title    string         `bson:"title" json:"title"`   // "Tigres vs Forge"
	Date     string         `bson:"date" json:"date"`     // Ej: "2026-02-11"
	Time     string         `bson:"time" json:"time"`     // "21:00" (Podrías parsearlo a Date si quieres)
	League   string         `bson:"league" json:"league"` // "CONCACAF"
	Channels []AgendaOption `bson:"channels" json:"channels"`
	Order    int            `bson:"order" json:"order"`
}

// Lo que guardaremos en Mongo (un solo documento gigante o lista, prefiero lista)
type AgendaUpdateDTO struct {
	Events []SportEvent `json:"events"`
}

type AgendaMeta struct {
	LastUpdated time.Time `bson:"last_updated" json:"last_updated"`
}
