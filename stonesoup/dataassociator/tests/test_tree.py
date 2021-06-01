import datetime
import pytest
import numpy as np

from ..neighbour import (
    NearestNeighbour, GlobalNearestNeighbour, GNNWith2DAssignment)
from ..tree import DetectionKDTreeMixIn, TPRTreeMixIn
from stonesoup.types.track import Track
from stonesoup.types.detection import Detection
from stonesoup.types.state import GaussianState


class DetectionKDTreeNN(NearestNeighbour, DetectionKDTreeMixIn):
    '''DetectionKDTreeNN from NearestNeighbour and DetectionKDTreeMixIn'''
    pass


class DetectionKDTreeGNN(GlobalNearestNeighbour, DetectionKDTreeMixIn):
    '''DetectionKDTreeGNN from GlobalNearestNeighbour and DetectionKDTreeMixIn'''
    pass


class DetectionKDTreeGNN2D(GNNWith2DAssignment, DetectionKDTreeMixIn):
    '''DetectionKDTreeGNN2D from GNNWith2DAssignment and DetectionKDTreeMixIn'''
    pass


class TPRTreeNN(NearestNeighbour, TPRTreeMixIn):
    '''TPRTreeNN from NearestNeighbour and TPRTreeMixIn'''
    pass


class TPRTreeGNN(GlobalNearestNeighbour, TPRTreeMixIn):
    '''TPRTreeGNN from GlobalNearestNeighbour and TPRTreeMixIn'''
    pass


class TPRTreeGNN2D(GNNWith2DAssignment, TPRTreeMixIn):
    '''TPRTreeGNN2D from GNNWith2DAssignment and TPRTreeMixIn'''
    pass


@pytest.fixture(params=[None, 10])
def number_of_neighbours(request):
    return request.param


@pytest.fixture(params=[[1, 3], [np.newaxis, np.newaxis]])
def vel_mapping(request):
    return request.param


@pytest.fixture(params=[
    DetectionKDTreeNN, DetectionKDTreeGNN, DetectionKDTreeGNN2D, TPRTreeNN, TPRTreeGNN, TPRTreeGNN2D])
def associator(
        request, distance_hypothesiser, probability_predictor,
        probability_updater, measurement_model, number_of_neighbours, vel_mapping):
    '''Distance associator for each KD Tree'''
    kd_trees = [DetectionKDTreeNN, DetectionKDTreeGNN, DetectionKDTreeGNN2D]
    if request.param in kd_trees:
        return request.param(distance_hypothesiser, probability_predictor,
                             probability_updater, number_of_neighbours=number_of_neighbours)
    else:
        return request.param(distance_hypothesiser, measurement_model,
                             datetime.timedelta(hours=1), vel_mapping=vel_mapping)


@pytest.fixture(params=[DetectionKDTreeGNN2D])
def probability_associator(
        request, probability_hypothesiser, probability_predictor,
        probability_updater, measurement_model):
    '''Probability associator for each KD Tree'''
    return request.param(probability_hypothesiser, probability_predictor, probability_updater)


def test_nearest_neighbour(associator):
    '''Test method for nearest neighbour and KD tree'''
    timestamp = datetime.datetime.now()
    t1 = Track([GaussianState(np.array([[0, 0, 0, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    t2 = Track([GaussianState(np.array([[3, 0, 3, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    d1 = Detection(np.array([[2, 2]]), timestamp)
    d2 = Detection(np.array([[5, 5]]), timestamp)

    tracks = {t1, t2}
    detections = {d1, d2}

    associations = associator.associate(tracks, detections, timestamp)

    # There should be 2 associations
    assert len(associations) == 2

    # Each track should associate with a unique detection
    associated_measurements = [hypothesis.measurement
                               for hypothesis in associations.values()
                               if hypothesis.measurement]
    assert len(associated_measurements) == len(set(associated_measurements))

    tracks = {}
    associations = associator.associate(tracks, detections, timestamp)
    assert len(associations) == 0
    print("Testing ...")
    print(len(associations))

    tracks = {t1, t2}
    detections = {}
    associations = associator.associate(tracks, detections, timestamp)
    print("Testing ...")
    print(len(associations))

    if isinstance(associator,DetectionKDTreeMixIn):
        print("numb neigbours = {}".format(associator.number_of_neighbours))

def test_missed_detection_nearest_neighbour(associator):
    '''Test method for nearest neighbour and KD tree'''
    timestamp = datetime.datetime.now()
    t1 = Track([GaussianState(np.array([[0, 0, 0, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    t2 = Track([GaussianState(np.array([[3, 0, 3, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    d1 = Detection(np.array([[20, 20]]), timestamp)

    tracks = {t1, t2}
    detections = {d1}

    associations = associator.associate(tracks, detections, timestamp)

    # Best hypothesis should be missed detection hypothesis
    assert all(not hypothesis.measurement
               for hypothesis in associations.values())


def test_probability_gnn(probability_associator):
    '''Test method for global nearest neighbour and KD tree'''
    timestamp = datetime.datetime.now()
    t1 = Track([GaussianState(np.array([[0, 0, 0, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    t2 = Track([GaussianState(np.array([[3, 0, 3, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    d1 = Detection(np.array([[2, 2]]), timestamp)
    d2 = Detection(np.array([[5, 5]]), timestamp)

    tracks = {t1, t2}
    detections = {d1, d2}

    associations = probability_associator.associate(
        tracks, detections, timestamp)

    # There should be 2 associations
    assert len(associations) == 2

    # Each track should associate with a unique detection
    associated_measurements = [hypothesis.measurement
                               for hypothesis in associations.values()
                               if hypothesis.measurement]
    assert len(associated_measurements) == len(set(associated_measurements))


def test_probability(pda_associator):

    timestamp = datetime.datetime.now()
    t1 = Track([GaussianState(np.array([[0, 0, 0, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    t2 = Track([GaussianState(np.array([[3, 0, 3, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    d1 = Detection(np.array([[0, 0]]), timestamp)
    d2 = Detection(np.array([[3, 3]]), timestamp)

    tracks = {t1, t2}
    detections = {d1, d2}

    associations = pda_associator.associate(tracks, detections, timestamp)

    # There should be 2 associations
    assert len(associations) == 2

    # verify association probabilities are correct
    prob_t1_d1_association = [hyp.probability for hyp in associations[t1]
                              if hyp.measurement is d1]
    prob_t1_d2_association = [hyp.probability for hyp in associations[t1]
                              if hyp.measurement is d2]
    prob_t2_d1_association = [hyp.probability for hyp in associations[t2]
                              if hyp.measurement is d1]
    prob_t2_d2_association = [hyp.probability for hyp in associations[t2]
                              if hyp.measurement is d2]

    assert prob_t1_d1_association[0] > prob_t1_d2_association[0]
    assert prob_t2_d1_association[0] < prob_t2_d2_association[0]


def test_missed_detection_probability(pda_associator):

    timestamp = datetime.datetime.now()
    t1 = Track([GaussianState(np.array([[0, 0, 0, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    t2 = Track([GaussianState(np.array([[3, 0, 3, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    d1 = Detection(np.array([[20, 20]]), timestamp)

    tracks = {t1, t2}
    detections = {d1}

    associations = pda_associator.associate(tracks, detections, timestamp)

    # Best hypothesis should be missed detection hypothesis
    max_track1_prob = max([hyp.probability for hyp in associations[t1]])
    max_track2_prob = max([hyp.probability for hyp in associations[t1]])

    track1_missed_detect_prob = max(
        [hyp.probability for hyp in associations[t1]
         if isinstance(hyp.measurement, MissedDetection)])
    track2_missed_detect_prob = max(
        [hyp.probability for hyp in associations[t1]
         if isinstance(hyp.measurement, MissedDetection)])

    assert max_track1_prob == track1_missed_detect_prob
    assert max_track2_prob == track2_missed_detect_prob


def test_no_detections_probability(pda_associator):

    timestamp = datetime.datetime.now()
    t1 = Track([GaussianState(np.array([[0, 0, 0, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])
    t2 = Track([GaussianState(np.array([[3, 0, 3, 0]]), np.diag([1, 0.1, 1, 0.1]), timestamp)])

    tracks = {t1, t2}
    detections = {}

    associations = pda_associator.associate(tracks, detections, timestamp)

    # All hypotheses should be missed detection hypothesis
    assert all(isinstance(hypothesis.measurement, MissedDetection)
               for multihyp in associations.values()
               for hypothesis in multihyp)


def test_no_tracks_probability(pda_associator):

    timestamp = datetime.datetime.now()
    d1 = Detection(np.array([[2, 2]]), timestamp)
    d2 = Detection(np.array([[5, 5]]), timestamp)

    tracks = {}
    detections = {d1, d2}

    associations = pda_associator.associate(tracks, detections, timestamp)

    # Since no Tracks went in, there should be no associations
    assert not associations
