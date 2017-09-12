from PIL import Image
from contextlib import contextmanager
from crowdcount.models import density_map
from crowdcount.models.annotations import groundtruth
import attr
import keras.preprocessing.image as kimg
import matplotlib.pyplot as plt
import numpy as np
import os


def show(path, prediction=None):
    Previewer(path, prediction).show()


def save(path, dest, prediction=None):
    Previewer(path, prediction).save(dest)


@attr.s
class Previewer:
    path = attr.ib()
    prediction = attr.ib(default=None)
    CMAP = 'seismic'

    def __attrs_post_init__(self):
        if self.prediction is not None:
            self.prediction = np.squeeze(self.prediction)
        try:
            self.annotations = groundtruth.get(self.path)
        except KeyError:
            self.annotations = None

    def show(self):
        print("Displaying {}".format(self.path))
        with self._create_plot() as plt:
            plt.show()

    def save(self, dest):
        print("Saving to {}".format(dest))
        with self._create_plot() as plt:
            png = "{}.png".format(dest[0:-4])
            plt.savefig(png)  # matlabplot only supports png, so convert.
            Image.open(png).convert("RGB").save(dest, 'JPEG', quality=100)
            os.remove(png)

    @contextmanager
    def _create_plot(self):
        fig = plt.figure(figsize=(8, 6), dpi=100)
        fig.suptitle('Crowd Count')

        self._reset_plot_position()
        self._render_img(fig)
        self._render_groundtruth(fig)
        self._render_prediction(fig)

        yield plt
        plt.close()

    def _render_img(self, fig):
        img = kimg.load_img(self.path)
        ax = fig.add_subplot(self._next_plot_position())
        ax.imshow(img)

        if self.annotations is not None and self.annotations.any():
            ax.plot(self.annotations[:, 0], self.annotations[:, 1], 'r+')
            ax.set_title("Annotations: {}".format(len(self.annotations)))

    def _render_groundtruth(self, fig):
        if self.annotations is None:
            return

        ax = fig.add_subplot(self._next_plot_position())
        dm = density_map.generate(self.path, self.annotations)
        ax.imshow(dm, cmap=self.CMAP)
        ax.set_title("Ground Truth: {0:.2f}".format(dm.sum()))

    def _render_prediction(self, fig):
        if self.prediction is None:
            return

        ax = fig.add_subplot(self._next_plot_position())
        ax.imshow(self.prediction, cmap=self.CMAP)
        ax.set_title("Prediction: {0:.2f}".format(self.prediction.sum()))

    def _reset_plot_position(self):
        self.current_plot = 1

    def _next_plot_position(self):
        subplot = "1{}{}".format(self._cols(), self.current_plot)
        self.current_plot += 1
        return subplot

    def _cols(self):
        return len([v for v in [self.path, self.annotations, self.prediction] if v is not None])