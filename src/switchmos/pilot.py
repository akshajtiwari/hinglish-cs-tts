"""Small helpers for the Step 3 pilot: training targets and the model-selection score."""
import math

# the four validation numbers whose plain average picks the winner (owner decision 2026-10-22)
SELECTION_METRICS = ["speechjudge_val_accuracy", "bvcc_val_srcc", "somos_val_srcc", "mango_val_srcc"]


def clip_mean_targets(keys, scores):
    """{clip key: mean score} from two parallel lists: the clip of each rating and the rating."""
    totals = {}
    counts = {}
    for key, score in zip(keys, scores):
        if key not in totals:
            totals[key] = 0.0
            counts[key] = 0
        totals[key] += score
        counts[key] += 1
    means = {}
    for key in totals:
        means[key] = totals[key] / counts[key]
    return means


def page_normalised_targets(keys, pages, scores):
    """MUSHRA scores turned into z-scores inside each listening page, then averaged per clip.

    One rater scores several systems on one page, so subtracting the page mean removes how strict that rater was.
    A page with a single score, or with no spread, gives 0 for its scores.
    """
    scores_of_page = {}
    for page, score in zip(pages, scores):
        if page not in scores_of_page:
            scores_of_page[page] = []
        scores_of_page[page].append(score)
    mean_of_page = {}
    std_of_page = {}
    for page in scores_of_page:
        values = scores_of_page[page]
        mean = sum(values) / len(values)
        variance = sum([(value - mean) ** 2 for value in values]) / len(values)
        mean_of_page[page] = mean
        std_of_page[page] = math.sqrt(variance)
    z_scores = []
    for page, score in zip(pages, scores):
        if std_of_page[page] == 0:
            z_scores.append(0.0)
        else:
            z_scores.append((score - mean_of_page[page]) / std_of_page[page])
    return clip_mean_targets(keys, z_scores)


def selection_score(val_metrics):
    """The plain average of the four validation numbers in SELECTION_METRICS; None if one of them is missing."""
    values = []
    for name in SELECTION_METRICS:
        value = val_metrics.get(name)
        if value is None or math.isnan(value):
            return None
        values.append(value)
    return sum(values) / len(values)
