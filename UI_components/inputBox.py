import pygame


class InputBox:
    def __init__(self, x, y, w, h, label, placeholder):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text = placeholder
        self.txt_surface = font.render(self.text, True, (0, 0, 0))
        self.active = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = font.render(self.text, True, (0, 0, 0))

    def draw(self, screen):
        label_surface = font.render(self.label, True, (0, 0, 0))
        screen.blit(label_surface, (self.rect.x - 100, self.rect.y + 5))
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

