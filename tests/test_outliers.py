import pandas as pd
from outliers import is_id_column, detect_outliers


def test_is_id_column_by_name():
    s = pd.Series([1, 2, 3], name="user_id")
    assert is_id_column(s) is True


def test_is_id_column_by_uniqueness():
    s = pd.Series(range(100), name="record")
    assert is_id_column(s) is True


def test_non_id_numeric_column():
    s = pd.Series([10, 11, 10, 12, 11], name="age")
    assert is_id_column(s) is False


def test_detect_outliers():
    s = pd.Series([10, 11, 12, 13, 100])
    outliers = detect_outliers(s)
    assert 100 in outliers
    assert len(outliers) == 1


def test_detect_outliers_empty():
    s = pd.Series([])
    assert detect_outliers(s) == []
