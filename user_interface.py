import pygame
import json
from generate_options import generateCompleteOptions, generatePartialOptions, processInputs


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


class OptionsScrollArea:
    def __init__(self, x, y, w, h, font, json_path='./assistanceJSONs/completeOptions.json'):
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

            # Start capture button click (no action for now)
            if self.start_button_rect.collidepoint(event.pos):
                print('Start capture clicked (not implemented)')

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

            y += self.item_height + self.padding

        screen.set_clip(clip)

        # Draw start capture button
        pygame.draw.rect(screen, (0, 120, 200), self.start_button_rect)
        txt = self.font.render('Start capture', True, (255, 255, 255))
        screen.blit(txt, (self.start_button_rect.x + (self.start_button_rect.w - txt.get_width())/2, self.start_button_rect.y + (self.start_button_rect.h - txt.get_height())/2))
# Game main function
def run_ui(callback):
    clock = pygame.time.Clock()

    # ------- INPUTS
    # Multipliers
    fc_multipliers = [("M", 1e6), ("G", 1e9)]
    bw_multipliers = [("M", 1e6), ("G", 1e9)]
    time_multipliers = [("", 1), ("m", 1e-3)]

    # Graphics
    input_f_min = InputBox(150, 50, 140, 32, "F_min:", "1", multipliers=fc_multipliers, unit="Hz", default_multiplier_index=3)
    input_f_max = InputBox(150, 100, 140, 32, "F_max:", "2", multipliers=bw_multipliers, unit="Hz", default_multiplier_index=3) 
    input_time = InputBox(WIDTH/2 + 150, 50, 140, 32, "Temps:", "1", multipliers=time_multipliers, unit="s")
    input_num_chan = InputBox(WIDTH/2 + 150, 100, 140, 32, "#Chan:*", "1", multipliers=None, unit="")

    # ------- "Genrar Opcions" button
    # Positioning
    inputs_bottom = max(input_f_max.rect.bottom, input_num_chan.rect.bottom)
    options_button_width = 200
    options_button_height = 40
    options_button_rect = pygame.Rect(WIDTH/2 - options_button_width/2, inputs_bottom + 20, options_button_width, options_button_height)

    # After click text
    are_inputs_valid = False
    options_button_text = ""

    # ------- Options scroll area (80% of screen)
    area_w = int(0.8 * WIDTH)
    area_h = int(0.8 * HEIGHT)
    area_x = (WIDTH - area_w) // 2
    # place area start below potential button text; reserve margin
    area_y = options_button_rect.bottom + 60
    # shrink if overflowing
    if area_y + area_h + 80 > HEIGHT:
        area_h = max(100, HEIGHT - area_y - 80)

    options_area = OptionsScrollArea(area_x, area_y, area_w, area_h, font)
    options_area.refresh()

    # ------- Main loop
    running = True
    while running:
        # Events loop
        for event in pygame.event.get():
            # Quit event
            if event.type == pygame.QUIT:
                running = False

            # Handle input_boxes events
            input_f_min.handle_event(event)
            input_f_max.handle_event(event)
            input_time.handle_event(event)
            input_num_chan.handle_event(event)

            # Forward event to options area (handles clicks/scroll)
            options_area.handle_event(event)

            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                # "Generar Opcions" button click
                if options_button_rect.collidepoint(event.pos):
                    # Build numeric representations of inputs
                    try:
                        fmin_val = float(input_f_min.text) * input_f_min.get_multiplier_value()
                        fmax_val = float(input_f_max.text) * input_f_max.get_multiplier_value()
                        time_val = float(input_time.text) * input_time.get_multiplier_value()
                        num_chan_val = int(input_num_chan.text)
                    except ValueError:
                        print("Error: Please enter valid numeric values.")
                        fmin_val = fmax_val = time_val = num_chan_val = None

                    # Check if values are valid
                    are_inputs_valid, userInputs = processInputs(f_min=fmin_val, f_max=fmax_val, time=time_val, num_chan=num_chan_val)
                    if are_inputs_valid:
                        print("Generating options...")
                        p_ok = generatePartialOptions(userInputs["fc"], userInputs["bw"], './assistanceJSONs/mcr_converter_rates_table.json', './assistanceJSONs/partialOptions.json')
                        if p_ok:
                            c_ok = generateCompleteOptions(userInputs["fc"], userInputs["bw"], './assistanceJSONs/partialOptions.json')
                            if c_ok:
                                options_button_text = "S'han generat les opcions correctament."
                                # refresh displayed options
                                options_area.refresh()
                            else:
                                options_button_text = "Error: No s'han pogut generar les opcions completes."
                        else:
                            options_button_text = "Error: No s'han pogut generar les opcions parcials."
                    else:
                        options_button_text = userInputs # User inputs contains the error message in this case
                    
                    
                        
                        

        # ------- Graphics
        # Background
        screen.fill((255, 255, 255))

        # Input_boxes
        input_f_min.draw(screen)
        input_f_max.draw(screen)
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
        # Draw options scroll area
        options_area.draw(screen)
        # Update display
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()