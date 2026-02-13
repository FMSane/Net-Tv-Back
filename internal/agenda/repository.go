package agenda

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
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

	// BORRADO TOTAL:
	// Borramos TODOS los eventos de la agenda actual, sin importar la fecha.
	// La agenda extraída por el crawler es la única versión válida.
	_, err := r.col.DeleteMany(ctx, bson.M{})
	if err != nil {
		return err
	}

	// INSERCIÓN MASIVA:
	// Insertamos la lista "fresca" tal cual viene del crawler.
	docs := make([]interface{}, len(events))
	for i, e := range events {
		docs[i] = e
	}

	_, err = r.col.InsertMany(ctx, docs)
	return err
}

func (r *repo) GetAgenda(ctx context.Context) ([]SportEvent, error) {
	// ORDENAR:
	// Usamos el campo "order" para respetar el orden visual de la web.
	findOptions := options.Find().SetSort(bson.D{
		{Key: "order", Value: 1},
		{Key: "time", Value: 1},
	})

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
