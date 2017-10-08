from crowdcount.ml.callbacks import DensityCheckpoint
from crowdcount.ml.generators import density as generator
from crowdcount.models import paths as ccp
from keras.callbacks import CSVLogger, ModelCheckpoint, TensorBoard
from keras.layers import Conv2D, MaxPooling2D, Input, average
from keras.models import load_model, Model as KModel
import attr
import crowdcount.ml as ml
import keras.optimizers
import os


def train(model_path=None):
    model = _create_model(model_path)
    initial_epoch = ml.fetch_epoch(model_path)
    print(model.summary())

    model.fit_generator(generator.training(),
            generator.steps_per_epoch(),
            initial_epoch=initial_epoch,
            epochs=150 - initial_epoch,
            verbose=1,
            validation_data=generator.validation(),
            validation_steps=generator.validation_steps(),
            callbacks=_create_callbacks())

    test(model)


def test(model=None, model_path=None):
    if not model:
        model = _create_model(model_path)
    score = model.evaluate_generator(generator.validation(), steps=generator.validation_steps())
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])


@attr.s
class Model:
    weights = attr.ib(default="data/weights/floyd26.epoch42.hdf5")

    def __attrs_post_init__(self):
        self.model = _create_model(self.weights)

    def predict(self, image_array):
        return self.model.predict(ml.image_to_batch(image_array), batch_size=1)

    def summary(self):
        return self.model.summary()


def predict(image_array, model_path):
    return Model(model_path).predict(image_array)


def _create_model(model_path=None):
    """
    Based on the model proposed by Fully Convolutional Crowd Counting On Highly Congested Scenes
    and the multi-scale cnn for crowd counting, utilizing multiple columns.
    https://arxiv.org/pdf/1612.00220.pdf
    https://arxiv.org/pdf/1702.02359.pdf
    """
    if model_path:
        print("Loading model for epoch {} from {}".format(ml.fetch_epoch(model_path), model_path))
        return load_model(model_path)

    inputs = Input(shape=(None, None, 3))
    cols = [_create_column(d, inputs) for d in [3, 5, 9]]
    model = KModel(inputs=inputs, outputs=average(cols))
    return _compile_model(model)


def _create_column(kernel_dimension, inputs):
    kd = kernel_dimension
    x = Conv2D(36, kernel_size=(kd, kd), activation='relu', padding='same')(inputs)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)
    x = Conv2D(72, (kd, kd), activation='relu', padding='same')(x)
    x = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(x)
    x = Conv2D(36, (kd, kd), activation='relu', padding='same')(x)
    if kd == 9:
        kd = 7
    x = Conv2D(24, (kd, kd), activation='relu', padding='same')(x)
    x = Conv2D(16, (kd, kd), activation='relu', padding='same')(x)
    return Conv2D(1, (1, 1), activation='relu', kernel_initializer='random_normal')(x)


def _compile_model(model):
    model.compile(loss='mean_squared_error',
                  optimizer=keras.optimizers.adam(lr=1e-6, decay=5e-6),
                  metrics=['mae', 'mse', 'accuracy'])
    return model


def _create_callbacks():
    os.makedirs(ccp.output('weights'), exist_ok=True)
    return [CSVLogger(ccp.output('keras_history.csv'), append=True),
            ModelCheckpoint(ccp.output("weights/weights.{epoch:02d}-{val_loss:.2f}.hdf5")),
            TensorBoard(log_dir=ccp.output('tensorboard')),
            DensityCheckpoint("data/shakecam/shakeshack-1504543773.jpg")]
