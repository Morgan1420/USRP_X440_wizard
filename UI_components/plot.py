import pygame


class Plot:
    def __init__(self, font, axis_min=0.0, axis_max=4e9):
        self.font = font
        self.axis_min = axis_min
        self.axis_max = axis_max

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
