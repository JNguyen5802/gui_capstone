import gi
import webbrowser
import os
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
os.environ["GDK_RENDERING"] = "cairo"  # or "gl"
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk  # Import Gdk for applying the CSS
from PIL import Image, ImageDraw


class MyWindow(Gtk.Window):
    def __init__(self, app):
        super().__init__(title="C-UAS Interface 2025")
        self.set_default_size(1000, 600)
        self.set_application(app)  # Link the window to the application

        def create_legend_item(icon_path, text):
            # Create a horizontal box for the icon and label
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            # Create the icon image
            icon = Gtk.Image.new_from_file(icon_path)  # Replace with path to your icon image
            icon.set_size_request(30, 30)  # Set the icon size
            
            # Create the label
            label = Gtk.Label(label=text, halign=Gtk.Align.START)
            
            # Add the icon and label to the horizontal box
            item_box.append(icon)
            item_box.append(label)
            
            return item_box
        
        # Create the main container (a horizontal box) for the window content
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_hexpand(True)  # Allow horizontal expansion
        main_box.set_vexpand(True)  # Allow vertical expansion
        self.set_child(main_box)  # Set main_box as the main widget of the window

        # ------------------------ Left Side Panel -----------------------
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_panel.set_size_request(300, -1)  # Set a fixed width for the side panel
        left_panel.add_css_class("side-panel")  # Add a CSS class for styling
        left_panel.set_vexpand(True)  # Allow the side panel to expand vertically
        
        # Create a frame (rectangle) for the title and make it expand horizontally
        legend_frame = Gtk.Frame()
        legend_frame.add_css_class("title-frame")  # Add CSS class for further styling
        legend_label = Gtk.Label(label="Legend", halign=Gtk.Align.CENTER)
        legend_frame.set_child(legend_label)  # Add the label inside the frame
        left_panel.append(legend_frame)
        legend_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        legend_box.set_margin_top(10)

        #Add Items to the Legend
        legend_box.append(create_legend_item("/home/dfec/Pictures/Screenshots/drone_reboot.png","Booting Drone"))
        legend_box.append(create_legend_item("/home/dfec/Pictures/Screenshots/DiscoveryDrone.jpg","Discovery Drone"))
        legend_box.append(create_legend_item("/home/dfec/Pictures/Screenshots/RogueDrone.jpg","Rogue Drone"))
        legend_box.append(create_legend_item("/home/dfec/Pictures/Screenshots/FortemRadar.png","Radar"))
        legend_box.append(create_legend_item("/home/dfec/Pictures/Screenshots/GCS.png","Ground Station"))
        left_panel.append(legend_box)

        # #Progress Bar for DD
        # progress_bar_label = Gtk.Label(label="Discovery Drone Battery (%)", halign=Gtk.Align.CENTER)
        # left_panel.append(progress_bar_label)
        # self.progress_bar = Gtk.ProgressBar()
        # self.progress_bar.set_margin_top(10)
        # self.progress_bar.set_margin_bottom(10)
        # left_panel.append(self.progress_bar)

        # #Progress Bar for RD
        # progress_bar_label = Gtk.Label(label="Rogue Drone Battery (%)", halign=Gtk.Align.CENTER)
        # left_panel.append(progress_bar_label)
        # self.progress_bar2 = Gtk.ProgressBar()
        # self.progress_bar2.set_margin_top(10)
        # self.progress_bar2.set_margin_bottom(10)    
        # left_panel.append(self.progress_bar2)
        
        # Create a frame (rectangle) for the title and make it expand horizontally
        status_frame = Gtk.Frame()
        status_frame.add_css_class("title-frame")  # Add CSS class for further styling
        status_label = Gtk.Label(label="Status Panel", halign=Gtk.Align.CENTER)
        status_frame.set_child(status_label)  # Add the label inside the frame
        left_panel.append(status_frame)
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        status_box.set_margin_top(10)

        # Add the side panel to the main container
        main_box.append(left_panel)

        # ----------------------- Main Content Area (Center) ----------------
        content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_area.add_css_class("content-area")  # Add a CSS class for styling
        content_area.set_hexpand(True)  # Allow the content area to expand horizontally
        content_area.set_vexpand(True)  # Allow the content area to expand vertically

        # Button to open Google Maps in the system browser
        open_maps_button = Gtk.Button(label="Open Google Maps Satellite View")
        open_maps_button.connect("clicked", self.open_maps)
        content_area.append(open_maps_button)

        #---------------------GUI LatLong Grids-----------------
        #Load static image map
        image_path = "/home/dfec/Pictures/Screenshots/Test2.png"
        map_image = Image.open(image_path)
        draw = ImageDraw.Draw(map_image)

        image_width, image_height = map_image.size

        # Lat/Long for the four corners of the image
        # lat1, lon1 = 39.01897, -104.89435  # Top-Left
        # lat2, lon2 = 39.01897, -104.89431  # Top-Right
        # lat3, lon3 = 39.01739, -104.89435  # Bottom-Left
        # lat4, lon4 = 39.01739, -104.89431  # Bottom-Right
        
        #New test coordinates
        lat1, lon1 = 39.019045, -104.894301  # Top-Left
        lat2, lon2 = 39.019045, -104.892113  # Top-Right
        lat3, lon3 = 39.017430, -104.894301  # Bottom-Left
        lat4, lon4 = 39.017430, -104.892113  # Bottom-Right
 
        ## Correctly calculated lat_per_pixel and lon_per_pixel
        lat_range = lat1 - lat3  # Should be positive
        lon_range = lon2 - lon1  # Should be positive
        lat_per_pixel = lat_range / image_height
        lon_per_pixel = lon_range / image_width

        # Check for zero range and raise an error if detected
        if lat_range == 0 or lon_range == 0:
            raise ValueError("Latitude or Longitude range is zero. Please adjust coordinates.")


        # Function to convert lat/long to pixel coordinates
        def latlon_to_pixel(latitude, longitude):
             # Check if the coordinate is within bounds
            if not (lat3 <= latitude <= lat1) or not (lon1 <= longitude <= lon2):
                print(f"Warning: Latitude {latitude} or Longitude {longitude} is out of the image bounds.")
                return None
            # Calculate pixel position
            pixel_x = (longitude - lon1) / lon_per_pixel
            pixel_y = (lat1 - latitude) / lat_per_pixel
            print(f"Lat/Lon: ({latitude}, {longitude}) -> Pixel: ({int(pixel_x)}, {int(pixel_y)})")
            return int(pixel_x), int(pixel_y)

        # Check that coordinates fall within adjusted bounds
        #latitude, longitude = 39.01818, -104.89433  # CENTER COORD 
        #latitude, longitude = 39.01897, -104.89433 # TOP CENTER COORD
        #latitude, longitude = 39.01739, -104.89433 # BOTTOM CENTER COORD
        #latitude, longitude = 39.01818, -104.89435 # LEFT CENTER COORD
        #latitude, longitude = 39.01818, -104.89431 # RIGHT CENTER COORD

        #Radar Coord Data
        latitude, longitude = 39.01839, -104.89353


        if lat3 <= latitude <= lat1 and lon1 <= longitude <= lon2:
            x, y = latlon_to_pixel(latitude, longitude)
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="red", outline="black")
        else:
            print("Adjusted coordinates are still out of bounds.")

        # Save or display the result
        map_image.save("/home/dfec/Pictures/Screenshots/NewMapWGrid.png")
        map_image.show()

        #-------------------------------------------------------


        # Load the image
        #image = Gtk.Image.new_from_file("C:\\Users\\C25Jimmy.Nguyen\\OneDrive - afacademy.af.edu\\Desktop\\GUI CAPSTONE\\Screenshot 2024-10-04 224853.png")
        image = Gtk.Picture.new_for_filename("/home/dfec/Pictures/Screenshots/Gui.png")
        # Ensure the image expands and fills the available space
        image.set_hexpand(True)
        image.set_vexpand(True)
        image.set_content_fit(Gtk.ContentFit.FILL)  # Make the image fill the container
        # Add the image to the content area
        content_area.append(image)
        # Add the content area to the main container
        main_box.append(content_area)



        # ----------------------- Right Side Panel ----------------------------
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right_panel.set_size_request(300, -1)  # Set a fixed width for the side panel
        right_panel.add_css_class("side-panel")  # Add a CSS class for styling
        right_panel.set_vexpand(True)  # Allow the side panel to expand vertically

        # Create a frame (rectangle) for the title and make it expand horizontally
        title_frame = Gtk.Frame()
        # title_frame.set_hexpand(True)  # Make the frame expand horizontally
        title_frame.add_css_class("title-frame")  # Add CSS class for further styling
        # Create a label for the title and add it inside the frame
        right_panel_title = Gtk.Label(label="Controls", halign=Gtk.Align.CENTER)
        title_frame.set_child(right_panel_title)  # Add the label inside the frame
        right_panel.append(title_frame)

        # Create a button and add it to the right panel
        button_in_right_panel = Gtk.Button(label="Toggle Drone Path")
        button_in_right_panel.set_margin_top(10)
        right_panel.append(button_in_right_panel)

        button2_in_right_panel = Gtk.Button(label="Log Data")
        button2_in_right_panel.set_margin_top(10)
        right_panel.append(button2_in_right_panel)

        button3_in_right_panel = Gtk.Button(label="Input Lat/Long")
        button3_in_right_panel.set_margin_top(10)
        right_panel.append(button3_in_right_panel)

        button4_in_right_panel = Gtk.Button(label="Reload Map")
        button4_in_right_panel.set_margin_top(10)
        right_panel.append(button4_in_right_panel)
        button5_in_right_panel = Gtk.Button(label="Freeze")
        button5_in_right_panel.set_margin_top(10)
        right_panel.append(button5_in_right_panel)

        button6_in_right_panel = Gtk.Button(label="Camera Stream")
        button6_in_right_panel.set_margin_top(10)

        button7_in_right_panel = Gtk.Button(label="Follow-me Mode")
        button7_in_right_panel.set_margin_top(10)
        right_panel.append(button7_in_right_panel)

        main_box.append(right_panel)
        # Apply the custom CSS styles
        self.apply_css()

    def apply_css(self):
        # Load CSS provider
        css_provider = Gtk.CssProvider()

        # Define CSS styles for the side panel and content area
        css = b"""
        .side-panel {
            border: 2px solid black;
            padding: 10px;
        }
        .content-area {
            border: 2px solid blue;
            padding: 10px;
        }
        .title-frame {
            background-color: #a9a9a9;  /* Set background color */
            border: 2px solid black;    /* Add border to the frame */
            padding: 5px;
        }
        label {
            font-weight: bold;  /* Make the label text bold */
        }

        """  # Make sure the triple-quoted string is properly closed here

        # Load the CSS
        css_provider.load_from_data(css)

        # Get the default display from Gdk (not Gtk)
        display = Gdk.Display.get_default()

        # Apply the CSS provider to the display's default screen
        Gtk.StyleContext.add_provider_for_display(display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def open_maps(self, widget):
        # URL to open Google Maps in satellite view
        google_maps_url = "https://www.google.com/maps/place/Stillman+Field/@39.0090343,-104.8828153,255m/data=!3m1!1e3!4m6!3m5!1s0x8713537f7d0f542b:0x9f68218ee71a4b94!8m2!3d39.0088982!4d-104.8818144!16s%2Fg%2F11stld1zr5?entry=ttu&g_ep=EgoyMDI0MTAwMi4xIKXMDSoASAFQAw%3D%3D"
        webbrowser.open(google_maps_url)

class MyApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.myapp", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        # Create and present the window when the application is activated
        win = MyWindow(self)
        win.present()

def main():
    app = MyApp()
    app.run(None)

if __name__ == "__main__":
    main()
