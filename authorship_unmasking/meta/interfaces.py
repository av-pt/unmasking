# Copyright (C) 2017-2019 Janek Bevendorff, Webis Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from authorship_unmasking.output.interfaces import Output

from abc import ABCMeta, abstractmethod
from sklearn.base import BaseEstimator
from typing import Any, Dict, Iterable, Optional

import msgpack
import numpy as np
import os


# noinspection PyPep8Naming
class MetaClassificationModel(Output, metaclass=ABCMeta):
    """
    Base class for meta classification models.
    """

    def __init__(self):
        self._version = 1
        self._clf = None
        self._clf_params = {}

    @abstractmethod
    def _get_estimator(self) -> BaseEstimator:
        """
        Create a new (unconfigured) estimator instance.
        :return: estimator instance
        """
        pass

    def get_configured_estimator(self) -> BaseEstimator:
        """
        Create a new configured estimator instance.

        :return: estimator instance
        """
        clf = self._get_estimator()
        clf.set_params(**self._clf_params)
        return clf

    @abstractmethod
    async def optimize(self, X: Iterable[Iterable[float]], y: Iterable[int]):
        """
        Optimize hyperparameters of the model.

        :param X: samples
        :param y: labels
        """
        pass

    @abstractmethod
    async def fit(self, X: Iterable[Iterable[float]], y: Iterable[int]):
        """
        Fit model to data in X with labels from y.

        :param X: training samples
        :param y: labels
        """
        pass

    @abstractmethod
    async def predict(self, X: Iterable[Iterable[float]]) -> np.ndarray:
        """
        Predict classes for samples in X.

        :param X: samples
        :return: numpy array of predicted labels
        """
        pass

    @abstractmethod
    async def decision_function(self, X: Iterable[Iterable[float]]) -> np.ndarray:
        """
        Classification decision function / probabilities for samples in X.

        :param X: samples
        :return: decision function values
        """
        pass

    async def load(self, file_name: str):
        """
        Load model from given file.

        :param file_name: input file name
        """

        with open(file_name, "rb") as f:
            in_data = msgpack.unpack(f, use_list=False)

        if b"version" not in in_data:
            raise IOError("Invalid model format")

        if in_data[b"version"] > self._version or in_data[b"version"] < 1:
            raise ValueError("Unsupported model version: " + in_data[b"version"])

        if in_data[b"version"] == 1:
            for i, clf_dict in enumerate(in_data[b"clf"]):
                clf = self.get_configured_estimator()

                for k in clf_dict:
                    key = k[1:].decode("utf-8")

                    if k[0] == ord("a") or k[0] == ord("m"):
                        clf.__dict__[key] = np.array(clf_dict[k])
                    elif k[0] == ord("s"):
                        clf.__dict__[key] = clf_dict[k].decode("utf-8")
                    elif k[0] == ord("i"):
                        clf.__dict__[key] = np.int64(clf_dict[k])
                    elif k[0] == ord("f"):
                        clf.__dict__[key] = np.float64(clf_dict[k])
                    else:
                        clf.__dict__[key] = clf_dict[k]
                self._clf = clf

    async def save(self, output_dir: str, file_name: Optional[str] = None):
        out_dict = {
            "version": self._version,
            "clf": []
        }

        clf_dict = {}
        for k in self._clf.__dict__:
            if isinstance(self._clf.__dict__[k], np.ndarray):
                if len(self._clf.__dict__[k].shape) > 1:
                    clf_dict["m" + k] = tuple(map(tuple, self._clf.__dict__[k]))
                else:
                    clf_dict["a" + k] = tuple(self._clf.__dict__[k])
            elif isinstance(self._clf.__dict__[k], np.integer):
                clf_dict["i" + k] = int(self._clf.__dict__[k])
            elif isinstance(self._clf.__dict__[k], np.inexact):
                clf_dict["f" + k] = float(self._clf.__dict__[k])
            elif isinstance(self._clf.__dict__[k], str):
                clf_dict["s" + k] = self._clf.__dict__[k]
            else:
                clf_dict["t" + k] = self._clf.__dict__[k]

            out_dict["clf"].append(clf_dict)

        if file_name is None:
            file_name = self._generate_output_basename() + ".model"

        with open(os.path.join(output_dir, file_name), "wb") as f:
            msgpack.pack(out_dict, f)

    def reset(self):
        self._clf = None
        self._clf_params = {}

    @property
    def params(self) -> Dict[str, Any]:
        """Get parameters for each estimator."""
        return self._clf_params

    @params.setter
    def params(self, params: Dict[str, Any]):
        """Set parameters for each estimator."""
        self._clf_params = params
