import gi
import webbrowser
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk  # Import Gdk for applying the CSS

class MyWindow(Gtk.Window):
    def __init__(self, app):
        super().__init__(title="C-UAS Interface 2025")
        self.set_default_size(1000, 600)
        self.set_application(app)  # Link the window to the application

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
        title_frame = Gtk.Frame()
        # title_frame.set_hexpand(True)  # Make the frame expand horizontally
        title_frame.add_css_class("title-frame")  # Add CSS class for further styling
        # Create a label for the title and add it inside the frame
        left_panel_title = Gtk.Label(label="Status Panel", halign=Gtk.Align.CENTER)
        title_frame.set_child(left_panel_title)  # Add the label inside the frame
        # Add the title frame to the top of the left panel
        left_panel.append(title_frame)



        progress_bar_label = Gtk.Label(label="Discovery Drone Battery (%)", halign=Gtk.Align.CENTER)
        left_panel.append(progress_bar_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_margin_top(10)
        self.progress_bar.set_margin_bottom(10)
        left_panel.append(self.progress_bar)

        progress_bar_label = Gtk.Label(label="Rogue Drone Battery (%)", halign=Gtk.Align.CENTER)
        left_panel.append(progress_bar_label)

        self.progress_bar2 = Gtk.ProgressBar()
        self.progress_bar2.set_margin_top(10)
        self.progress_bar2.set_margin_bottom(10)
        left_panel.append(self.progress_bar2)
        

        # Create a frame (rectangle) for the title and make it expand horizontally
        title_frame = Gtk.Frame()
        # title_frame.set_hexpand(True)  # Make the frame expand horizontally
        title_frame.add_css_class("title-frame")  # Add CSS class for further styling
        # Create a label for the title and add it inside the frame
        left_panel_title = Gtk.Label(label="Legend", halign=Gtk.Align.CENTER)
        title_frame.set_child(left_panel_title)  # Add the label inside the frame
        # Add the title frame to the top of the left panel
        left_panel.append(title_frame)




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

        # Load the image
        image = Gtk.Image.new_from_file("C:\\Users\\C25Jimmy.Nguyen\\OneDrive - afacademy.af.edu\\Desktop\\GUI CAPSTONE\\Screenshot 2024-10-04 224853.png")
       
        # Make sure the image expands and fills the available space
        image.set_hexpand(True)
        image.set_vexpand(True)

        # Add the image to the content area
        content_area.append(image)

        # Add content to the main content area
        content_label = Gtk.Label(label="Main Content Area", halign=Gtk.Align.CENTER)
        content_area.append(content_label)
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
        # Add the title frame to the top of the left panel
        right_panel.append(title_frame)

        # Create a button and add it to the right panel
        button_in_right_panel = Gtk.Button(label="Toggle Drone Path")
        button_in_right_panel.set_margin_top(10)
        right_panel.append(button_in_right_panel)

        # Create a button and add it to the right panel
        button2_in_right_panel = Gtk.Button(label="Log Data")
        button2_in_right_panel.set_margin_top(10)
        right_panel.append(button2_in_right_panel)

        # Create a button and add it to the right panel
        button3_in_right_panel = Gtk.Button(label="Input Lat/Long")
        button3_in_right_panel.set_margin_top(10)
        right_panel.append(button3_in_right_panel)

        # Create a button and add it to the right panel
        button4_in_right_panel = Gtk.Button(label="Reload Map")
        button4_in_right_panel.set_margin_top(10)
        right_panel.append(button4_in_right_panel)

        # Create a button and add it to the right panel
        button5_in_right_panel = Gtk.Button(label="Freeze")
        button5_in_right_panel.set_margin_top(10)
        right_panel.append(button5_in_right_panel)

        # Create a button and add it to the right panel
        button6_in_right_panel = Gtk.Button(label="Camera Stream")
        button6_in_right_panel.set_margin_top(10)
        right_panel.append(button6_in_right_panel)

        # Create a button and add it to the right panel
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
