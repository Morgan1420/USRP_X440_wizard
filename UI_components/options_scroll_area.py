import pygame
import json


class OptionsScrollArea:
    def __init__(self, x, y, w, h, font, json_path='./assistanceJSONs/filteredOptions.json'):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.json_path = json_path
        self.items = []
        self.selected_index = None
        self.scroll = 0
        self.item_height = 60
        self.padding = 8
        # Start capture button
        btn_w = 180
        btn_h = 40
        btn_x = x + (w - btn_w) // 2
        btn_y = y + h + 12
        self.start_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        # per-item "Mostra" button dimensions
        self.item_button_w = 84
        self.item_button_h = 28

    def refresh(self):
        # Load complete options from JSON
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                self.items = data
            else:
                self.items = []
        except Exception:
            self.items = []

    def handle_event(self, event):
        # Scroll wheel
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 30
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Mouse wheel (older systems)
            if event.button == 4:
                self.scroll -= 30
            elif event.button == 5:
                self.scroll += 30

            # Click inside items
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.rect.y + self.scroll
                idx = rel_y // (self.item_height + self.padding)
                if 0 <= idx < len(self.items):
                    self.selected_index = int(idx)

                # Check if the "Mostra" button for that item was clicked
                # compute item rect and button rect
                if 0 <= idx < len(self.items):
                    item_y = self.rect.y + (idx * (self.item_height + self.padding)) - self.scroll + self.padding
                    item_rect = pygame.Rect(self.rect.x + self.padding, int(item_y), self.rect.w - self.padding * 2, self.item_height)
                    btn_x = item_rect.right - self.item_button_w - 8
                    btn_y = item_rect.y + (item_rect.h - self.item_button_h)//2
                    btn_rect = pygame.Rect(btn_x, btn_y, self.item_button_w, self.item_button_h)
                    if btn_rect.collidepoint(event.pos):
                        return ('show', self.items[int(idx)])

            # Start capture button click -> signal to open hardware config screen
            if self.start_button_rect.collidepoint(event.pos):
                # Only allow starting capture when an item is selected
                if self.selected_index is None:
                    return None
                try:
                    idx = int(self.selected_index)
                except Exception:
                    return None
                if idx < 0 or idx >= len(self.items):
                    return None
                # return the selected item as payload
                return ('start_capture', self.items[idx])

        return None

        # Clamp scroll
        max_scroll = max(0, len(self.items) * (self.item_height + self.padding) - self.rect.h)
        if self.scroll < 0:
            self.scroll = 0
        if self.scroll > max_scroll:
            self.scroll = max_scroll

    def draw(self, screen):
        # Background
        pygame.draw.rect(screen, (245, 245, 245), self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)

        # Clip to area
        clip = screen.get_clip()
        screen.set_clip(self.rect)

        y = self.rect.y - self.scroll + self.padding
        for i, item in enumerate(self.items):
            item_rect = pygame.Rect(self.rect.x + self.padding, int(y), self.rect.w - self.padding * 2, self.item_height)
            # Selected highlight
            if self.selected_index == i:
                pygame.draw.rect(screen, (200, 230, 255), item_rect)
            else:
                pygame.draw.rect(screen, (255, 255, 255), item_rect)
            pygame.draw.rect(screen, (0, 0, 0), item_rect, 1)

            # Draw summary text
            title = item.get('complete_option_id', f'Option {i}')
            try:
                chans = item.get('chans_needed', '')
            except Exception:
                chans = ''
            left_text = f"{title}  chans: {chans}"
            t_surf = self.font.render(left_text, True, (0, 0, 0))
            screen.blit(t_surf, (item_rect.x + 8, item_rect.y + 8))

            # Frequency range
            f_start = item.get('f_start', '')
            f_end = item.get('f_end', '')
            range_text = f"{int(f_start)} - {int(f_end)} Hz" if f_start != '' and f_end != '' else ''
            r_surf = self.font.render(range_text, True, (50, 50, 50))
            screen.blit(r_surf, (item_rect.x + 8, item_rect.y + 32))

            # "Mostra" button on the right
            btn_x = item_rect.right - self.item_button_w - 8
            btn_y = item_rect.y + (item_rect.h - self.item_button_h)//2
            btn_rect = pygame.Rect(btn_x, btn_y, self.item_button_w, self.item_button_h)
            pygame.draw.rect(screen, (100, 180, 100), btn_rect)
            btxt = self.font.render('Mostra', True, (255, 255, 255))
            screen.blit(btxt, (btn_rect.x + (btn_rect.w - btxt.get_width())/2, btn_rect.y + (btn_rect.h - btxt.get_height())/2))

            y += self.item_height + self.padding

        screen.set_clip(clip)

        # Draw start capture button (disabled if no selection)
        enabled = (self.selected_index is not None and 0 <= int(self.selected_index) < len(self.items))
        btn_color = (0, 120, 200) if enabled else (160, 160, 160)
        txt_color = (255, 255, 255) if enabled else (200, 200, 200)
        pygame.draw.rect(screen, btn_color, self.start_button_rect)
        txt = self.font.render('Start capture', True, txt_color)
        screen.blit(txt, (self.start_button_rect.x + (self.start_button_rect.w - txt.get_width())/2, self.start_button_rect.y + (self.start_button_rect.h - txt.get_height())/2))
