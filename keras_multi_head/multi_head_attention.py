import keras
import keras.backend as K
from keras_self_attention import ScaledDotProductAttention


class MultiHeadAttention(keras.layers.Layer):
    """Multi-head attention layer.

    See: https://arxiv.org/pdf/1706.03762.pdf
    """

    def __init__(self,
                 head_num,
                 activation='relu',
                 kernel_initializer='glorot_normal',
                 kernel_regularizer=None,
                 kernel_constraint=None,
                 history_only=False,
                 **kwargs):
        """Initialize the layer.

        :param head_num: Number of heads.
        :param activation: Activations for linear mappings.
        :param kernel_initializer: Initializer for linear mappings.
        :param kernel_regularizer: Regularizer for linear mappings.
        :param kernel_constraint: Constraints for linear mappings.
        :param history_only: Whether to only use history in attention layer.
        """
        self.supports_masking = True
        self.head_num = head_num
        self.activation = keras.activations.get(activation)
        self.kernel_initializer = keras.initializers.get(kernel_initializer)
        self.kernel_regularizer = keras.regularizers.get(kernel_regularizer)
        self.kernel_constraint = keras.constraints.get(kernel_constraint)
        self.history_only = history_only

        self.Wq, self.Wk, self.Wv, self.Wo = None, None, None, None
        super(MultiHeadAttention, self).__init__(**kwargs)

    def get_config(self):
        config = {
            'head_num': self.head_num,
            'activation': self.activation,
            'kernel_initializer': self.kernel_initializer,
            'kernel_regularizer': self.kernel_regularizer,
            'kernel_constraint': self.kernel_constraint,
            'history_only': self.history_only,
        }
        base_config = super(MultiHeadAttention, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

    def compute_output_shape(self, input_shape):
        if isinstance(input_shape, list):
            q, k, v = input_shape
            return q[:-1] + (v[-1],)
        return input_shape

    def compute_mask(self, inputs, input_mask=None):
        if isinstance(input_mask, list):
            return input_mask[0]
        return input_mask

    def build(self, input_shape):
        if isinstance(input_shape, list):
            q, k, v = input_shape
        else:
            q = k = v = input_shape
        feature_dim = v[-1]
        if feature_dim % self.head_num != 0:
            raise IndexError('Invalid head number %d with the given input dim %d' % (self.head_num, feature_dim))
        self.Wq = self.add_weight(
            shape=(q[-1], feature_dim),
            initializer=self.kernel_initializer,
            name='%s_Wq' % self.name,
        )
        self.Wk = self.add_weight(
            shape=(k[-1], feature_dim),
            initializer=self.kernel_initializer,
            name='%s_Wk' % self.name,
        )
        self.Wv = self.add_weight(
            shape=(v[-1], feature_dim),
            initializer=self.kernel_initializer,
            name='%s_Wv' % self.name,
        )
        self.Wo = self.add_weight(
            shape=(feature_dim, feature_dim),
            initializer=self.kernel_initializer,
            name='%s_Wo' % self.name,
        )
        super(MultiHeadAttention, self).build(input_shape)

    def call(self, inputs, mask=None):
        if isinstance(inputs, list):
            q, k, v = inputs
        else:
            q = k = v = inputs
        feature_dim = K.shape(v)[-1]
        head_dim = feature_dim // self.head_num
        q = K.dot(q, self.Wq)
        k = K.dot(k, self.Wk)
        v = K.dot(v, self.Wv)
        if self.activation is not None:
            q = self.activation(q)
            k = self.activation(k)
            v = self.activation(v)
        outputs = []
        for i in range(self.head_num):
            begin, end = i * head_dim, (i + 1) * head_dim
            outputs.append(ScaledDotProductAttention(
                history_only=self.history_only,
                name='%s-Att-%d' % (self.name, i + 1),
            )([
                q[:, :, begin:end],
                k[:, :, begin:end],
                v[:, :, begin:end],
            ]))
        y = K.dot(K.concatenate(outputs), self.Wo)
        if self.activation is not None:
            y = self.activation(y)
        return y
