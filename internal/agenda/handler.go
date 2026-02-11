package agenda

import "github.com/gofiber/fiber/v2"

type Handler struct {
	repo Repository
}

func NewHandler(repo Repository) *Handler {
	return &Handler{repo: repo}
}

// GET /api/agenda
func (h *Handler) GetAgenda(c *fiber.Ctx) error {
	events, err := h.repo.GetAgenda(c.Context())
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Error interno"})
	}
	return c.JSON(events)
}

// POST /api/agenda/update (Para Python)
func (h *Handler) UpdateAgenda(c *fiber.Ctx) error {
	var dto AgendaUpdateDTO
	if err := c.BodyParser(&dto); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "JSON invalido"})
	}

	if err := h.repo.ReplaceAgenda(c.Context(), dto.Events); err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Error guardando agenda"})
	}

	return c.JSON(fiber.Map{"message": "Agenda actualizada", "count": len(dto.Events)})
}
