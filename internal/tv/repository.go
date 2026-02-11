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
		db: db.Collection("channels"),
	}
}

func (r *repository) UpsertChannelSources(ctx context.Context, dto UpdateChannelDTO) error {
	filter := bson.M{"name": dto.Name}

	update := bson.M{
		"$set": bson.M{
			"sources":      dto.Sources,
			"last_updated": time.Now(),
			"logo":         dto.Logo,
			"category":     dto.Category,
		},
		"$setOnInsert": bson.M{
			"created_at": time.Now(),
		},
	}

	opts := options.Update().SetUpsert(true)
	_, err := r.db.UpdateOne(ctx, filter, update, opts)
	return err
}

func (r *repository) GetAll(ctx context.Context) ([]Channel, error) {
	// Agregamos un Sort alfabético por defecto para que no salgan desordenados
	opts := options.Find().SetSort(bson.D{{Key: "name", Value: 1}})

	cursor, err := r.db.Find(ctx, bson.M{}, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	// Inicializar como slice vacío para que devuelva [] en vez de null si no hay datos
	channels := make([]Channel, 0)

	if err = cursor.All(ctx, &channels); err != nil {
		return nil, err
	}
	return channels, nil
}
