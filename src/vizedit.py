import cv2
import json
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk

image_path = r'data/images/v1/flowchart_page_3.png'
json_path = r'data/jsonf/flowchart_page_3_roboflow.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

img = cv2.imread(image_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Resize image for GUI
max_w, max_h = 1200, 800
h, w = img_rgb.shape[:2]
scale = min(max_w / w, max_h / h, 1.0)
new_w, new_h = int(w * scale), int(h * scale)
img_resized = cv2.resize(img_rgb, (new_w, new_h))
img_pil = Image.fromarray(img_resized)

class BoxEditor(tk.Tk):
    def __init__(self, img_pil, predictions, scale):
        super().__init__()
        self.title("Flowchart Box Editor")
        self.img_tk = ImageTk.PhotoImage(img_pil)
        self.canvas = tk.Canvas(self, width=self.img_tk.width(), height=self.img_tk.height())
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
        self.predictions = predictions
        self.scale = scale
        self.box_items = []
        self.arrows = data.get('arrows', [])
        self.arrow_items = []

        # Shape count label (move this up!)
        self.shape_count_label = tk.Label(self, text="")
        self.shape_count_label.pack(side=tk.TOP)

        # Now it's safe to call these:
        self.draw_boxes()
        self.draw_arrows()
        self.canvas.bind("<Button-1>", self.on_click)

        # Store buttons as instance variables
        self.btn_save = tk.Button(self, text="Save JSON", command=self.save_json)
        self.btn_save.pack(side=tk.LEFT)
        self.btn_add = tk.Button(self, text="Add Box", command=self.start_add_box)
        self.btn_add.pack(side=tk.LEFT)
        self.btn_resize = tk.Button(self, text="Resize Box", command=self.start_resize_box)
        self.btn_resize.pack(side=tk.LEFT)
        self.btn_remove = tk.Button(self, text="Remove Shape", command=self.start_remove_box)
        self.btn_remove.pack(side=tk.LEFT)
        self.btn_arrow = tk.Button(self, text="Add Arrow", command=self.start_add_arrow)
        self.btn_arrow.pack(side=tk.LEFT)
        self.btn_remove_arrow = tk.Button(self, text="Remove Arrow", command=self.start_remove_arrow)
        self.btn_remove_arrow.pack(side=tk.LEFT)

        # For adding box
        self.adding_box = False
        self.start_x = self.start_y = None
        self.temp_box = None

        # For resizing box
        self.resizing_box = False
        self.selected_box_idx = None
        self.selected_box = None
        self.selected_label = None
        self.resizing_corner = None

        # For removing box
        self.removing_box = False

        # For adding arrow
        self.adding_arrow = False
        self.arrow_start_idx = None

        # For removing arrow
        self.removing_arrow = False

        self.update_mode_buttons()
        self.update_shape_count()

    def update_mode_buttons(self):
        # Reset all to default
        default = self.btn_save.cget("bg")
        self.btn_add.config(bg=default)
        self.btn_resize.config(bg=default)
        self.btn_remove.config(bg=default)
        self.btn_arrow.config(bg=default)
        self.btn_remove_arrow.config(bg=default)
        # Highlight active mode
        active_color = "yellow"
        if self.adding_box:
            self.btn_add.config(bg=active_color)
        elif self.resizing_box:
            self.btn_resize.config(bg=active_color)
        elif self.removing_box:
            self.btn_remove.config(bg=active_color)
        elif self.adding_arrow:
            self.btn_arrow.config(bg=active_color)
        elif self.removing_arrow:
            self.btn_remove_arrow.config(bg=active_color)

    def update_shape_count(self):
        count = len([p for p in self.predictions if not p.get('deleted')])
        self.shape_count_label.config(text=f"Shapes: {count}")

    def draw_boxes(self):
        self.canvas.delete("all")  # Clear all items from canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)  # Redraw background
        self.box_items.clear()
        for i, pred in enumerate(self.predictions):
            if pred.get('deleted'):
                continue
            x1 = int((pred['x'] - pred['width'] / 2) * self.scale)
            y1 = int((pred['y'] - pred['height'] / 2) * self.scale)
            x2 = int((pred['x'] + pred['width'] / 2) * self.scale)
            y2 = int((pred['y'] + pred['height'] / 2) * self.scale)
            color = "red" if 'arrow' in pred['class'] else "green"
            box = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            label = self.canvas.create_text(x1+5, y1+15, anchor=tk.NW, text=pred['class'], fill=color)
            self.box_items.append((box, label, i))
        self.update_shape_count()

    def draw_arrows(self):
        for arrow in self.arrow_items:
            self.canvas.delete(arrow)
        self.arrow_items.clear()
        for idx, arrow in enumerate(self.arrows):
            start_idx, end_idx = arrow['from'], arrow['to']
            if start_idx >= len(self.predictions) or end_idx >= len(self.predictions):
                continue
            start_pred = self.predictions[start_idx]
            end_pred = self.predictions[end_idx]
            if start_pred.get('deleted') or end_pred.get('deleted'):
                continue
            x1 = int(start_pred['x'] * self.scale)
            y1 = int(start_pred['y'] * self.scale)
            x2 = int(end_pred['x'] * self.scale)
            y2 = int(end_pred['y'] * self.scale)
            arrow_item = self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="blue", width=2)
            self.arrow_items.append((arrow_item, (x1, y1, x2, y2), idx))

    def on_click(self, event):
        if self.adding_box:
            if self.start_x is None:
                self.start_x, self.start_y = event.x, event.y
                self.temp_box = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="blue", width=2)
                self.canvas.bind("<B1-Motion>", self.on_drag_add_box)
            else:
                end_x, end_y = event.x, event.y
                self.canvas.unbind("<B1-Motion>")
                self.canvas.delete(self.temp_box)
                x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
                x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
                cx = ((x1 + x2) / 2) / self.scale
                cy = ((y1 + y2) / 2) / self.scale
                w_box = abs(x2 - x1) / self.scale
                h_box = abs(y2 - y1) / self.scale
                new_pred = {
                    "x": cx,
                    "y": cy,
                    "width": w_box,
                    "height": h_box,
                    "class": ""
                }
                self.predictions.append(new_pred)
                self.draw_boxes()
                self.draw_arrows()
                self.adding_box = False
                self.start_x = self.start_y = None
                self.temp_box = None
        elif self.resizing_box:
            for box, label, idx in self.box_items:
                coords = self.canvas.coords(box)
                if coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]:
                    self.selected_box_idx = idx
                    self.selected_box = box
                    self.selected_label = label
                    corners = [(coords[0], coords[1]), (coords[2], coords[1]), (coords[2], coords[3]), (coords[0], coords[3])]
                    dists = [((event.x-x)**2 + (event.y-y)**2) for x, y in corners]
                    self.resizing_corner = dists.index(min(dists))
                    self.canvas.bind("<B1-Motion>", self.on_drag_resize_box)
                    break
        elif self.removing_box:
            for box, label, idx in list(self.box_items):
                coords = self.canvas.coords(box)
                if coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]:
                    self.predictions[idx]['deleted'] = True
                    # Just redraw everything; don't manually remove from box_items
                    self.draw_boxes()
                    self.draw_arrows()
                    self.update_shape_count()
                    break
        elif self.adding_arrow:
            # Select start and end shapes for arrow
            for box, label, idx in self.box_items:
                coords = self.canvas.coords(box)
                if coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]:
                    if self.arrow_start_idx is None:
                        self.arrow_start_idx = idx
                        self.canvas.itemconfig(box, outline="blue")
                    else:
                        arrow = {"from": self.arrow_start_idx, "to": idx}
                        self.arrows.append(arrow)
                        self.arrow_start_idx = None
                        self.draw_arrows()  # Only redraw arrows
                        # Do NOT call self.draw_boxes() here
                    break
        elif self.removing_arrow:
            # Remove arrow if clicked near it
            for arrow_item, coords, idx in list(self.arrow_items):
                x1, y1, x2, y2 = coords
                # Calculate distance from click to line segment
                px, py = event.x, event.y
                dist = self._point_line_distance(px, py, x1, y1, x2, y2)
                if dist < 10:  # threshold in pixels
                    self.canvas.delete(arrow_item)
                    self.arrows.pop(idx)
                    self.draw_arrows()
                    break

    def on_drag_add_box(self, event):
        if self.temp_box and self.start_x is not None and self.start_y is not None:
            self.canvas.coords(self.temp_box, self.start_x, self.start_y, event.x, event.y)

    def start_add_box(self):
        self.adding_box = True
        self.resizing_box = False
        self.removing_box = False
        self.adding_arrow = False
        self.removing_arrow = False
        self.start_x = self.start_y = None
        self.temp_box = None
        self.update_mode_buttons()

    def start_resize_box(self):
        self.resizing_box = True
        self.adding_box = False
        self.removing_box = False
        self.adding_arrow = False
        self.removing_arrow = False
        self.selected_box_idx = None
        self.selected_box = None
        self.selected_label = None
        self.resizing_corner = None
        self.update_mode_buttons()

    def start_remove_box(self):
        self.removing_box = True
        self.adding_box = False
        self.resizing_box = False
        self.adding_arrow = False
        self.removing_arrow = False
        self.update_mode_buttons()

    def start_add_arrow(self):
        self.adding_arrow = True
        self.adding_box = False
        self.resizing_box = False
        self.removing_box = False
        self.removing_arrow = False
        self.arrow_start_idx = None
        self.update_mode_buttons()

    def start_remove_arrow(self):
        self.removing_arrow = True
        self.adding_box = False
        self.resizing_box = False
        self.removing_box = False
        self.adding_arrow = False
        self.update_mode_buttons()

    def on_drag_resize_box(self, event):
        if self.selected_box is not None and self.selected_box_idx is not None:
            coords = self.canvas.coords(self.selected_box)
            if len(coords) == 4:
                # Update the selected corner
                if self.resizing_corner == 0:  # top-left
                    coords[0], coords[1] = event.x, event.y
                elif self.resizing_corner == 1:  # top-right
                    coords[2], coords[1] = event.x, event.y
                elif self.resizing_corner == 2:  # bottom-right
                    coords[2], coords[3] = event.x, event.y
                elif self.resizing_corner == 3:  # bottom-left
                    coords[0], coords[3] = event.x, event.y
                self.canvas.coords(self.selected_box, *coords)
                # Update label position
                self.canvas.coords(self.selected_label, coords[0]+5, coords[1]+15)
                # Update prediction
                x1, y1, x2, y2 = coords
                cx = ((x1 + x2) / 2) / self.scale
                cy = ((y1 + y2) / 2) / self.scale
                w_box = abs(x2 - x1) / self.scale
                h_box = abs(y2 - y1) / self.scale
                self.predictions[self.selected_box_idx]['x'] = cx
                self.predictions[self.selected_box_idx]['y'] = cy
                self.predictions[self.selected_box_idx]['width'] = w_box
                self.predictions[self.selected_box_idx]['height'] = h_box
            else:
                self.selected_box = None
                self.selected_label = None
                self.selected_box_idx = None
                self.resizing_corner = None
                self.canvas.unbind("<B1-Motion>")

    def save_json(self):
        filtered = [p for p in self.predictions if not p.get('deleted')]
        data_out = dict(data)
        data_out['predictions'] = filtered
        data_out['arrows'] = self.arrows
        with open(json_path.replace('.json', '_edited.json'), 'w', encoding='utf-8') as f:
            json.dump(data_out, f, indent=2)
        print("Saved edited JSON!")

    @staticmethod
    def _point_line_distance(px, py, x1, y1, x2, y2):
        # Compute distance from point (px,py) to line segment (x1,y1)-(x2,y2)
        from math import hypot
        line_mag = hypot(x2 - x1, y2 - y1)
        if line_mag < 1e-6:
            return hypot(px - x1, py - y1)
        u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)
        u = max(min(u, 1), 0)
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        return hypot(px - ix, py - iy)

if __name__ == "__main__":
    app = BoxEditor(img_pil, data['predictions'], scale)
    app.mainloop()