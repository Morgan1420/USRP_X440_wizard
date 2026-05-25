import pygame


class InputBox:
    
    '''
    This is no ordinary input box, it contains:
      - A label on the left (to explain what the input is for)
      - The input box itself (where the user can type)
      - Optional multiplier buttons on the right (to specify units like kHz, MHz, etc. with a single click)
      - Optional unit label on the right (to show the unit of the input value, e.g. "Hz")
    '''
    
    # Init function takes and parses all the parameters
    def __init__(self, x, y, w, h, label, placeholder, font, multipliers=None, unit="", default_multiplier_index=0, label_gap=100):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text = placeholder
        self.font = font
        self.txt_surface = self.font.render(self.text, True, (0, 0, 0))
        self.active = False
        self.label = label 
        self.label_gap = label_gap # gap in pixels between label and input box (used for extra gaps when the lable is too long)
        self.multipliers = multipliers or [] # multipliers: list of tuples (label, value)
        self.unit = unit
        if self.multipliers:
            self.selected_multiplier = max(0, min(default_multiplier_index, len(self.multipliers) - 1))
        else:
            self.selected_multiplier = None
        self.multiplier_rects = []

    # Handle_event function:
    def handle_event(self, event):
        # Check for mouse click events
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if any multiplier button was clicked
            clicked = False
            for i, mrect in enumerate(self.multiplier_rects):
                if mrect.collidepoint(event.pos):
                    self.selected_multiplier = i
                    clicked = True
                    break
            
            # If we didn't click a multiplier, check if we clicked the input box to activate it
            if not clicked:
                self.active = self.rect.collidepoint(event.pos)

        # Check for key events when the input box is active
        if event.type == pygame.KEYDOWN and self.active:
            # Handle the key input character
            if event.key == pygame.K_BACKSPACE: # Delete key
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN: # Enter key
                self.active = False
            else: # Any other key 
                self.text += event.unicode
            
            # Re-render the text surface after any change
            self.txt_surface = self.font.render(self.text, True, (0, 0, 0))

    # Assistant function to get the current value of the input box, applying the multiplier if selected
    def get_multiplier_value(self):
        if self.multipliers and self.selected_multiplier is not None:
            return float(self.multipliers[self.selected_multiplier][1])
        return 1.0

    # Assistant function to get the current multiplier label
    def get_multiplier_label(self):
        if self.multipliers and self.selected_multiplier is not None:
            return str(self.multipliers[self.selected_multiplier][0])
        return ''

    # Draw function
    def draw(self, screen):
        # Draw label and input box
        label_surface = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(label_surface, (self.rect.x - self.label_gap, self.rect.y + 5))
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
            # Draw unit after input box if no multipliers
            if self.unit:
                unit_surf = self.font.render(self.unit, True, (0, 0, 0))
                screen.blit(unit_surf, (self.rect.right + 8, self.rect.y + (self.rect.h - unit_surf.get_height()) // 2))
