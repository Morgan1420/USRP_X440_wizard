import pygame
import json

from .input_box import InputBox


class FilterPopUp:
    def __init__(self, font, json_path='./assistanceJSONs/filters.json'):
        self.font = font
        self.json_path = json_path
        self.width = 420
        self.height = 200
        self.active = False
        self.min_input = None
        self.max_input = None
        self.ok_rect = None
        self.cancel_rect = None

    def open(self):
        self.active = True
        # Inputs will be positioned when drawing (centered)
        self.min_input = None
        self.max_input = None

    def close(self):
        self.active = False

    def handle_event(self, event, screen):
        if not self.active:
            return None

        # ensure inputs positioned
        self._ensure_inputs(screen)

        # forward events to inputs
        self.min_input.handle_event(event)
        self.max_input.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.ok_rect and self.ok_rect.collidepoint(event.pos):
                self._save()
                self.close()
                return 'ok'
            if self.cancel_rect and self.cancel_rect.collidepoint(event.pos):
                self.close()
                return 'cancel'

        return None

    def _save(self):
        # Parse integer values or None
        def parse_int(s):
            try:
                s = s.strip()
                if s == '':
                    return None
                return int(float(s))
            except Exception:
                return None

        min_val = parse_int(self.min_input.text)
        max_val = parse_int(self.max_input.text)

        obj = {
            'min_channels': min_val,
            'max_channels': max_val
        }
        try:
            with open(self.json_path, 'w') as f:
                json.dump(obj, f, indent=2)
        except Exception:
            # best-effort: ignore write errors
            pass

    def _ensure_inputs(self, screen):
        sw, sh = screen.get_size()
        x = (sw - self.width) // 2
        y = (sh - self.height) // 2

        input_w = 140
        input_h = 32
        input_x = x + 120
        input_y1 = y + 40
        input_y2 = y + 90

        if self.min_input is None:
            self.min_input = InputBox(input_x, input_y1, input_w, input_h, 'Min num of channels', '', self.font)
        else:
            self.min_input.rect.x = input_x
            self.min_input.rect.y = input_y1

        if self.max_input is None:
            self.max_input = InputBox(input_x, input_y2, input_w, input_h, 'Max num of chanells', '', self.font)
        else:
            self.max_input.rect.x = input_x
            self.max_input.rect.y = input_y2

        # OK / Cancel positions
        btn_w = 80
        btn_h = 34
        self.ok_rect = pygame.Rect(x + self.width - btn_w - 16, y + self.height - btn_h - 12, btn_w, btn_h)
        self.cancel_rect = pygame.Rect(x + 16, y + self.height - btn_h - 12, btn_w, btn_h)

    def draw(self, screen):
        if not self.active:
            return

        sw, sh = screen.get_size()
        x = (sw - self.width) // 2
        y = (sh - self.height) // 2

        # Draw semi-transparent overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Popup background
        popup_rect = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(screen, (255, 255, 255), popup_rect)
        pygame.draw.rect(screen, (0, 0, 0), popup_rect, 2)

        # Title
        title_surf = self.font.render('Filter options', True, (0, 0, 0))
        screen.blit(title_surf, (x + (self.width - title_surf.get_width()) // 2, y + 8))

        # Ensure inputs positioned
        self._ensure_inputs(screen)

        # Draw inputs
        self.min_input.draw(screen)
        self.max_input.draw(screen)

        # Draw buttons
        pygame.draw.rect(screen, (200, 200, 200), self.cancel_rect)
        pygame.draw.rect(screen, (0, 120, 200), self.ok_rect)

        cancel_s = self.font.render('Cancel', True, (0, 0, 0))
        ok_s = self.font.render('OK', True, (255, 255, 255))

        screen.blit(cancel_s, (self.cancel_rect.x + (self.cancel_rect.w - cancel_s.get_width()) // 2, self.cancel_rect.y + (self.cancel_rect.h - cancel_s.get_height()) // 2))
        screen.blit(ok_s, (self.ok_rect.x + (self.ok_rect.w - ok_s.get_width()) // 2, self.ok_rect.y + (self.ok_rect.h - ok_s.get_height()) // 2))
