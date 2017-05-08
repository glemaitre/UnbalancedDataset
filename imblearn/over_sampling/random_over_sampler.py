﻿"""Class to perform random over-sampling."""

# Authors: Guillaume Lemaitre <g.lemaitre58@gmail.com>
#          Christos Aridas
# License: MIT

from __future__ import division, print_function

from collections import Counter

import numpy as np
from sklearn.utils import check_random_state

from ..base import MultiClassSamplerMixin
from .base import BaseOverSampler


class RandomOverSampler(BaseOverSampler, MultiClassSamplerMixin):
    """Class to perform random over-sampling.

    Object to over-sample the minority class(es) by picking samples at random
    with replacement.

    Parameters
    ----------
    ratio : str or float, optional (default='auto')
        If 'auto', the ratio will be defined automatically to balance
        the dataset. Otherwise, the ratio is defined as the number
        of samples in the minority class over the the number of samples
        in the majority class.

    random_state : int, RandomState instance or None, optional (default=None)
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by np.random.

    Attributes
    ----------
    min_c_ : str or int
        The identifier of the minority class.

    max_c_ : str or int
        The identifier of the majority class.

    stats_c_ : dict of str/int : int
        A dictionary in which the number of occurences of each class is
        reported.

    X_shape_ : tuple of int
        Shape of the data `X` during fitting.

    Notes
    -----
    Supports multiple classes.

    Examples
    --------

    >>> from collections import Counter
    >>> from sklearn.datasets import make_classification
    >>> from imblearn.over_sampling import \
    RandomOverSampler # doctest: +NORMALIZE_WHITESPACE
    >>> X, y = make_classification(n_classes=2, class_sep=2,
    ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
    ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
    >>> print('Original dataset shape {}'.format(Counter(y)))
    Original dataset shape Counter({1: 900, 0: 100})
    >>> ros = RandomOverSampler(random_state=42)
    >>> X_res, y_res = ros.fit_sample(X, y)
    >>> print('Resampled dataset shape {}'.format(Counter(y_res)))
    Resampled dataset shape Counter({0: 900, 1: 900})

    """

    def __init__(self, ratio='auto', random_state=None):
        super(RandomOverSampler, self).__init__(
            ratio=ratio, random_state=random_state)

    def _sample(self, X, y):
        """Resample the dataset.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Matrix containing the data which have to be sampled.

        y : ndarray, shape (n_samples, )
            Corresponding label for each sample in X.

        Returns
        -------
        X_resampled : ndarray, shape (n_samples_new, n_features)
            The array containing the resampled data.

        y_resampled : ndarray, shape (n_samples_new)
            The corresponding label of `X_resampled`

        """
        random_state = check_random_state(self.random_state)
        target_stats = Counter(y)

        X_resampled = X.copy()
        y_resampled = y.copy()

        for class_sample, num_samples in self.ratio_.items():
            index_samples = random_state.randint(
                low=0, high=target_stats[class_sample], size=num_samples)

            X_resampled = np.concatenate((X_resampled,
                                          X[y == class_sample][index_samples]),
                                         axis=0)

            y_resampled = np.concatenate((y_resampled,
                                          y[y == class_sample][index_samples]),
                                         axis=0)

        self.logger.info('Over-sampling performed: %s', Counter(y_resampled))

        return X_resampled, y_resampled
