"""Evaluation metrics, written with the standard library only so they can be tested anywhere.

Utterance level: SRCC (Spearman), LCC (Pearson) and MSE between predicted and human scores.
System level: first average the predictions and the human scores per system, then compare those means.
Pairwise accuracy: the share of pairs where the higher score went to the clip people preferred.
"""
import math


def rankdata(values):
    """Ranks starting at 1; equal values share the average of their ranks (like scipy.stats.rankdata)."""
    # positions sorted by value; equal values keep their original order
    value_and_position = []
    for position in range(len(values)):
        value_and_position.append((values[position], position))
    value_and_position.sort()
    order = [position for value, position in value_and_position]
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        # find the end of the group of equal values that starts at `start`
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        average_rank = (start + end) / 2 + 1
        for position in range(start, end + 1):
            ranks[order[position]] = average_rank
        start = end + 1
    return ranks


def mean(values):
    """The average of a list of numbers."""
    return sum(values) / len(values)


def pearson(x, y):
    """Pearson correlation (LCC). Returns NaN when one of the lists is constant."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("need two equal-length sequences with at least 2 values")
    mean_x = mean(x)
    mean_y = mean(y)
    # sum() is used on purpose: since Python 3.12 it adds floats more exactly than a += loop
    sum_xy = sum([(a - mean_x) * (b - mean_y) for a, b in zip(x, y)])
    sum_xx = sum([(a - mean_x) ** 2 for a in x])
    sum_yy = sum([(b - mean_y) ** 2 for b in y])
    if sum_xx == 0 or sum_yy == 0:
        return float("nan")
    return sum_xy / math.sqrt(sum_xx * sum_yy)


def spearman(x, y):
    """Spearman rank correlation (SRCC): Pearson correlation of the ranks."""
    return pearson(rankdata(x), rankdata(y))


def mse(x, y):
    """Mean squared error."""
    return sum([(a - b) ** 2 for a, b in zip(x, y)]) / len(x)


def system_means(values, systems):
    """{system: average of its values}."""
    values_by_system = {}
    for value, system in zip(values, systems):
        if system not in values_by_system:
            values_by_system[system] = []
        values_by_system[system].append(value)
    means = {}
    for system in values_by_system:
        means[system] = mean(values_by_system[system])
    return means


def regression_report(pred, true, systems=None):
    """MSE, LCC and SRCC at utterance level, and at system level when the systems are given."""
    report = {
        "n": len(pred),
        "utt_mse": mse(pred, true),
        "utt_lcc": pearson(pred, true),
        "utt_srcc": spearman(pred, true),
    }
    if systems is not None:
        pred_means = system_means(pred, systems)
        true_means = system_means(true, systems)
        names = sorted(pred_means)
        pred_list = [pred_means[name] for name in names]
        true_list = [true_means[name] for name in names]
        report["n_systems"] = len(names)
        report["sys_mse"] = mse(pred_list, true_list)
        report["sys_lcc"] = pearson(pred_list, true_list)
        report["sys_srcc"] = spearman(pred_list, true_list)
    return report


def pairwise_accuracy(score_a, score_b, labels):
    """labels are "A" or "B" (decided pairs only). Equal scores count as half right."""
    if not labels:
        return float("nan")
    right = 0.0
    for a, b, label in zip(score_a, score_b, labels):
        if a == b:
            right += 0.5
        else:
            a_scored_higher = a > b
            people_chose_a = label == "A"
            if a_scored_higher == people_chose_a:
                right += 1
    return right / len(labels)
