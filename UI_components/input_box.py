import pygame


class InputBox:
    def __init__(self, x, y, w, h, label, placeholder, font, multipliers=None, unit="", default_multiplier_index=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text = placeholder
        self.font = font
        self.txt_surface = self.font.render(self.text, True, (0, 0, 0))
        self.active = False
        self.label = label
        # multipliers: list of tuples (label, value)
        self.multipliers = multipliers or []
        self.unit = unit
        if self.multipliers:
            self.selected_multiplier = max(0, min(default_multiplier_index, len(self.multipliers) - 1))
        else:
            self.selected_multiplier = None
        self.multiplier_rects = []

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check multiplier clicks first
            clicked = False
            for i, mrect in enumerate(self.multiplier_rects):
                if mrect.collidepoint(event.pos):
                    self.selected_multiplier = i
                    clicked = True
                    break

            if not clicked:
                self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, (0, 0, 0))

    def get_multiplier_value(self):
        if self.multipliers and self.selected_multiplier is not None:
            try:
                return float(self.multipliers[self.selected_multiplier][1])
            except Exception:
                return 1.0
        return 1.0

    def get_multiplier_label(self):
        if self.multipliers and self.selected_multiplier is not None:
            return str(self.multipliers[self.selected_multiplier][0])
        return ''

    def draw(self, screen):
        label_surface = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(label_surface, (self.rect.x - 100, self.rect.y + 5))
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

        # Draw multipliers to the right of the input box
        self.multiplier_rects = []
        if self.multipliers:
            padding = 6
            x = self.rect.right + 8
            for i, (mlabel, mval) in enumerate(self.multipliers):
                text_surf = self.font.render(mlabel, True, (0, 0, 0))
                mrect = pygame.Rect(x, self.rect.y, text_surf.get_width() + padding * 2, self.rect.h)
                # Highlight selected
                if i == self.selected_multiplier:
                    pygame.draw.rect(screen, (200, 200, 200), mrect)
                pygame.draw.rect(screen, (0, 0, 0), mrect, 1)
                screen.blit(text_surf, (mrect.x + padding, mrect.y + (self.rect.h - text_surf.get_height()) // 2))
                self.multiplier_rects.append(mrect)
                x = mrect.right + 6

            # Draw unit after multipliers
            if self.unit:
                unit_surf = self.font.render(self.unit, True, (0, 0, 0))
                screen.blit(unit_surf, (x + 4, self.rect.y + (self.rect.h - unit_surf.get_height()) // 2))
        else:
            if self.unit:
                unit_surf = self.font.render(self.unit, True, (0, 0, 0))
                screen.blit(unit_surf, (self.rect.right + 8, self.rect.y + (self.rect.h - unit_surf.get_height()) // 2))
