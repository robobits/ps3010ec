import tkinter as tk

class SevenSegmentModule():
    """SevenSegmentModule creates a multidigit decimal display that will show updates as
       the value of the object is updated

       The number of digits and position of the decimal point are fixed when the
       object is created and a max_value is provided to ensure the display is kept
       in ranger.  If max_value is not provided range protection is disabled.

       The number of digites, decimal point position, or max_value cannot be modified
       after creation

       setter and getter properties are in place.  e.g. obj.value = 100

       Negative values are not supported.  Setting a negative value will be reset to 0

       If max_value is provided, set > max_value will be reset to max_value.
       If max_value is not provided the internal value will be maintained but the display
       will truncate to the least significant digits available on the display.

       The caller must provide two arrays containing the digit images in order from
       zero through nine.  The first array contains no decimal point and the second
       array of images contains a decimal point on the right side.

       The height and width of individual digits are provided by the caller and the
       tkinter frame containing the digits is expanded to include all the digits called for

       The geometry manager of choice is passed through to the created frame to allow the
       display module to be placed from the calling application.
    """

    # self._value
    # self.valueFrame
    # self.digits[0-3]['digit_value']
    # self.digits[0-3]['canvas']
    # self.digits[0-3]['canvas_images']
    # self.max_value
    # self.places
    # self.point_position

    def __init__(self,
                 parent_frame,
                 height,
                 width,
                 images_dp,
                 images_ndp,
                 max_value=None,
                 places=4,
                 point_position=1):
        self._value = 0  # Starting value 0
        self.valueFrame = tk.Frame(parent_frame)
        self.max_value = max_value
        self.places = places
        self.point_position = point_position
        self.digits = []

        for ci in range(0, self.places):
            self.digits.append(dict())
            self.digits[-1]['digit_value'] = 0
            self.digits[-1]['canvas'] = tk.Canvas(self.valueFrame,
                                                  width=width,
                                                  height=height,
                                                  highlightthickness=0)
            self.digits[-1]['canvas'].pack(side='left',
                                           expand=1,
                                           pady=0,
                                           padx=0,
                                           fill='both',
                                           ipadx=0,
                                           ipady=0)
            self.digits[-1]['canvas_images'] = []
            if ci == self.point_position:  # This is the decimal point column.  Need images with decimal point
                for image in images_dp:
                    self.digits[-1]['canvas_images'].append(
                        self.digits[-1]['canvas'].create_image(0,
                                                               0,
                                                               image=image,
                                                               anchor="nw",
                                                               state='hidden'))
            else:  # Use images without decimal point
                for image in images_ndp:
                    self.digits[-1]['canvas_images'].append(
                        self.digits[-1]['canvas'].create_image(0,
                                                               0,
                                                               image=image,
                                                               anchor="nw",
                                                               state='hidden'))

        self._update_display()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self.max_value is None:  # Max value not set.  No range checking
            self._value = new_value
        else:
            if new_value <= self.max_value:
                self._value = new_value
            elif new_value < 0:
                self._value = 0
            else:
                self._value = self.max_value
        self._update_display()

    def __iadd__(self, inc_by):
        new_value = self._value + inc_by
        if (new_value > self.max_value):
            self._value = self.max_value
        else:
            self._value = new_value

        self._update_display()
        return self

    def __isub__(self, dec_by):
        new_value = self._value - dec_by
        if (new_value < 0):
            self._value = 0
        else:
            self._value = new_value

        self._update_display()
        return self

    def _update_display(self):
        """"""

        # From self.value, update the individual digits
        string_template = f"{{value:{self.places:02}}}"
        raw_string = string_template.format(value=self._value)

        for i in range(0, self.places):  # Use range to slice the string
            self.digits[i]['digit_value'] = int(raw_string[i])

        for digit in self.digits:
            # Move all the images out of sight
            for image in digit['canvas_images']:
                digit['canvas'].itemconfig(image, state='hidden')

            # Show the new value
            digit['canvas'].itemconfig(
                digit['canvas_images'][digit['digit_value']], state='normal')

    # Pass the geometry manager calls through to the frame to allow placement
    def pack(self, *args, **kwargs):
        self.valueFrame.pack(*args, **kwargs)

    def place(self, *args, **kwargs):
        self.valueFrame.place(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self.valueFrame.grid(*args, **kwargs)
