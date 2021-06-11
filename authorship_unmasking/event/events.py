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

from authorship_unmasking.event.interfaces import Event
from authorship_unmasking.input.interfaces import SamplePair
from authorship_unmasking.output.interfaces import Aggregator

from typing import Any, Dict, Iterable, List, Optional, Tuple


class ProgressEvent(Event):
    """
    Event for indicating progress of an operation with a fixed number of steps to be performed.
    """
    
    def __init__(self, group_id: str, serial: int, events_total: Optional[int] = None):
        """
        :param group_id: event group ID token
        :param serial: event serial number
        :param events_total: total number of events that will be sent in this event group
        """
        super().__init__(group_id, serial)
        
        if events_total is not None and events_total < 1:
            raise AttributeError("events_total must be greater than 0")

        self._events_total = events_total

    @property
    def text(self) -> str:
        """Get user-readable textural representation of this event."""
        if self._events_total is None:
            return "Progress: {}".format(self.serial)

        return "Progress: {}/{} ({:.2f}%)".format(self.serial + 1, self.events_total, self.percent_done)

    @property
    def generic_text(self) -> Optional[str]:
        """Generic progress description."""
        return None

    @property
    def unit(self) -> Optional[str]:
        """Progress item unit name."""
        return None

    @property
    def events_total(self) -> Optional[int]:
        """Get total number of events that will be sent in this event group."""
        return self._events_total

    @property
    def percent_done(self) -> Optional[float]:
        """Total progress in percent (None if total process is unknown)."""
        if self._events_total is None:
            return None

        return (float(self.serial) / self.events_total) * 100.0

    @property
    def finished(self) -> bool:
        """True if all operations have finished."""
        return self._events_total is not None and self.serial >= self._events_total


class PairChunkingProgressEvent(ProgressEvent):
    """
    Event for indicating pair chunking progress.
    """

    @property
    def text(self) -> str:
        """Get user-readable textural representation of this event."""
        if self.percent_done is not None:
            return "Chunking pair: ({:.2f}%)".format(self.percent_done)

        return "Chunking pair..."

    @property
    def generic_text(self) -> Optional[str]:
        """Generic progress description."""
        return "Chunking pair"

    @property
    def unit(self) -> Optional[str]:
        """Progress item unit name."""
        return "pair(s)"


class PairBuildingProgressEvent(ProgressEvent):
    """
    Event for status reports on pair generation.
    """

    def __init__(self, group_id: str, serial: int, pairs_total: Optional[int] = None, pair: SamplePair = None,
                 files_a: Optional[List[str]] = None, files_b: Optional[List[str]] = None):
        """
        :param group_id: event group ID token
        :param serial: event serial number
        :param pair: pair for which this event is emitted
        :param files_a: participating files for chunk set a
        :param files_b: participating files for chunk set b
        """
        super().__init__(group_id, serial, pairs_total)
        self._pair = pair
        self._files_a = [] if files_a is None else files_a
        self._files_b = [] if files_b is None else files_b

    @property
    def pair(self):
        """Pair for which this event is emitted"""
        return self._pair

    @property
    def files(self) -> Tuple[List[str], List[str]]:
        """Lists of input files participating in this pair's generation of chunk sets a and b"""
        return self._files_a, self._files_b

    @files.setter
    def files(self, files: Tuple[List[str], List[str]]):
        """
        Set files participating in this pair's generation.

        :param files: participating files for chunk sets a and b as tuple of lists
        """
        self._files_a = files[0]
        self._files_b = files[1]

    @property
    def text(self) -> str:
        """Get user-readable textural representation of this event."""
        if self.events_total is None:
            return "Generated pair {}.".format(self.serial)

        return "Generated pair {} of {}.".format(self.serial + 1, self.events_total)

    @property
    def generic_text(self) -> Optional[str]:
        """Generic progress description."""
        return "Generating pairs"

    @property
    def unit(self) -> Optional[str]:
        """Progress item unit name."""
        return "pair(s)"


class ConfigurationFinishedEvent(Event):
    """
    Event fired after a job configuration has finished execution.
    """
    def __init__(self, group_id: str, serial: int, aggregators: List[Aggregator]):
        """
        :param group_id: event group ID token
        :param serial: event serial number
        :param aggregators: list of curve aggregators
        """
        super().__init__(group_id, serial)
        self._aggregators = aggregators

    @property
    def aggregators(self) -> List[Aggregator]:
        """Get aggregators associated with this event"""
        return self._aggregators

    def add_aggregator(self, aggregator: Aggregator):
        """
        Associate aggregator with this event.

        :param aggregator: aggregator to add
        """
        self._aggregators.append(aggregator)


class JobFinishedEvent(ConfigurationFinishedEvent):
    """
    Event fired when a job has finished execution.
    """
    pass


class UnmaskingTrainCurveEvent(Event):
    """
    Event for updating training curves of pairs during unmasking.
    """
    
    def __init__(self, group_id: str, serial: int, n: int = 0, pair: SamplePair = None, feature_set: type = None):
        """
        :param group_id: event group ID token
        :param serial: event serial number
        :param n: predicted final number of total values (should be set to the total number of unmasking iterations)
        :param pair: pair for which this curve is being calculated
        :param feature_set: feature set class used for generating this curve
        """
        super().__init__(group_id, serial)
        self._n = n
        self._values = []
        self._pair = pair
        self._feature_set = feature_set

    @property
    def pair(self):
        """Pair for which this curve is being calculated."""
        return self._pair
    
    @property
    def values(self) -> List[float]:
        """Accuracy values of curve (may be shorter than ``n``)."""
        return self._values
    
    @values.setter
    def values(self, points: List[float]):
        """Set curve points and update ``n`` if necessary."""
        self._values = list(points)
        self._n = max(self._n, len(self._values))

    def value(self, point: float):
        """Add point to curve and update ``n`` if necessary."""
        self._values.append(point)
        self._n = max(self._n, len(self._values))
    
    @property
    def n(self) -> int:
        """
        Predicted number of data points (usually the number of unmasking iterations).
        This is not the actual number of curve points, which would be ``len(values)``.
        """
        return self._n
    
    @n.setter
    def n(self, n: int):
        """
        Update prediction of the number of final data points in the curve.
        This should be set to the number of unmasking iterations.
        """
        self._n = n
    
    @property
    def feature_set(self) -> type:
        """Feature set class used for generating this curve."""
        return self._feature_set
    
    @feature_set.setter
    def feature_set(self, fs: type):
        """Set feature set class used for generating this curve."""
        self._feature_set = fs


class ModelFitEvent(Event):
    """
    Event to be fired when a model has been fit to a dataset.
    """

    def __init__(self, group_id: str, serial: int, data: Iterable[Iterable[float]] = None,
                 labels: Iterable[str] = None, is_truth: bool = False):
        """
        :param group_id: event group ID token
        :param serial: event serial number
        :param data: data which the model has been fit on
        :param labels: data class labels as strings
        :param is_truth: True if labels are ground truth
        """
        super().__init__(group_id, serial)
        self._data = None
        self._labels = None
        self._data = data
        self._labels = labels
        self._is_truth = is_truth

    @property
    def is_truth(self) -> bool:
        """If labels are the ground truth."""
        return self._is_truth

    @is_truth.setter
    def is_truth(self, is_truth: bool):
        """Set if labels are the ground truth."""
        self._is_truth = is_truth

    @property
    def data(self) -> Iterable[Iterable[float]]:
        """Data the model has been fit on."""
        return self._data

    @data.setter
    def data(self, data: Iterable[Iterable[float]]):
        """Set model data."""
        self._data = data

    @property
    def labels(self) -> Iterable[str]:
        """Data class labels as strings."""
        return self._labels

    @labels.setter
    def labels(self, labels: Iterable[str]):
        """Set class labels as strings."""
        self._labels = labels


class ModelPredictEvent(ModelFitEvent):
    """
    Event to be fried when a model has been applied to a dataset to predict samples.
    """

    @property
    def data(self) -> Iterable[Iterable[float]]:
        """Predicted data."""
        return super().data

    @data.setter
    def data(self, data: Iterable[Iterable[float]]):
        """Set predicted data."""
        super().data = data

    @property
    def labels(self) -> Iterable[str]:
        """Predicted class labels as strings."""
        return super().labels

    @labels.setter
    def labels(self, labels: Iterable[str]):
        """Set predicted class labels as strings."""
        super().labels = labels


class ModelMetricsEvent(ModelPredictEvent):
    """
    :class:: ModelPredictEvent with additional performance metrics.
    """

    def __init__(self, group_id: str, serial: int, data: Iterable[Iterable[float]] = None,
                 labels: Iterable[str] = None, is_truth: bool = False, metrics: Dict[str, Any] = None):
        super().__init__(group_id, serial, data, labels, is_truth)
        self._metrics = metrics if metrics is not None else {}

    @property
    def metrics(self) -> Dict[str, Any]:
        """Performance metrics dictionary."""
        return self._metrics

    @metrics.setter
    def metrics(self, metrics: Dict[str, Any]):
        """Set performance metrics dictionary."""
        self._metrics = metrics


class UnmaskingModelEvaluatedEvent(ProgressEvent):
    """
    Event to be fired when an unmasking model has been evaluated.
    """

    def __init__(self, group_id: str, serial: int, source_path: str, score: float):
        super().__init__(group_id, serial)

        self._source_path = source_path
        self._score = score

    @property
    def text(self) -> str:
        return "\nModel evaluated: {}\nScore: {:.3f}".format(self._source_path, self._score)


class UnmaskingModelSelectedEvent(UnmaskingModelEvaluatedEvent):
    """
    Event to be fired when an unmasking model has been selected as best-performing.
    """
    def __init__(self, group_id: str, serial: int, source_path: str, score: float, model: "UnmaskingResult"):
        super().__init__(group_id, serial, source_path, score)
        self._model = model

    @property
    def model(self) -> "UnmaskingResult":
        """Performance metrics dictionary."""
        return self._model

    @model.setter
    def model(self, model: "UnmaskingResult"):
        """Set performance metrics dictionary."""
        self._model = model

    @property
    def text(self) -> str:
        return "\nBest performing model selected: {}\nScore: {:.3f}".format(self._source_path, self._score)
