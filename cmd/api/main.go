package main

import (
	"context"
	"log"
	"os" // <--- NUEVO
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"my-streaming-app/internal/agenda"
	"my-streaming-app/internal/tv"
)

func main() {
	// 1. Obtener Variables de Entorno
	mongoURI := os.Getenv("MONGODB_URI")
	if mongoURI == "" {
		mongoURI = "mongodb://127.0.0.1:27017" // Fallback para local
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// 2. Base de Datos
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		log.Fatal("Error conectando a Mongo:", err)
	}

	db := client.Database("streaming_db")

	// 3. Repositorios y Handlers
	tvRepo := tv.NewRepository(db)
	tvHandler := tv.NewHandler(tvRepo)
	agendaRepo := agenda.NewRepository(db)
	agendaHandler := agenda.NewHandler(agendaRepo)

	app := fiber.New()

	// --- CORS CONFIGURADO PARA PRODUCCIÓN ---
	app.Use(cors.New(cors.Config{
		AllowOrigins: "*", // En producción puedes poner la URL de tu front de Vercel/Firebase
		AllowHeaders: "Origin, Content-Type, Accept",
	}))

	api := app.Group("/api")
	api.Post("/tv/update-sources", tvHandler.UpdateSources)
	api.Get("/tv/channels", tvHandler.GetChannels)
	api.Post("/agenda/update", agendaHandler.UpdateAgenda)
	api.Get("/agenda", agendaHandler.GetAgenda)

	log.Printf("🚀 Servidor corriendo en puerto %s", port)
	log.Fatal(app.Listen(":" + port))
}
