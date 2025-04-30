import gi, os, csv, openpyxl, shutil, datetime, re, subprocess
import numpy as np
os.environ["GDK_RENDERING"] = "gl"
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk, GdkPixbuf, GLib
from PIL import Image, ImageDraw
from typing import List, Tuple
import client

BASE_PATH = os.path.realpath(os.path.dirname(__file__))

def expand(filename: str):
    return os.path.join(BASE_PATH, filename)

def np2pixbuf(nda: np.ndarray) -> GdkPixbuf.Pixbuf:
    return GdkPixbuf.Pixbuf.new_from_data(
        nda.tobytes(), GdkPixbuf.Colorspace.RGB,
        False, 8, nda.shape[1], nda.shape[0], nda.shape[1] * 3)

# Load drone images as PIL images (ensure they are small e.g. 20x20 px)
disco_icon = Image.open(expand("DiscoveryDrone_Transparent.png")).convert("RGBA")
disco_icon = disco_icon.resize((50, 50), Image.Resampling.LANCZOS)  # Resize to 20x20 pixels

rogue_icon = Image.open(expand("RogueDrone_Transparent.png")).convert("RGBA")
rogue_icon = rogue_icon.resize((50, 50), Image.Resampling.LANCZOS)  # Resize to 20x20 pixels
    
# Define reference points for the top-left, bottom-left, and top-right corners
LAT1, LON1 = 39.019045, -104.894301  # Top-left
LAT3 = 39.017430  # Bottom-left
LON2 = -104.892113  # Top-right
LAT_RANGE = LAT1 - LAT3
LON_RANGE = LON2 - LON1

clean_map_pil = Image.open(expand("Map.png")).convert("RGB")
clean_map_np = np.array(clean_map_pil)
clean_map_pixbuf = np2pixbuf(clean_map_np)
clean_map_np = None
HEIGHT = clean_map_pil.height
WIDTH = clean_map_pil.width
LAT_PER_PIX = LAT_RANGE / HEIGHT
LON_PER_PIX = LON_RANGE / WIDTH

# Start IPC client
client.start()
    
def plot_icons(image: Image.Image, icon: Image.Image, coordinates: List[Tuple[float, float]]):
    lat, lon = coordinates[-1]
    pixel_x = round((lon - LON1) / LON_PER_PIX)
    pixel_y = round((LAT1 - lat) / LAT_PER_PIX)
    image.paste(icon, (pixel_x - icon.width // 2, pixel_y - icon.height // 2), mask=icon)

def clean_coordinate(value: int | float | str):
    """
    Cleans a coordinate string by ensuring correct decimal placement and preventing unnecessary float rounding.
    """
    if isinstance(value, (int, float)):
        return float(value)  # If it's already a valid number, return as-is

    if isinstance(value, str):
        value = value.strip().replace(" ", "")
        # Ensure it follows the correct format (detect negative and decimal)
        match = re.search(r"-?\d+\.\d+", value)
        if match:
            return float(match.group())  # Convert to float while preserving precision

    return np.nan

def read_coordinates(file_path: str) -> List[Tuple[float, float]]:
    """
    Reads latitude and longitude coordinates from a CSV or Excel (.xlsx) file.
    Supports formats with BREAK lines and standard telemetry headers.
    """
    coordinates: List[Tuple[float, float]] = []

    try:
        filename = file_path.lower()
        if filename.endswith(".xlsx") or filename.endswith(".xlsm"):
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active

            for row in sheet.iter_rows(values_only=True):
                if len(row) < 3 or row[1] is None or row[2] is None:
                    continue
                latitude = clean_coordinate(row[1])
                longitude = clean_coordinate(row[2])
                if latitude is not np.nan and longitude is not np.nan:
                    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                        coordinates.append((latitude, longitude))

        elif file_path.lower().endswith(".csv"):
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = []
                for row in reader:
                    if not row or row[0].startswith("BREAK"):
                        continue

                    # Update headers if it's a header row
                    if row[0].strip() == "Time" and "Latitude" in row and "Longitude" in row:
                        headers = row
                        continue

                    if len(headers) >= 3:
                        try:
                            lat_idx = headers.index("Latitude")
                            lon_idx = headers.index("Longitude")

                            lat_value = row[lat_idx]
                            lon_value = row[lon_idx]

                            latitude = clean_coordinate(lat_value)
                            longitude = clean_coordinate(lon_value)

                            if latitude is not np.nan and longitude is not np.nan:
                                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                                    coordinates.append((latitude, longitude))
                        except Exception as e:
                            print(f"Skipping row: {row} due to error: {e}")

        else:
            print("Unsupported file extension")
        return coordinates

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

class MyWindow(Gtk.Window):
    def refresh_image(self, pixbuf: GdkPixbuf.Pixbuf):
        """
        Refreshes the displayed map image.
        """
        try:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.map_image_widget.set_paintable(texture)

            self.content_area.queue_draw()
        except Exception as e:
            print(f"Error refreshing image: {e}")

    def __init__(self, app: Gtk.Application):
        super().__init__(title="C-UAS Interface 2025")
        self.set_default_size(1000, 600)
        self.set_application(app)  # Link the window to the application

        self.auto_reload = True

        #### C H A N G E S ####
        # Store coordinates
        self.rogue_coordinates = []
        self.discovery_coordinates = []

        # Initialize counters for save operations
        self.discovery_save_counter = 1

        def create_legend_item(icon_path: str, text: str):
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            icon = Gtk.Image.new_from_file(icon_path)
            icon.set_size_request(50, 50)
            label = Gtk.Label(label=text, halign=Gtk.Align.START)
            item_box.append(icon)
            item_box.append(label)
            return item_box
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_hexpand(True)
        main_box.set_vexpand(True)
        self.set_child(main_box)

        # ------------------------ Left Side Panel -----------------------
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_panel.set_size_request(300, -1)
        left_panel.add_css_class("side-panel")
        left_panel.set_vexpand(True)
        self.left_panel = left_panel

        # Legend Frame
        legend_frame = Gtk.Frame()
        legend_frame.add_css_class("title-frame")
        legend_label = Gtk.Label(label="Legend", halign=Gtk.Align.CENTER)
        legend_frame.set_child(legend_label)
        left_panel.append(legend_frame)
        legend_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        legend_box.set_margin_top(10)

        # Add Legend Items
        legend_box.append(create_legend_item(expand("drone_reboot.png"), "Booting Drone"))
        legend_box.append(create_legend_item(expand("DiscoveryDrone_Transparent.png"), "Discovery Drone"))
        legend_box.append(create_legend_item(expand("RogueDrone_Transparent.png"),"Rogue Drone"))
        legend_box.append(create_legend_item(expand("FortemRadar.png"),"Radar"))
        legend_box.append(create_legend_item(expand("GCS.png"),"Ground Station"))
        left_panel.append(legend_box)

        main_box.append(left_panel)
        
        # ----------------------- Main Content Area ----------------------
        self.content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_area.add_css_class("content-area")
        self.content_area.set_hexpand(True)
        self.content_area.set_vexpand(True)
        main_box.append(self.content_area)

        self.map_image_widget = Gtk.Picture()
        self.map_image_widget.set_hexpand(True)
        self.map_image_widget.set_vexpand(True)
        self.content_area.append(self.map_image_widget)
        self.refresh_image(clean_map_pixbuf)

        # ----------------------- Right Side Panel ----------------------
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right_panel.set_size_request(300, -1)
        right_panel.add_css_class("side-panel")
        right_panel.set_vexpand(True)

        # Controls Frame
        title_frame = Gtk.Frame()
        title_frame.add_css_class("title-frame")
        right_panel_title = Gtk.Label(label="Controls", halign=Gtk.Align.CENTER)
        title_frame.set_child(right_panel_title)
        right_panel.append(title_frame)

        # Buttons
        BUTTONS: List[Tuple[str, function, str]] = [
            ("Replay Points", self.on_replay_button_clicked, "large-button"),
            ("Save Rogue Coordinates", self.on_save_rogue_coords_clicked, "save-button"),
            ("Save Discovery Coordinates", self.on_save_discovery_coords_clicked, "save-button"),
            ("Clear Map", self.on_clear_map_clicked, "save-button"),
            ("Reload Data", self.on_reload_data_clicked, None),
            ("Start Record", self.on_start_flight_button_clicked, "large-button")
        ]

        for label, handler, css_class in BUTTONS:
            btn = Gtk.Button(label=label)
            btn.set_margin(10)
            btn.set_size_request(200, 60)
            if css_class:
                btn.add_css_class(css_class)
            btn.connect("clicked", handler)
            right_panel.append(btn)

        main_box.append(right_panel)
        self.apply_css()  # Apply CSS once during initialization

    CSS = b"""
        .side-panel { border: 2px solid black; padding: 10px; }
        .content-area { border: 2px solid blue; padding: 10px; }
        .title-frame { background-color: #a9a9a9; border: 2px solid black; padding: 5px; }
        label { font-weight: bold; }
        .large-button, .save-button { padding: 20px; font-size: 18px; }
        .status-label { padding: 10px; border-radius: 5px; color: white; font-weight: bold; }
        .status-ok { background-color: #4CAF50; }
        .status-error { background-color: #F44336; }
        """
            
    def apply_css(self):
        """
        Applies custom CSS styling once during initialization.
        """
        try:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(self.CSS)
            display = Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception as e:
            print(f"Error applying CSS: {e}")

    def on_clear_map_clicked(self, button):
        """
        Clears the map by resetting it to the base image.
        """
        print("Clear Map button clicked.")
        self.clear_map()
        self.auto_reload = False

    def clear_map(self):
        """
        Resets map to original image.
        """
        try:
            self.refresh_image(clean_map_pixbuf)
            self.content_area.queue_draw()
        except Exception as e:
            print(f"Error clearing map: {e}")

    def on_reload_data_clicked(self, button):
        """
        Re-enables auto-reload and updates the map.
        """
        print("Reload Data button clicked. Enabling auto-reload.")
        self.auto_reload = False
        self.discovery_coordinates, self.rogue_coordinates = client.getVals()
        self.update_map(self.rogue_coordinates, self.discovery_coordinates)
        self.auto_reload = True

    def on_save_rogue_coords_clicked(self, button):
        """
        Copies RogueCoords.csv with timestamp.
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(
                expand("RogueCoords.csv"),
                expand(f"RogueCoords_Copy_{timestamp}.csv")
            )
            print(f"Saved RogueCoords copy")
        except Exception as e:
            print(f"Error copying RogueCoords: {e}")

    def on_save_discovery_coords_clicked(self, button):
        """
        Copies DiscoveryCoords.csv with counter.
        """
        try:
            new_file = expand(f"discovery_coords_copy_{self.discovery_save_counter}.csv")
            shutil.copy(expand("DiscoveryCoords.csv"), new_file)
            print(f"Saved discovery coordinates copy {self.discovery_save_counter}")
            self.discovery_save_counter += 1
        except Exception as e:
            print(f"Error saving discovery coordinates: {e}")

    def on_start_flight_button_clicked(self, button):
        try:
            subprocess.Popen(["/home/dfec/camera_start.sh"])
            print("Camera script started.")
        except Exception as e:
            print(f"Failed to start script: {e}")

    def on_replay_button_clicked(self, button):
        """
        Handles replay file selection.
        """
        dialog = Gtk.Dialog(transient_for=self, modal=True, title="Select a Replay Save File")
        dialog.set_default_size(300, 150)
        file_dropdown = Gtk.ComboBoxText()
        file_dropdown.append_text("RogueCoords_Downsampled_Every5.csv")
        file_dropdown.set_active(0)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin(20)
        box.append(file_dropdown)
        dialog.get_content_area().append(box)
        dialog.add_buttons("OK", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL)
        dialog.connect("response", lambda d, r: self.handle_reply_response(d, r, file_dropdown))
        dialog.show()

    def handle_reply_response(self, dialog: Gtk.Dialog, response: Gtk.ResponseType, file_dropdown: Gtk.ComboBoxText):
        if response == Gtk.ResponseType.OK:
            selected_file = file_dropdown.get_active_text()
            if selected_file:
                self.replay_points(selected_file, "replay_drone")
        dialog.destroy()

    def start_csv_monitoring(self):
        """
        Starts background CSV monitoring.
        """
        def monitor_changes():
            if self.auto_reload:
                try:
                    self.discovery_coordinates, self.rogue_coordinates = client.getVals()
                    GLib.idle_add(self.update_map, self.rogue_coordinates, self.discovery_coordinates)
                except Exception as e:
                    print(f"Monitoring error: {e}")
        GLib.timeout_add(100, monitor_changes)
        

    def update_map(self, rogue_coordinates: List[Tuple[float, float]], discovery_coordinates: List[Tuple[float, float]]):
        """
        Updates the map with rogue and discovery coordinates.
        """
        try:
            pil_image = clean_map_pil.copy()
            draw = ImageDraw.Draw(pil_image)

            # Function to plot points
            def plot_point(coordinate: Tuple[float, float], color: str):
                latitude, longitude = coordinate
                if not (LAT3 <= latitude <= LAT1) or not (LON1 <= longitude <= LON2):
                    print(f"Warning: Latitude {latitude} or Longitude {longitude} out of bounds.")
                    return None
                pixel_x = int((longitude - LON1) / LON_PER_PIX)
                pixel_y = int((LAT1 - latitude) / LAT_PER_PIX)
                draw.ellipse((pixel_x - 5, pixel_y - 5, pixel_x + 5, pixel_y + 5), fill=color, outline="black")

            # Plot all but the last rogue coordinate as circles
            for coord in rogue_coordinates[:-1]:
                plot_point(coord, "red")

            # Plot last rogue coordinate with the rogue drone image
            if rogue_coordinates:
                plot_icons(pil_image, rogue_icon, rogue_coordinates)

            # Same for discovery
            for coord in discovery_coordinates[:-1]:
                plot_point(coord, "green")

            if discovery_coordinates:
                plot_icons(pil_image, disco_icon, discovery_coordinates)

            # Convert back to Pixbuf for GTK
            updated_array = np.array(pil_image)
            updated_pixbuf = np2pixbuf(updated_array)
            texture = Gdk.Texture.new_for_pixbuf(updated_pixbuf)

            # Update the Gtk.Picture widget
            self.map_image_widget.set_paintable(texture)
            self.content_area.queue_draw()
        except Exception as e:
            print(f"Error updating map: {e}")
    
    def replay_points(self, file_name: str, drone_name: str):
        """
        Replays saved flight path from a selected file.
        """
        try:
            print(f"Replay initiated for {drone_name} drone with file: {file_name}")
            self.auto_reload = False  
            print("Auto-reload permanently disabled during replay.")

            # Load coordinates
            coordinates = read_coordinates(file_name)
            if len(coordinates) == 0:
                print(f"No coordinates found in {file_name}")
                return

            print(f"Loaded {len(coordinates)} points from {file_name}")

            # Load a fresh copy of the base map as the replay canvas
            self.replay_map_image = clean_map_pil.copy()
            draw = ImageDraw.Draw(self.replay_map_image)

            # Store coordinates and initialize index
            self.replay_coordinates = coordinates
            self.replay_index = 0

            def plot_next_point():
                if self.replay_index < len(self.replay_coordinates):
                    lat, lon = self.replay_coordinates[self.replay_index]
                    print(f"Plotting {drone_name} point {self.replay_index + 1}/{len(self.replay_coordinates)}: ({lat}, {lon})")

                    # Convert to pixels
                    pixel_x, pixel_y = self.convert_to_pixels(lat, lon)

                    # Draw point
                    draw.ellipse((pixel_x - 5, pixel_y - 5, pixel_x + 5, pixel_y + 5), fill="red", outline="black")

                    # Draw connecting path
                    if self.replay_index > 0:
                        prev_lat, prev_lon = self.replay_coordinates[self.replay_index - 1]
                        prev_x, prev_y = self.convert_to_pixels(prev_lat, prev_lon)
                        draw.line([(prev_x, prev_y), (pixel_x, pixel_y)], fill="red", width=2)

                    # Update map widget with current replay frame
                    updated_array = np.array(self.replay_map_image)
                    updated_pixbuf = np2pixbuf(updated_array)
                    texture = Gdk.Texture.new_for_pixbuf(updated_pixbuf)
                    self.map_image_widget.set_paintable(texture)
                    self.content_area.queue_draw()

                    self.replay_index += 1
                    return True  # Keep replaying
                else:
                    print(f"{drone_name.capitalize()} Drone Replay completed.")
                    return False  # Stop replay

            # Start the timed animation
            GLib.timeout_add(200, plot_next_point)

        except Exception as e:
            print(f"Error in replay_points: {e}")

    def convert_to_pixels(self, lat: float, lon: float):
        """
        Converts latitude and longitude to pixel coordinates on the map.
        Ensures correct scaling so points are mapped accurately.
        """

        # Get map dimensions (match your actual base image size)
        # width, height = 1000, 600  # Adjust these values to match the base image

        # Convert lat/lon to pixel coordinates
        try:
            pixel_x = round(((lon - LON1) / LON_RANGE) * WIDTH)
            pixel_y = round(((LAT1 - lat) / LAT_RANGE) * HEIGHT)

            # print(f"Lat: {lat}, Lon: {lon} -> Pixel: ({pixel_x}, {pixel_y})")  # Debugging output
            return pixel_x, pixel_y
        except Exception as e:
            print(f"Error in convert_to_pixels: {e}")
            return int(0), int(0)  # Return (0,0) if an error occurs

class MyApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.myapp", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = MyWindow(self)
        win.present()
        win.start_csv_monitoring()

def main():
    app = MyApp()
    app.run(None)

if __name__ == "__main__":
    main()