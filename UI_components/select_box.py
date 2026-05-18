import pygame


class SelectBox:
    def __init__(self, x, y, w, h, label, options, font, default_index=0, label_gap=100):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.label = label
        self.options = list(options)
        self.selected = max(0, min(default_index, len(self.options) - 1)) if self.options else None
        self.expanded = False
        # if True, draw the options list above the box instead of below
        self.expand_up = False
        self.label_gap = label_gap

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # click on main rect toggles expand
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return

            # if expanded, check options area (below or above depending on expand_up)
            if self.expanded:
                n = len(self.options)
                step = self.rect.h + 2
                if not self.expand_up:
                    opt_y_start = self.rect.bottom
                else:
                    opt_y_start = self.rect.top - n * step

                for i in range(n):
                    orect = pygame.Rect(self.rect.x, opt_y_start + i * step, self.rect.w, self.rect.h)
                    if orect.collidepoint(event.pos):
                        self.selected = i
                        self.expanded = False
                        return
                # click outside options collapses
                self.expanded = False

    def get_value(self):
        if self.selected is None:
            return None
        return self.options[self.selected]

    def draw(self, screen):
        # label
        label_s = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(label_s, (self.rect.x - self.label_gap, self.rect.y + 5))

        # box
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 1)

        # selected text
        val = self.get_value() or ''
        txt = self.font.render(val, True, (0, 0, 0))
        screen.blit(txt, (self.rect.x + 6, self.rect.y + (self.rect.h - txt.get_height()) // 2))

        # dropdown arrow
        arrow_x = self.rect.right - 14
        arrow_y = self.rect.y + self.rect.h // 2
        pygame.draw.polygon(screen, (0, 0, 0), [(arrow_x - 6, arrow_y - 3), (arrow_x + 6, arrow_y - 3), (arrow_x, arrow_y + 4)])

        # options if expanded (draw below or above)
        if self.expanded:
            n = len(self.options)
            step = self.rect.h + 2
            if not self.expand_up:
                opt_y_start = self.rect.bottom
            else:
                opt_y_start = self.rect.top - n * step

            for i, opt in enumerate(self.options):
                orect = pygame.Rect(self.rect.x, opt_y_start + i * step, self.rect.w, self.rect.h)
                pygame.draw.rect(screen, (255, 255, 255), orect)
                pygame.draw.rect(screen, (0, 0, 0), orect, 1)
                os = self.font.render(opt, True, (0, 0, 0))
                screen.blit(os, (orect.x + 6, orect.y + (orect.h - os.get_height()) // 2))
