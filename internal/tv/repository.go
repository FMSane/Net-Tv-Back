package tv

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Repository interface {
	UpsertChannelSources(ctx context.Context, dto UpdateChannelDTO) error
	GetAll(ctx context.Context) ([]Channel, error)
}

type repository struct {
	db *mongo.Collection
}

func NewRepository(db *mongo.Database) Repository {
	return &repository{
		db: db.Collection("channels"), // Nombre de la colección en Mongo
	}
}

func (r *repository) UpsertChannelSources(ctx context.Context, dto UpdateChannelDTO) error {
	// 1. Filtro: Buscamos por nombre exacto
	filter := bson.M{"name": dto.Name}

	// 2. Actualización: Solo tocamos los 'sources' y la fecha.
	// Usamos $setOnInsert para poner valores por defecto si es nuevo (como el logo vacio)
	update := bson.M{
		"$set": bson.M{
			"sources":      dto.Sources,
			"last_updated": time.Now(),
			"logo":         dto.Logo,
			"category":     dto.Category,
		},
		"$setOnInsert": bson.M{
			// Ya no hace falta poner defaults aquí porque el Python siempre manda data
			"created_at": time.Now(),
		},
	}

	// 3. Opciones: Upsert = true (Crear si no existe)
	opts := options.Update().SetUpsert(true)

	_, err := r.db.UpdateOne(ctx, filter, update, opts)
	return err
}

func (r *repository) GetAll(ctx context.Context) ([]Channel, error) {
	// Buscamos todos los documentos (filtro vacío)
	cursor, err := r.db.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var channels []Channel
	if err = cursor.All(ctx, &channels); err != nil {
		return nil, err
	}
	return channels, nil
}
