package tv

import "github.com/gofiber/fiber/v2"

type Handler struct {
	repo Repository
}

func NewHandler(repo Repository) *Handler {
	return &Handler{repo: repo}
}

// UpdateSources maneja el POST /api/tv/update-sources
func (h *Handler) UpdateSources(c *fiber.Ctx) error {
	var dto UpdateChannelDTO

	// 1. Parsear el Body (JSON -> Struct)
	if err := c.BodyParser(&dto); err != nil {
		return c.Status(400).JSON(fiber.Map{
			"error": "JSON inválido",
		})
	}

	// 2. Validaciones básicas
	if dto.Name == "" || len(dto.Sources) == 0 {
		return c.Status(400).JSON(fiber.Map{
			"error": "El nombre y los sources son obligatorios",
		})
	}

	// 3. Llamar a la base de datos
	err := h.repo.UpsertChannelSources(c.Context(), dto)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{
			"error": "Error guardando en base de datos: " + err.Error(),
		})
	}

	// 4. Responder Éxito
	return c.Status(200).JSON(fiber.Map{
		"message": "Canal actualizado correctamente",
		"channel": dto.Name,
	})
}

func (h *Handler) GetChannels(c *fiber.Ctx) error {
	channels, err := h.repo.GetAll(c.Context())
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "No se pudieron cargar los canales"})
	}
	return c.JSON(channels)
}
