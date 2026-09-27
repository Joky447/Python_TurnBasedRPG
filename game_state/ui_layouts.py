"""Where things are on the menu_ui mockups, in the mockup's own pixels (x0, y0, x1, y1).

tools/make_ui_templates.py uses these to erase the changing parts of each mockup,
and the screens use them (scaled to the window) to draw live content in the same spots.
"""
import pygame

CREATE = {
    "art": "menu_ui/character selection ui.png",
    "size": (1673, 940),
    "btn_boy": (175, 322, 448, 403), "erase_boy": (212, 336, 420, 390, "row"),
    "btn_girl": (452, 324, 715, 402), "erase_girl": (490, 336, 690, 390, "row"),
    "btn_sword": (172, 512, 449, 598), "erase_sword": (208, 526, 420, 584, "row"),
    "btn_sorc": (452, 515, 716, 594), "erase_sorc": (490, 526, 690, 584, "row"),
    "icon_male": (234, 336, 286, 390), "icon_female": (523, 336, 568, 392),
    "icon_sword": (208, 524, 266, 590), "icon_staff": (498, 524, 554, 586),
    "weapon_icon_art": (1218, 267, 1287, 337),
    "blurb": (190, 612, 640, 675),
    "preview_feet": (978, 668),            # x = middle of the pedestal
    "preview_stage": (782, 232, 1192, 728),
    "weapon_icon": (1222, 270, 1284, 334),
    "weapon_text": (1298, 262),
    "skill_gems": [(1263, 408), (1263, 497), (1263, 585), (1263, 673)],
    "skill_text": [(1312, 380), (1312, 468), (1312, 556), (1312, 644)],
    "name_label": (140, 192), "name_box": (250, 172, 750, 214),
    "confirm": (626, 772, 1050, 862),
    "erase_figure": (866, 320, 1116, 668),
    # see-through panel areas (the pedestal scene between them stays solid)
    "glass": [(136, 228, 746, 718), (1196, 228, 1592, 734)],   # the sample character: only its outline is erased
    "erase": [
        (185, 610, 645, 680),                  # class blurb

        (1222, 270, 1284, 334),                     # weapon icon
        (1296, 258, 1565, 346),               # weapon name + stats
        (1247, 392, 1280, 425), (1247, 481, 1280, 514), (1247, 569, 1280, 602), (1247, 657, 1280, 690),  # skill icons
        (1305, 376, 1576, 442), (1305, 464, 1576, 530), (1305, 552, 1576, 618),
        (1305, 640, 1576, 708),  # skill text
    ],
}

CAMP = {
    "art": "menu_ui/base camp ui.png",
    "size": (1664, 945),
    "title": (596, 14, 1066, 112), "title_letters_bottom": 93,   # "BASE CAMP" and its underline
    "menu_btn": (42, 30, 308, 97), "erase_menu_label": (74, 46, 276, 82, "row"),
    "tab_skills": (705, 168, 898, 230), "erase_tab_skills": (742, 180, 868, 218, "row"),
    "tab_equipment": (902, 166, 1138, 232), "erase_tab_equipment": (938, 178, 1102, 220, "row"),
    "btn_selected": (356, 666, 502, 722), "erase_btn_selected": (382, 678, 478, 710, "row"),
    "btn_delete": (508, 668, 634, 720), "erase_btn_delete": (530, 678, 614, 710, "row"),
    "slot_boxes": [(722, 266, 888, 452), (898, 266, 1064, 452), (1075, 266, 1248, 452),
                   (1253, 266, 1418, 452), (1425, 266, 1590, 452)],
    "erase_slot_inner": [(738, 282, 872, 436), (914, 282, 1048, 436), (1093, 284, 1230, 434),
                         (1269, 282, 1402, 436), (1441, 282, 1574, 436)],
    "create_btn": (65, 770, 622, 853), "erase_create_label": (205, 788, 520, 836, "row"),
    "roster_rows": [(55, 645, 642, 748), (55, 760, 642, 863)],
    "roster_header": (78, 626),
    "sprite_feet": (185, 548),
    "sprite_stage": (48, 150, 355, 600),
    "name": (365, 160), "class": (365, 212),
    "stat_right": 628,     # the stat column's text must end before the panel's frame
    "stat_values": [(416, 292), (416, 352), (416, 416), (416, 478), (416, 540)],
    "stat_labels": [(416, 270), (416, 330), (416, 394), (416, 456), (416, 518)],
    "stat_icons": [(382, 290), (382, 346), (382, 410), (382, 472), (382, 538)],
    "divider": (365, 600, 253),
    "inventory_header": (782, 484),
    "inventory_area": (730, 540, 1570, 742),
    "begin_btn": (895, 795, 1405, 870), "begin_text_x": 1010,
    "glass": [(40, 145, 648, 872), (696, 158, 1604, 770)],   # see-through panel areas
    "erase": [
        (50, 150, 636, 494), (352, 494, 636, 596),  # sample character, name, class and stats (redrawn in code)
        (46, 480, 360, 604, 16),                    # her boots and the pedestal (a platform is drawn in code)
        (72, 608, 238, 644),                   # "Roster (1/2)"
        (64, 654, 634, 740),                   # roster row contents
        (50, 763, 638, 862),               # "Create New Character" button
        (705, 168, 1142, 234),                # tabs
        (712, 258, 1592, 462),                      # equipment slots
        (778, 480, 952, 522),                       # "Inventory (0)"
        (722, 532, 1576, 748),                 # inventory contents
        (1004, 810, 1370, 856, "row"),        # "Begin Adventure as ..." label
    ],
    "erase_right_content": (705, 242, 1596, 766),
}


class ArtLayout:
    """Converts mockup coordinates to window coordinates."""

    def __init__(self, layout: dict, screen_size: tuple[int, int]):
        self.layout = layout
        self.sx = screen_size[0] / layout["size"][0]
        self.sy = screen_size[1] / layout["size"][1]

    def rect(self, r) -> pygame.Rect:
        x0, y0, x1, y1 = r
        return pygame.Rect(round(x0 * self.sx), round(y0 * self.sy), round((x1 - x0) * self.sx), round((y1 - y0) * self.sy))

    def point(self, p) -> tuple[int, int]:
        return round(p[0] * self.sx), round(p[1] * self.sy)

    def size(self, v) -> int:
        return max(1, round(v * self.sy))

    def __getitem__(self, key):
        return self.layout[key]
