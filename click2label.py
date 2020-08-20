import os
import numpy as np
import pandas as pd
from collections import Iterable
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import colors as mpcolors
import IPython


class ClickLabel(object):
    """Class that displays images and records left/righ mouse click labelling"""

    def __init__(self,
                 data_folder='data/',
                 result_path='labels/df.csv',
                 label_options=['Cat meme', 'Dog meme'],
                 color_options=['red', 'blue'],
                 rows=2,
                 columns=4,
                 fontsize=10
                 ):
        """Constructs attributes and reads in any existing result table

            Parameters
            ----------
            data_folder: str
                Path to folder containing images to be labelled
            result_path: str
                Filepath to CSV file in which to save results. If the file already exists
                it will be imported, but this will only succeed if the CSV contains  
                columns named 'filename', 'label' and 'timestamp'. Any additional columns 
                in the CSV will be lost when a save occurs. 
            label_options: list-like of str 
                Two str that are names each labels, for left and right click respectively
            color_options: list-like of str 
                Two str that are color names that can pass to matplotlib.colors.to_rgb()
            rows: int
                number of rows to display on each labelling grid
            columns: int
                number of columns to display on each labelling grid
            fontsize: int
                size of font for text displayed on labelling grid

        """
        # Check validity of arguments
        for (v, s) in [(data_folder, 'data_folder'), (result_path, 'result_path')]:
            assert isinstance(v, str), '\'' + s + '\' must be str'
        for (v, s) in [(label_options, 'label_options'), (color_options, 'color_options')]:
            assert isinstance(v, Iterable), '\'' + s + \
                '\' must be a list-like iterable'
            assert len(v) == 2, '\'' + s + '\' must be of length 2'
            assert (type(v[0]) == str) and (type(v[1]) ==
                                            str), '\'' + s + '\' elements must be str'
        for (v, s) in [(rows, 'rows'), (columns, 'columns'), (fontsize, 'fontsize')]:
            assert isinstance(v, int), '\'' + s + '\' must be int'

        self.rows, self.columns, self.fontsize = rows, columns, fontsize
        self.num = rows * columns  # number of images to display on one grid

        self.result_path = result_path
        self.result = self.result_table()  # read in or create result table

        self.image_paths = self.get_image_paths(
            data_folder)  # get filepaths for all images
        self.images = []  # images attribute is empty until we first call labelling_grid()

        self.label_options, self.color_options = label_options, color_options
        # map click events to labels, left mouse event = 1, right mouse event = 3
        self.click_map = dict([(a, b) for a, b in zip([1, 3], label_options)])
        # map each label to color, with the 'None' label given False
        self.color_map = {
            **dict([(label_options[x], color_options[x]) for x in [0, 1]]), 'None': False}

    def result_table(self):
        """Attempts to read from a previous result table if one exists, else creates a new result table"""
        if os.path.exists(self.result_path):  # if the file exists attempt to read it
            try:  # attempt to read
                # file must be a CSV with 'filename' column
                df = pd.read_csv(self.result_path, index_col='filename')
                # CSV must contain 'label' column
                df['done'] = df['label'] != 'None'
                # CSV must contain 'timestamp' column
                return df.sort_values(['done', 'timestamp']).drop('done', axis=1)
            except:  # if conditions aren't met raise error
                raise ValueError("""The file that 'result_path' points to must be a CSV containing
                                     columns named 'filename', 'label' and 'timestamp""")
        else:  # if file does not exist create empty result table
            return pd.DataFrame(columns=['filename', 'label', 'timestamp']).set_index('filename')

    def get_image_paths(self, path):
        """Gets list of filepaths for all images in the data_folder, with unlabelled images first in the list"""
        if path[-1] != '/':
            path += '/'  # make sure data_folder input has trailing slash
        labelled = list(self.result.index)  # previously labelled
        # never labelled
        unlabelled = [
            path + f for f in os.listdir(path) if path + f not in labelled]
        # order such that never labelled are first
        return np.concatenate([np.sort(unlabelled), labelled])

    def onclick(self, event):
        """Mouse click event handler, will update an image if the user left or right clicks"""
        if event.button in self.click_map.keys():  # if mouse click occurs
            # loop through each image on the grid
            for idx, img in enumerate(self.images):
                if event.inaxes == img.ax:  # if click occured on this image
                    # map button number to label
                    label = self.click_map[event.button]
                    if label == img.label:
                        label = 'None'  # if this matches the label for this image we unlabel
                    color = self.color_map[label]  #  map label to color
                    img.update(label=label, timestamp=str(
                        dt.now())[:-7])  #  update image

    def labelling_grid(self):
        """
        Generates a labelling grid, adds images and the event handler. 
        If a grid was previously generated using this instance, then before
        generating a new grid the labels from the previous grid are added 
        to the result table, and the result table is saved as a CSV
        """
        if len(self.images) > 0:  # true if a previous grid was generated
            for i in self.images:  # for each image in the previous grid
                # store latest label/timestamp to result
                self.result.loc[i.path] = [i.label, i.timestamp]
            # save result table as CSV to result_path
            self.result.to_csv(self.result_path)
            # update image_paths so previous grid images are at the end
            self.image_paths = np.concatenate(
                [self.image_paths[self.num:], self.image_paths[:self.num]])

        # create figure for grid, where height of grid varies dynamically with number of rows
        fig = plt.figure(figsize=(9, 2 + (1.5 * self.rows)),
                         num='LEFT CLICK: {} / RIGHT CLICK: {}'.format(*self.label_options))

        self.images = []  # reset list of image
        # loop through enough images to fill grid
        for idx, f in enumerate(self.image_paths[:self.num]):
            ax = fig.add_subplot(self.rows, self.columns,
                                 idx + 1)  # add subplot to grid
            self.images.append(self.SingleImage(
                path=f, ax=ax, props=self))  # add image

        cid = fig.canvas.mpl_connect(
            'button_press_event', self.onclick)  # connect event handler
        plt.tight_layout(pad=2)  #  ensure spacing between images in grid
        plt.show()  # show grid

    class SingleImage(object):
        """Class that stores information relating to a single image within ClickLabel"""

        def __init__(self, path, props, ax):
            """Constructs attributes and performs initial update

            Parameters
            ----------
            path: str
                Path to image file to be displayed    
            ax: matplotlib Axes
                Axes in which to display the image
            props: ClickLabel
                An instance of ClickLabel from which to inherit selected properties
            """
            self.path, self.ax = path, ax
            self.color_map, self.fontsize = props.color_map, props.fontsize  # get properties

            # if a result already exists for this image, update with existing parameters
            if path in props.result.index:
                self.update(*props.result.loc[path])
            else:
                self.update()  #  otherwise update with default parameters

        def update(self, label='None', timestamp='None'):
            """Update attributes and image display

            Parameters
            ----------
            label: str
                Label assigned to this image, where 'None' indicates no label
            timestamp: str
                String type timestamp of format YYYY-MM-DD hh:mm:ss, or 'None' to use current time

            """
            if timestamp == 'None':
                timestamp = str(dt.now())[:-7]
            self.label, self.timestamp = label, timestamp  # update attributes

            self.ax.clear()  # clear previous display

            try:  # attempt
                self.image = mpimg.imread(self.path)  # read image from file
                self.ax.imshow(self.image)  # show image
            except:  #  if we fail to read display failure message
                self.image = np.array([[[255, 255, 255]]])
                self.ax.imshow(self.image)
                self.ax.text(0, 0, 'Error reading file',
                             ha='center', fontsize=self.fontsize)

            self.ax.set_xticks([]), self.ax.set_yticks([])  # remove axis ticks
            self.ax.set_title(self.path.split(
                '/')[-1], fontsize=self.fontsize)  # title = filename

            overlay = self.color_map[label]  # overlay to image
            if label != 'None':  # if we have a label add overlay color
                width, height = self.image.shape[:2]
                self.ax.imshow(np.resize(mpcolors.to_rgb(
                    overlay), (width, height, 3)), alpha=0.4)

            caption_color = 'k' if label == 'None' else overlay  # caption is black if no label
            caption = 'Label: ' + str(label)  # to display below x-axis
            self.ax.set_xlabel(caption, fontsize=self.fontsize,
                               color=caption_color)  #  add caption
