import pygame


class OptionDetailsScreen:
    '''
        This class displays a detaliled screen of a selected option.
        It shows all the metadata from the complete option toogether with a plot of the frequency range and the partial options.
        It also shows similar information for each partial option that composes it.
    '''
    
    
    # Init function takes and parses all the parameters
    def __init__(self, option, font, screen_w, screen_h):
        self.option = option or {}
        self.font = font
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.active = True
        self.padding = 12
        self.section_gap = 12
        self.line_h = font.get_linesize()
        self.close_rect = pygame.Rect(12, 12, 100, 34) # Close button
        self.scroll = 0 # Scrolling
        self.panel_rect = pygame.Rect(40, 40, self.screen_w - 80, self.screen_h - 80) # panel rect defines the visible content area
        self.content_height = self._calculate_content_height()

    # Assistance function to calculate the total height of the content
    def _calculate_content_height(self):
        # GENERAL SECTION: title + few metadata lines + plot area
        height = 0
        # Top padding
        height += self.padding
        height += 40  # title area
        # Metadata lines
        meta_lines = max(1, len(self.option.keys()))
        height += meta_lines * self.line_h + 8
        # Plot area
        height += 200
        height += self.section_gap

        # CHANEL SECTIONS: for each partial option we have a title, metadata lines and a plot area
        partials = self.option.get('partial_options') or []
        for p in partials:
            # Channel title
            height += 36  
            # Metadata lines
            meta_count = 0
            for kk, vv in p.items():
                meta_count += 1
            height += max(1, meta_count) * self.line_h
            # Plot area
            height += 160 
            height += self.section_gap

        # OTHER: Bottom padding
        height += 60
        height += self.padding
        
        return max(height, self.panel_rect.h)

    # Handle_event function:
    def handle_event(self, event):
        # Check for mouse click events
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Close button click
            if self.close_rect.collidepoint(event.pos):
                self.active = False
                return 'close'
        
        # Check for scroll mouse wheel events
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 30
            

        # Update the visible area
        # Calculate visible area inside panel (account for padding)
        visible_h = max(10, self.panel_rect.h - 2 * self.padding)
        max_scroll = max(0, self.content_height - visible_h)
        
        # Limit scroll to valid range
        if self.scroll < 0:
            self.scroll = 0
        if self.scroll > max_scroll:
            self.scroll = max_scroll

    # Draw function:
    def draw(self, screen):
        # Background overlay
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        # Main panel (full screen usage)
        panel_rect = pygame.Rect(40, 40, self.screen_w - 80, self.screen_h - 80)
        pygame.draw.rect(screen, (250, 250, 250), panel_rect)
        pygame.draw.rect(screen, (0, 0, 0), panel_rect, 2)

        # Close button
        pygame.draw.rect(screen, (200, 50, 50), self.close_rect)
        txt = self.font.render('Tornar', True, (255, 255, 255))
        screen.blit(txt, (self.close_rect.x + 8, self.close_rect.y + (self.close_rect.h - txt.get_height())/2))

        # Content clip to panel
        clip = screen.get_clip()
        screen.set_clip(panel_rect)

        # Starting position for content (account for padding and scroll)
        x = panel_rect.x + self.padding
        y = panel_rect.y + self.padding - self.scroll

        # General section
        title = f"Option {self.option.get('complete_option_id', '')}"
        title_surf = self.font.render(title, True, (0, 0, 180))
        screen.blit(title_surf, (x, y))
        y += 40

        # General Metadata 
        meta_keys = ['chans_needed', 'f_start', 'f_end', 'is_complete']
        for k in meta_keys:
            v = self.option.get(k, '')
            line = f"{k}: {v}"
            surf = self.font.render(line, True, (0, 0, 0))
            screen.blit(surf, (x, y))
            y += self.line_h

        # General plot 
        from UI_components.plot import Plot
        plot_h = 200
        plot_rect = pygame.Rect(x, y + 8, panel_rect.w - self.padding*2, plot_h)
        plotter = Plot(self.font) # Plot representation explained in plot.py
        plotter.draw(screen, plot_rect, self.option)
        y = plot_rect.bottom + self.section_gap

        # INDIVIDUAL CHANNEL SECTIONS
        partials = self.option.get('partial_options') or []
        def get_partial_id(pp, i):
            # Assist function to get the id of a partial option
            return pp.get('partial_option_id') or pp.get('id') or pp.get('partial_id') or i

        for idx, pp in enumerate(partials):
            # Channel title
            id = get_partial_id(pp, idx)
            ch_title = f"Channel {idx} - id: {id}"
            ch_surf = self.font.render(ch_title, True, (0, 0, 0))
            screen.blit(ch_surf, (x, y))
            y += 28 # padding

            # Channel metadata:
            for kk, vv in pp.items():
                # skip nested large structures by summarizing
                if isinstance(vv, (list, dict)):
                    val_str = f"<{type(vv).__name__} len={len(vv) if hasattr(vv, '__len__') else '?'}>"
                else:
                    val_str = str(vv)
                line = f"{kk}: {val_str}"
                # truncate long lines
                if len(line) > 120:
                    line = line[:117] + '...'
                surf = self.font.render(line, True, (50, 50, 50))
                screen.blit(surf, (x, y))
                y += self.line_h

            # Channel plot: draw only this partial using the Plot helper
            ch_plot_h = 200
            ch_plot_rect = pygame.Rect(x, y + 8, panel_rect.w - self.padding*2, ch_plot_h)
            plotter.draw(screen, ch_plot_rect, self.option, currentPartialOption=get_partial_id(pp, idx))
            
            # Draw Nyquist zones for this partial option
            plotter.addNyquistZones(screen, ch_plot_rect, pp)
            
            # Add small gap before next channel section
            y = ch_plot_rect.bottom + self.section_gap

        screen.set_clip(clip)
