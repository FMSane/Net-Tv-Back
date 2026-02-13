package agenda

import "time"

type AgendaOption struct {
	Name       string `bson:"name" json:"name"` // Ej: "Disney+"
	URL        string `bson:"url" json:"url"`   // El link decodificado
	Type       string `bson:"type" json:"type"` // NUEVO: "m3u8", "dash", "iframe"
	Drm        any    `bson:"drm" json:"drm"`   // NUEVO: Info DRM si aplica
	IsExternal bool   `bson:"is_external" json:"is_external"`
}

type SportEvent struct {
	Title    string         `bson:"title" json:"title"`
	Date     string         `bson:"date" json:"date"`
	Time     string         `bson:"time" json:"time"`
	League   string         `bson:"league" json:"league"`
	Image    string         `bson:"image" json:"image"` // NUEVO: Logo de la liga
	Channels []AgendaOption `bson:"channels" json:"channels"`
	Order    int            `bson:"order" json:"order"`
}

type AgendaUpdateDTO struct {
	Events []SportEvent `json:"events"`
}

type AgendaMeta struct {
	LastUpdated time.Time `bson:"last_updated" json:"last_updated"`
}
