package agenda

import (
	"context"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options" // <--- IMPORTANTE: Agregado
)

type Repository interface {
	ReplaceAgenda(ctx context.Context, events []SportEvent) error
	GetAgenda(ctx context.Context) ([]SportEvent, error)
}

type repo struct {
	col *mongo.Collection
}

func NewRepository(db *mongo.Database) Repository {
	return &repo{
		col: db.Collection("sports_agenda"),
	}
}

func (r *repo) ReplaceAgenda(ctx context.Context, events []SportEvent) error {
	if len(events) == 0 {
		return nil
	}

	newDate := events[0].Date

	// Limpieza de días anteriores
	_, err := r.col.DeleteMany(ctx, bson.M{"date": bson.M{"$ne": newDate}})
	if err != nil {
		return err
	}

	for _, e := range events {
		filter := bson.M{
			"title": e.Title,
			"time":  e.Time,
			"date":  e.Date,
		}

		update := bson.M{
			"$set": bson.M{
				"league": e.League,
			},
			"$addToSet": bson.M{
				"channels": bson.M{"$each": e.Channels},
			},
		}

		// Aquí ya no dará error porque importamos 'options'
		opts := options.Update().SetUpsert(true)
		_, err := r.col.UpdateOne(ctx, filter, update, opts)
		if err != nil {
			return err
		}
	}
	return nil
}

func (r *repo) GetAgenda(ctx context.Context) ([]SportEvent, error) {
	// Agregamos un Sort por tiempo para que la lista se vea ordenada
	findOptions := options.Find().SetSort(bson.D{{Key: "time", Value: 1}})

	cursor, err := r.col.Find(ctx, bson.M{}, findOptions)
	if err != nil {
		return nil, err
	}

	var events []SportEvent
	if err := cursor.All(ctx, &events); err != nil {
		return nil, err
	}
	return events, nil
}
