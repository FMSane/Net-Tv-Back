package tv

import (
	"go.mongodb.org/mongo-driver/bson/primitive"
	"time"
)

type DrmInfo struct {
	ClearKey *ClearKey `bson:"clearkey,omitempty" json:"clearkey,omitempty"`
}

type ClearKey struct {
	KeyId string `bson:"keyId" json:"keyId"`
	Key   string `bson:"key" json:"key"`
}

// Source: Representa cada opción de video (La14HD, BolaLoca, etc.)
type Source struct {
	Name     string            `bson:"name" json:"name"`                           // Ej: "Opción 1 (FL)"
	URL      string            `bson:"url" json:"url"`                             // Ej: "https://..."
	Type     string            `bson:"type" json:"type"`                           // "iframe", "m3u8"
	Priority int               `bson:"priority" json:"priority"`                   // 1, 2, 3...
	Headers  map[string]string `bson:"headers,omitempty" json:"headers,omitempty"` // "Referer", etc.
	Drm      *DrmInfo          `bson:"drm,omitempty" json:"drm,omitempty"`
}

// Channel: El documento completo en MongoDB
type Channel struct {
	ID          primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	Name        string             `bson:"name" json:"name"`         // Clave única (ej: "ESPN Colombia")
	Category    string             `bson:"category" json:"category"` // NUEVO: "Deportes", "Infantiles"
	Logo        string             `bson:"logo" json:"logo"`         // NUEVO: URL de la imagen
	Sources     []Source           `bson:"sources" json:"sources"`
	LastUpdated time.Time          `bson:"last_updated" json:"last_updated"`
}

// UpdateChannelDTO: Lo que recibimos EXACTAMENTE del Python
type UpdateChannelDTO struct {
	Name     string   `json:"name"`
	Category string   `json:"category"` // NUEVO
	Logo     string   `json:"logo"`     // NUEVO
	Sources  []Source `json:"sources"`
}
