import math

LABELS = ('positive', 'neutral', 'negative')


def validate_metrics(report):
    """Reject incomplete or non-finite evaluation artifacts before publishing them."""
    if not isinstance(report, dict) or report.get('labels') != list(LABELS):
        raise ValueError('Urutan label evaluasi tidak valid.')
    count = report.get('count')
    if type(count) is not int or count < 1:
        raise ValueError('Jumlah data evaluasi tidak valid.')
    matrix = report.get('confusion')
    if not isinstance(matrix, list) or len(matrix) != 3 or any(
        not isinstance(row, list) or len(row) != 3 or any(type(value) is not int or value < 0 for value in row)
        for row in matrix
    ) or sum(map(sum, matrix)) != count:
        raise ValueError('Confusion matrix tidak valid.')
    classes = report.get('per_class')
    if not isinstance(classes, list) or len(classes) != 3:
        raise ValueError('Metrik per kelas belum lengkap.')
    values = [report.get('accuracy'), report.get('macro_f1')]
    for index, row in enumerate(classes):
        if not isinstance(row, dict) or row.get('label') != LABELS[index] or type(row.get('support')) is not int or row['support'] != sum(matrix[index]):
            raise ValueError('Label atau support evaluasi tidak valid.')
        values.extend(row.get(key) for key in ('precision', 'recall', 'f1'))
    if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise ValueError('Skor evaluasi tidak valid.')


def calculate_metrics(actual, predictions):
    if not actual or len(actual) != len(predictions):
        raise ValueError('Evaluasi memerlukan jumlah label aktual dan prediksi yang sama, minimal satu.')
    confusion = [[0] * 3 for _ in LABELS]
    for truth, prediction in zip(actual, predictions):
        confusion[LABELS.index(truth)][LABELS.index(prediction)] += 1
    classes = []
    for i, label in enumerate(LABELS):
        support = sum(confusion[i])
        predicted = sum(row[i] for row in confusion)
        precision = confusion[i][i] / predicted if predicted else 0
        recall = confusion[i][i] / support if support else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        classes.append(dict(label=label, precision=precision, recall=recall, f1=f1, support=support))
    return dict(count=len(actual), accuracy=sum(confusion[i][i] for i in range(3)) / len(actual),
                macro_f1=sum(row['f1'] for row in classes) / 3, labels=LABELS,
                confusion=confusion, per_class=classes)
