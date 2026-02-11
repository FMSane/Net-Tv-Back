package agenda

import (
	"context"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
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

	// 1. Obtener la fecha del primer evento recibido (asumiendo que todos son del mismo día)
	newDate := events[0].Date

	// 2. Limpieza: Borrar eventos que NO sean de la fecha actual
	// Esto asegura que si el script corre el jueves, lo del miércoles desaparezca
	_, err := r.col.DeleteMany(ctx, bson.M{"date": bson.M{"$ne": newDate}})
	if err != nil {
		return err
	}

	// 3. Procesar cada evento con Upsert inteligente
	for _, e := range events {
		filter := bson.M{
			"title": e.Title,
			"time":  e.Time,
			"date":  e.Date,
		}

		// $addToSet agrega las opciones al array 'channels' solo si no existen ya
		update := bson.M{
			"$set": bson.M{
				"league": e.League,
			},
			"$addToSet": bson.M{
				"channels": bson.M{"$each": e.Channels},
			},
		}

		opts := options.Update().SetUpsert(true)
		_, err := r.col.UpdateOne(ctx, filter, update, opts)
		if err != nil {
			return err
		}
	}
	return nil
}
func (r *repo) GetAgenda(ctx context.Context) ([]SportEvent, error) {
	cursor, err := r.col.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}

	var events []SportEvent
	if err := cursor.All(ctx, &events); err != nil {
		return nil, err
	}
	return events, nil
}
