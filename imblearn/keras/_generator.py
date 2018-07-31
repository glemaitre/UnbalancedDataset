"""Implement generators for ``keras`` which will balance the data."""
from __future__ import division

import pytest

from scipy.sparse import issparse

from sklearn.base import clone
from sklearn.utils import safe_indexing
from sklearn.utils import check_random_state
from sklearn.utils.testing import set_random_state

keras = pytest.importorskip("keras")

from ..under_sampling import RandomUnderSampler
from ..utils import Substitution
from ..utils._docstring import _random_state_docstring
from ..tensorflow import balanced_batch_generator as tf_bbg


class BalancedBatchGenerator(keras.utils.Sequence):
    """Create balanced batches when training a keras model.

    Create a keras ``Sequence`` which is given to ``fit_generator``. The
    sampler defines the sampling strategy used to balance the dataset ahead of
    creating the batch. The sampler should have an attribute
    ``return_indices``.

    Parameters
    ----------
    X : ndarray, shape (n_samples, n_features)
        Original imbalanced dataset.

    y : ndarray, shape (n_samples,) or (n_samples, n_classes)
        Associated targets.

    sample_weight : ndarray, shape (n_samples,)
        Sample weight.

    sampler : object or None, optional (default=RandomUnderSampler)
        A sampler instance which has an attribute ``return_indices``.
        By default, the sampler used is a
        :class:`imblearn.under_sampling.RandomUnderSampler`.

    batch_size : int, optional (default=32)
        Number of samples per gradient update.

    sparse : bool, optional (default=False)
        Either or not to conserve or not the sparsity of the input (i.e. ``X``,
        ``y``, ``sample_weight``). By default, the returned batches will be
        dense.

    random_state : int, RandomState instance or None, optional (default=None)
        Control the randomization of the algorithm
        - If int, ``random_state`` is the seed used by the random number
          generator;
        - If ``RandomState`` instance, random_state is the random number
          generator;
        - If ``None``, the random number generator is the ``RandomState``
          instance used by ``np.random``.

    Attributes
    ----------
    sampler_ : object
        The sampler used to balance the dataset.

    indices_ : ndarray, shape (n_samples, n_features)
        The indices of the samples selected during sampling.

    Examples
    --------
    >>> from sklearn.datasets import load_iris
    >>> iris = load_iris()
    >>> from imblearn.datasets import make_imbalance
    >>> class_dict = dict()
    >>> class_dict[0] = 30; class_dict[1] = 50; class_dict[2] = 40
    >>> X, y = make_imbalance(iris.data, iris.target, class_dict)
    >>> import keras
    >>> y = keras.utils.to_categorical(y, 3)
    >>> model = keras.models.Sequential()
    >>> model.add(keras.layers.Dense(y.shape[1], input_dim=X.shape[1],
    ...                              activation='softmax'))
    >>> model.compile(optimizer='sgd', loss='categorical_crossentropy',
    ...               metrics=['accuracy'])
    >>> from imblearn.keras import BalancedBatchGenerator
    >>> from imblearn.under_sampling import NearMiss
    >>> training_generator = BalancedBatchGenerator(
    ...     X, y, sampler=NearMiss(), batch_size=10, random_state=42)
    >>> callback_history = model.fit_generator(generator=training_generator,
    ...                                        epochs=10, verbose=0)

    """
    def __init__(self, X, y, sample_weight=None, sampler=None, batch_size=32,
                 sparse=False, random_state=None):
        self.X = X
        self.y = y
        self.sample_weight = sample_weight
        self.sampler = sampler
        self.batch_size = batch_size
        self.sparse = sparse
        self.random_state = random_state
        self._sample()

    def _sample(self):
        random_state = check_random_state(self.random_state)
        if self.sampler is None:
            self.sampler_ = RandomUnderSampler(return_indices=True,
                                               random_state=random_state)
        else:
            if not hasattr(self.sampler, 'return_indices'):
                raise ValueError("'sampler' needs to return the indices of "
                                 "the samples selected. Provide a sampler "
                                 "which has an attribute 'return_indices'.")
            self.sampler_ = clone(self.sampler)
            self.sampler_.set_params(return_indices=True)
            set_random_state(self.sampler_, random_state)

        _, _, self.indices_ = self.sampler_.fit_sample(self.X, self.y)
        # shuffle the indices since the sampler are packing them by class
        random_state.shuffle(self.indices_)

    def __len__(self):
        return int(self.indices_.size // self.batch_size)

    def __getitem__(self, index):
        X_resampled = safe_indexing(
            self.X, self.indices_[index * self.batch_size:
                                  (index + 1) * self.batch_size])
        if issparse(X_resampled) and not self.sparse:
            X_resampled = X_resampled.toarray()

        y_resampled = safe_indexing(
            self.y, self.indices_[index * self.batch_size:
                                  (index + 1) * self.batch_size])
        if issparse(y_resampled) and not self.sparse:
            y_resampled = y_resampled.toarray()

        if self.sample_weight is not None:
            sample_weight_resampled = safe_indexing(
                self.sample_weight,
                self.indices_[index * self.batch_size:
                              (index + 1) * self.batch_size])
            if issparse(sample_weight_resampled) and not self.sparse:
                sample_weight = sample_weight.toarray()

        if self.sample_weight is None:
            return X_resampled, y_resampled
        else:
            return X_resampled, y_resampled, sample_weight_resampled


@Substitution(random_state=_random_state_docstring)
def balanced_batch_generator(X, y, sample_weight=None, sampler=None,
                             batch_size=32, sparse=False, random_state=None):
    """Create a balanced batch generator to train keras model.

    Returns a generator --- as well as the number of step per epoch --- which
    is given to ``fit_generator``. The sampler defines the sampling strategy
    used to balance the dataset ahead of creating the batch. The sampler should
    have an attribute ``return_indices``.

    Parameters
    ----------
    X : ndarray, shape (n_samples, n_features)
        Original imbalanced dataset.

    y : ndarray, shape (n_samples,) or (n_samples, n_classes)
        Associated targets.

    sample_weight : ndarray, shape (n_samples,)
        Sample weight.

    sampler : object or None, optional (default=RandomUnderSampler)
        A sampler instance which has an attribute ``return_indices``.
        By default, the sampler used is a
        :class:`imblearn.under_sampling.RandomUnderSampler`.

    batch_size : int, optional (default=32)
        Number of samples per gradient update.

    sparse : bool, optional (default=False)
        Either or not to conserve or not the sparsity of the input (i.e. ``X``,
        ``y``, ``sample_weight``). By default, the returned batches will be
        dense.

    {random_state}

    Returns
    -------
    generator : generator of tuple
        Generate batch of data. The tuple generated are either (X_batch,
        y_batch) or (X_batch, y_batch, sampler_weight_batch).

    steps_per_epoch : int
        The number of samples per epoch. Required by ``fit_generator`` in
        keras.

    Examples
    --------
    >>> from sklearn.datasets import load_iris
    >>> X, y = load_iris(return_X_y=True)
    >>> from imblearn.datasets import make_imbalance
    >>> class_dict = dict()
    >>> class_dict[0] = 30; class_dict[1] = 50; class_dict[2] = 40
    >>> from imblearn.datasets import make_imbalance
    >>> X, y = make_imbalance(X, y, class_dict)
    >>> import keras
    >>> y = keras.utils.to_categorical(y, 3)
    >>> model = keras.models.Sequential()
    >>> model.add(keras.layers.Dense(y.shape[1], input_dim=X.shape[1],
    ...                              activation='softmax'))
    >>> model.compile(optimizer='sgd', loss='categorical_crossentropy',
    ...               metrics=['accuracy'])
    >>> from imblearn.keras import balanced_batch_generator
    >>> from imblearn.under_sampling import NearMiss
    >>> training_generator, steps_per_epoch = balanced_batch_generator(
    ...     X, y, sampler=NearMiss(), batch_size=10, random_state=42)
    >>> callback_history = model.fit_generator(generator=training_generator,
    ...                                        steps_per_epoch=steps_per_epoch,
    ...                                        epochs=10, verbose=0)

    """

    return tf_bbg(X=X, y=y, sample_weight=sample_weight,
                  sampler=sampler, batch_size=batch_size,
                  sparse=sparse, random_state=random_state)
