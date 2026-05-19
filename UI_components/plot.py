import pygame


class Plot:
    def __init__(self, font, axis_min=0.0, axis_max=4e9):
        self.font = font
        self.axis_min = axis_min
        self.axis_max = axis_max

    def _axis_geometry(self, rect):
        margin = max(20, int(rect.w * 0.04))
        axis_start = rect.x + margin
        axis_end = rect.right - margin
        axis_w = axis_end - axis_start
        return axis_start, axis_end, axis_w, margin

    def freq_to_x(self, f, rect):
        try:
            fv = float(f)
        except Exception:
            fv = self.axis_min
        t = (fv - self.axis_min) / (self.axis_max - self.axis_min) if (self.axis_max - self.axis_min) != 0 else 0
        t = max(0.0, min(1.0, t))
        return int(rect.x + t * rect.w)

    def draw(self, surface, rect, option, currentPartialOption=None):
        # Clear plot area and draw a simple bottom X axis with ticks at 1G..4G
        pygame.draw.rect(surface, (245, 245, 245), rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 1)

        # Baseline (X axis) near bottom of rect with horizontal margins
        axis_y = rect.bottom - 28
        margin = max(20, int(rect.w * 0.04))
        axis_start = rect.x + margin
        axis_end = rect.right - margin
        pygame.draw.line(surface, (0, 0, 0), (axis_start, axis_y), (axis_end, axis_y), 2)

        # Small ticks: much smaller, half below axis. Labels slightly lower to avoid overlap
        tick_total = max(8, rect.h // 8)
        below = tick_total // 2
        label_y = axis_y + 10
        axis_w = axis_end - axis_start

        # helper to map any frequency to axis coordinates (respecting margins)
        def map_to_axis(f):
            try:
                fv = float(f)
            except Exception:
                fv = self.axis_min
            t = (fv - self.axis_min) / (self.axis_max - self.axis_min) if (self.axis_max - self.axis_min) != 0 else 0
            t = max(0.0, min(1.0, t))
            return int(axis_start + t * axis_w)

        for g in range(1, 5):
            t = (g * 1e9 - self.axis_min) / (self.axis_max - self.axis_min) if (self.axis_max - self.axis_min) != 0 else 0
            t = max(0.0, min(1.0, t))
            fx = int(axis_start + t * axis_w)
            top_y = axis_y - (tick_total - below)
            bottom_y = axis_y + below
            pygame.draw.line(surface, (0, 0, 0), (fx, top_y), (fx, bottom_y), 2)
            lbl = self.font.render(f"{g}G", True, (0, 0, 0))
            surface.blit(lbl, (fx - lbl.get_width()//2, label_y))

        # Partial list (used for legend decision)
        partials = option.get('partial_options') or []

        # Legend (top-left of plot)
        legend_x = rect.x + margin + 6
        legend_y = rect.y + 6
        box_size = 12
        gap = 6
        entries = [((200, 40, 40), "red box = desired bandwidth"),
                   ((60, 130, 220), "blue box = different channels")]
        # show gray entry only when a single partial is requested and has fcr_ghz
        show_gray = False
        if currentPartialOption is not None:
            for idx, p in enumerate(partials):
                try:
                    pid = partial_id(p, idx)
                except Exception:
                    pid = idx
                if str(pid) == str(currentPartialOption) and p.get('fcr_ghz') is not None:
                    show_gray = True
                    break
        if show_gray:
            entries.append(((120, 120, 120), "gray box = Nyquist zones"))

        for color, text in entries:
            pygame.draw.rect(surface, color, (legend_x, legend_y, box_size, box_size))
            lbl = self.font.render(text, True, (0, 0, 0))
            surface.blit(lbl, (legend_x + box_size + 6, legend_y - 2))
            legend_y += box_size + gap

        # Draw interest bandwidth as a red box if provided in option
        opt_fstart = option.get('f_start')
        opt_fend = option.get('f_end')
        if opt_fstart is not None and opt_fend is not None:
            rx1 = map_to_axis(opt_fstart)
            rx2 = map_to_axis(opt_fend)
            # clamp to axis area
            rx1 = max(axis_start, min(axis_end, rx1))
            rx2 = max(axis_start, min(axis_end, rx2))
            if rx2 <= rx1:
                rx2 = rx1 + 2
            # make the red band taller and align its bottom with the axis line
            band_h = max(80, rect.h // 4)
            band_y = axis_y - band_h
            band_surf = pygame.Surface((rx2 - rx1, band_h), pygame.SRCALPHA)
            band_surf.fill((200, 40, 40, 160))
            surface.blit(band_surf, (rx1, band_y))
            pygame.draw.rect(surface, (160, 30, 30), (rx1, band_y, rx2 - rx1, band_h), 2)

        # Draw partial options (blue boxes)
        partials = option.get('partial_options') or []

        # helper to determine id of partial
        def partial_id(p, idx):
            return p.get('partial_option_id') or p.get('id') or p.get('partial_id') or idx

        # select which partials to draw
        draw_partials = []
        if currentPartialOption is None:
            draw_partials = list(enumerate(partials))
        else:
            for idx, p in enumerate(partials):
                if str(partial_id(p, idx)) == str(currentPartialOption):
                    draw_partials = [(idx, p)]
                    break

        for idx, p in draw_partials:
            pf1 = p.get('f_start')
            pf2 = p.get('f_end')
            if pf1 is None or pf2 is None:
                continue
            x1 = map_to_axis(pf1)
            x2 = map_to_axis(pf2)
            # clamp to axis area
            x1 = max(axis_start, min(axis_end, x1))
            x2 = max(axis_start, min(axis_end, x2))
            if x2 <= x1:
                x2 = x1 + 2

            # determine number of subchannels for this partial
            num_sub = 1
            if isinstance(p.get('channels'), list):
                num_sub = max(1, len(p.get('channels')))
            else:
                for k in ('num_channels', 'num_chans', 'chans', 'chans_needed', 'n_chans'):
                    if k in p:
                        try:
                            num_sub = max(1, int(p.get(k)))
                        except Exception:
                            pass
                        break

            # if partial contains multiple channels, split the band into equal pieces
            total_w = x2 - x1
            piece_w = max(2, total_w // num_sub)
            blue_h = max(36, rect.h // 3)  # taller than red
            base_y = axis_y - blue_h

            for s in range(num_sub):
                sx1 = x1 + s * piece_w
                sx2 = sx1 + piece_w if s < num_sub - 1 else x2
                bw = max(2, sx2 - sx1)
                blue_surf = pygame.Surface((bw, blue_h), pygame.SRCALPHA)
                blue_surf.fill((60, 130, 220, 140))
                surface.blit(blue_surf, (sx1, base_y))
                # simple rectangular outline only (no roof)
                pygame.draw.rect(surface, (20, 80, 140), (sx1, base_y, bw, blue_h), 2)

    def addNyquistZones(self, surface, rect, partial):
        # Draw repeated boxes above the axis that span the full axis width.
        # Box frequency length = 0.5 * fcr_ghz (converted to Hz).
        
        fcr = partial.get('fcr_ghz')
        
        fcr_val = float(fcr)

        freq_box_hz = 0.5 * fcr_val * 1e9

        axis_start, axis_end, axis_w, margin = self._axis_geometry(rect)
        if axis_w <= 0 or (self.axis_max - self.axis_min) == 0:
            return

        # pixels per Hz on axis
        pph = axis_w / (self.axis_max - self.axis_min)
        px_box_w = max(2, int(freq_box_hz * pph))

        # box visual parameters
        axis_y = rect.bottom - 28
        box_h = max(30, rect.h // 10)
        box_y = axis_y - box_h

        # draw boxes across the full axis range
        x = axis_start
        while x < axis_end:
            w = min(px_box_w, axis_end - x)
            box_surf = pygame.Surface((w, box_h), pygame.SRCALPHA)
            box_surf.fill((120, 120, 120, 120))
            surface.blit(box_surf, (x, box_y))
            pygame.draw.rect(surface, (90, 90, 90), (x, box_y, w, box_h), 1)
            x += px_box_w
