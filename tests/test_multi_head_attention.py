import os
import tempfile
import random
import unittest
import keras
import numpy as np
from keras_multi_head import MultiHeadAttention


class TestMultiHead(unittest.TestCase):

    def test_sample(self):
        input_layer = keras.layers.Input(
            shape=(512,),
            name='Input',
        )
        embed_layer = keras.layers.Embedding(
            input_dim=12,
            output_dim=768,
            mask_zero=True,
            name='Embedding',
        )(input_layer)
        output_layer = MultiHeadAttention(
            head_num=12,
            name='Multi-Head',
        )(embed_layer)
        model = keras.models.Model(inputs=input_layer, outputs=output_layer)
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics={},
        )
        model.summary()
        self.assertEqual((None, 512, 768), model.layers[-1].output_shape)

    def test_invalid_head_num(self):
        with self.assertRaises(IndexError):
            input_layer = keras.layers.Input(
                shape=(2, 3),
                name='Input',
            )
            MultiHeadAttention(
                head_num=2,
                name='Multi-Head',
            )(input_layer)

    def test_fit_self(self):
        input_layer = keras.layers.Input(
            shape=(2, 3),
            name='Input',
        )
        att_layer = MultiHeadAttention(
            head_num=3,
            name='Multi-Head-1',
        )(input_layer)
        dense_layer = keras.layers.Dense(units=3, name='Dense-1')(att_layer)
        att_layer = MultiHeadAttention(
            head_num=3,
            name='Multi-Head-2',
        )(dense_layer)
        output_layer = keras.layers.Dense(units=3, name='Dense-2')(att_layer)
        model = keras.models.Model(inputs=input_layer, outputs=output_layer)
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics={},
        )
        model.summary()

        def _generator(batch_size=32):
            while True:
                inputs = np.random.random((batch_size, 2, 3))
                outputs = np.asarray([[[0.0, -0.1, 0.2]] * 2] * batch_size)
                yield inputs, outputs

        model.fit_generator(
            generator=_generator(),
            steps_per_epoch=1000,
            epochs=10,
            validation_data=_generator(),
            validation_steps=100,
            callbacks=[
                keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)
            ],
        )
        model_path = os.path.join(tempfile.gettempdir(), 'test_save_load_%f.h5' % random.random())
        model.save(model_path)
        model = keras.models.load_model(model_path, custom_objects={
            'MultiHeadAttention': MultiHeadAttention,
        })
        for inputs, _ in _generator(batch_size=3):
            predicts = model.predict(inputs)
            expect = np.asarray([[[0.0, -0.1, 0.2]] * 2] * 3)
            actual = np.round(predicts, decimals=1)
            self.assertTrue(np.allclose(expect, actual), (expect, actual))
            break

    def test_fit_multi(self):
        input_query = keras.layers.Input(
            shape=(2, 3),
            name='Input-Q',
        )
        input_key = keras.layers.Input(
            shape=(4, 5),
            name='Input-K',
        )
        input_value = keras.layers.Input(
            shape=(4, 6),
            name='Input-V',
        )
        att_layer = MultiHeadAttention(
            head_num=3,
            name='Multi-Head-1',
        )([input_query, input_key, input_value])
        dense_layer = keras.layers.Dense(units=3, name='Dense-1')(att_layer)
        att_layer = MultiHeadAttention(
            head_num=3,
            name='Multi-Head-2',
        )(dense_layer)
        output_layer = keras.layers.Dense(units=3, name='Dense-2')(att_layer)
        model = keras.models.Model(inputs=[input_query, input_key, input_value], outputs=output_layer)
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics={},
        )
        model.summary()

        def _generator(batch_size=32):
            while True:
                inputs = [
                    np.random.random((batch_size, 2, 3)),
                    np.random.random((batch_size, 4, 5)),
                    np.random.random((batch_size, 4, 6)),
                ]
                outputs = np.asarray([[[0.0, -0.1, 0.2]] * 2] * batch_size)
                yield inputs, outputs

        model.fit_generator(
            generator=_generator(),
            steps_per_epoch=1000,
            epochs=10,
            validation_data=_generator(),
            validation_steps=100,
            callbacks=[
                keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)
            ],
        )
        model_path = os.path.join(tempfile.gettempdir(), 'test_save_load_%f.h5' % random.random())
        model.save(model_path)
        model = keras.models.load_model(model_path, custom_objects={
            'MultiHeadAttention': MultiHeadAttention,
        })
        for inputs, _ in _generator(batch_size=3):
            predicts = model.predict(inputs)
            expect = np.asarray([[[0.0, -0.1, 0.2]] * 2] * 3)
            actual = np.round(predicts, decimals=1)
            self.assertTrue(np.allclose(expect, actual), (expect, actual))
            break
