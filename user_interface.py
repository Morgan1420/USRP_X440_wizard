import pygame
from generate_options import areInputsValid


# Pygame things
pygame.init()

WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("USRP X440 Wizard")

font = pygame.font.Font(None, 32)

# Game classes
class InputBox:
    def __init__(self, x, y, w, h, label, placeholder, multipliers=None, unit="", default_multiplier_index=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = pygame.Color('lightskyblue3')
        self.text = placeholder
        self.txt_surface = font.render(self.text, True, (0, 0, 0))
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
            self.txt_surface = font.render(self.text, True, (0, 0, 0))

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
        label_surface = font.render(self.label, True, (0, 0, 0))
        screen.blit(label_surface, (self.rect.x - 100, self.rect.y + 5))
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

        # Draw multipliers to the right of the input box
        self.multiplier_rects = []
        if self.multipliers:
            padding = 6
            x = self.rect.right + 8
            for i, (mlabel, mval) in enumerate(self.multipliers):
                text_surf = font.render(mlabel, True, (0, 0, 0))
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
                unit_surf = font.render(self.unit, True, (0, 0, 0))
                screen.blit(unit_surf, (x + 4, self.rect.y + (self.rect.h - unit_surf.get_height()) // 2))
        else:
            if self.unit:
                unit_surf = font.render(self.unit, True, (0, 0, 0))
                screen.blit(unit_surf, (self.rect.right + 8, self.rect.y + (self.rect.h - unit_surf.get_height()) // 2))

# Game main function
def run_ui(callback):
    clock = pygame.time.Clock()

    # ------- INPUTS
    # Multipliers
    fc_multipliers = [("", 1), ("K", 1e3), ("M", 1e6), ("G", 1e9)]
    bw_multipliers = [("", 1), ("K", 1e3), ("M", 1e6), ("G", 1e9)]
    time_multipliers = [("", 1), ("m", 1e-3)]

    # Graphics
    input_fc = InputBox(150, 50, 140, 32, "Fc:", "10", multipliers=fc_multipliers, unit="Hz", default_multiplier_index=2)
    input_bw = InputBox(150, 100, 140, 32, "BW:", "5", multipliers=bw_multipliers, unit="Hz", default_multiplier_index=1) 
    input_time = InputBox(WIDTH/2 + 150, 50, 140, 32, "Temps:", "1", multipliers=time_multipliers, unit="s")
    input_num_chan = InputBox(WIDTH/2 + 150, 100, 140, 32, "#Chan:*", "1", multipliers=None, unit="")

    # ------- "Genrar Opcions" button
    # Positioning
    inputs_bottom = max(input_bw.rect.bottom, input_num_chan.rect.bottom)
    options_button_width = 200
    options_button_height = 40
    options_button_rect = pygame.Rect(WIDTH/2 - options_button_width/2, inputs_bottom + 20, options_button_width, options_button_height)

    # After click text
    are_inputs_valid = False
    options_button_text = ""

    # ------- Main loop
    running = True
    while running:
        # Events loop
        for event in pygame.event.get():
            # Quit event
            if event.type == pygame.QUIT:
                running = False

            # Handle input_boxes events
            input_fc.handle_event(event)
            input_bw.handle_event(event)
            input_time.handle_event(event)
            input_num_chan.handle_event(event)

            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                # "Generar Opcions" button click
                if options_button_rect.collidepoint(event.pos):
                    # Build numeric representations of inputs
                    try:
                        fc_val = float(input_fc.text) * input_fc.get_multiplier_value()
                        bw_val = float(input_bw.text) * input_bw.get_multiplier_value()
                        time_val = float(input_time.text) * input_time.get_multiplier_value()
                        num_chan_val = int(input_num_chan.text)
                    except ValueError:
                        print("Error: Please enter valid numeric values.")
                        fc_val = bw_val = time_val = num_chan_val = None
                        

                    # Check if values are valid
                    are_inputs_valid, options_button_text = areInputsValid(fc_val, bw_val, time_val, num_chan_val)
                    
                    if are_inputs_valid:
                        # Generate options 
                        print("Generating options...")
                    else:
                        print(options_button_text)
                        
                        

        # ------- Graphics
        # Background
        screen.fill((255, 255, 255))

        # Input_boxes
        input_fc.draw(screen)
        input_bw.draw(screen)
        input_time.draw(screen)
        input_num_chan.draw(screen)

        # "Genrar Opcions" button
        pygame.draw.rect(screen, (0, 120, 200), options_button_rect)
        options_text = font.render("Genrar Opcions", True, (255, 255, 255))
        screen.blit(options_text, (options_button_rect.x + options_button_width/2 - options_text.get_width()/2, options_button_rect.y + options_button_height/2 - options_text.get_height()/2))

        # Button text (error/warning)
        if not are_inputs_valid:
            text_color = (200, 0, 0) if options_button_text.startswith("Error") else (200, 100, 0)
            options_button_text_surf = font.render(options_button_text, True, text_color)
            screen.blit(options_button_text_surf, (WIDTH/2 - options_button_text_surf.get_width()/2, options_button_rect.bottom + 10))
        else:
            options_button_text_surf = font.render(options_button_text, True, (0, 150, 0))
            screen.blit(options_button_text_surf, (WIDTH/2 - options_button_text_surf.get_width()/2, options_button_rect.bottom + 10))
        # Update display
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()