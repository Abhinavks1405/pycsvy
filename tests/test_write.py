from unittest.mock import MagicMock, patch

import pytest


class MockCSVWriter:
    writerow = MagicMock()
    writerows = MagicMock()


def test_save_header(tmpdir, mocker):
    import yaml

    from csvy.writers import write_header

    dumper = mocker.spy(yaml, "safe_dump")
    header = {"Name": "Ada Lovelace", "Country of origin": "UK"}

    filename = tmpdir / "some_file.cvsy"
    write_header(filename, header)
    dumper.assert_called_with(header, sort_keys=False)

    with filename.open("r") as f:
        lines = [line.strip() for line in f.readlines()]

    assert len(lines) == 4
    assert lines[0] == "---"
    assert lines[-1] == "---"
    for i, (k, v) in enumerate(header.items()):
        assert k in lines[i + 1]
        assert v in lines[i + 1]

    write_header(filename, header, comment="#", sort_keys=True)
    dumper.assert_called_with(header, sort_keys=True)

    with filename.open("r") as f:
        lines = [line.strip() for line in f.readlines()]
    print(lines)
    assert len(lines) == 4
    assert all([line.startswith("#") for line in lines])
    assert lines[0] == "#---"
    assert lines[-1] == "#---"
    for i, (k, v) in enumerate(sorted(header.items())):
        assert k in lines[i + 1]
        assert v in lines[i + 1]


@patch("numpy.savetxt")
def test_write_numpy(mock_save, tmpdir):
    import numpy as np

    from csvy.writers import write_numpy

    filename = tmpdir / "some_file.csv"

    data = []
    assert not write_numpy(filename, data)

    data = np.array([])
    assert write_numpy(filename, data)
    mock_save.assert_called_once()


@patch("pandas.DataFrame.to_csv")
def test_write_pandas(mock_save, tmpdir):
    import pandas as pd

    from csvy.writers import write_pandas

    filename = tmpdir / "some_file.csv"

    data = []
    assert not write_pandas(filename, data)

    data = pd.DataFrame()
    assert write_pandas(filename, data)
    mock_save.assert_called_once()


@patch("csv.writer")
def test_write_csv(mock_save, tmpdir):
    from csvy.writers import write_csv

    class Writer:
        writerow = MagicMock()

    mock_save.return_value = Writer
    filename = tmpdir / "some_file.csv"

    data = [[1, 2], [3, 4]]
    assert write_csv(filename, data)

    mock_save.assert_called_once()
    assert Writer.writerow.call_count == len(data)


@patch("csv.writer")
@patch("csvy.writers.write_header")
@pytest.mark.parametrize(
    "csv_options,yaml_options",
    (
        (csv_options, yaml_options)
        for csv_options in (None, {"delimiter": ","})
        for yaml_options in (None, {"sort_keys": False})
    ),
)
def test_writer(mock_write_header, mock_csv_writer, csv_options, yaml_options, tmpdir):
    from csvy.writers import Writer

    mock_csv_writer.return_value = MockCSVWriter

    filename = tmpdir / "some_file.csv"
    header = {"name": "HAL"}
    comment = "# "

    writer = Writer(filename, header, comment, csv_options, yaml_options)
    csv_options = csv_options or {}
    yaml_options = yaml_options or {}
    mock_write_header.assert_called_once_with(
        writer._file, header, comment, **yaml_options
    )

    mock_csv_writer.assert_called_once_with(writer._file, **csv_options)


@patch("csv.writer")
@patch("csvy.writers.write_header")
def test_writer_writerow(mock_write_header, mock_csv_writer, tmpdir):
    from csvy.writers import Writer

    filename = tmpdir / "some_file.csv"
    writer = Writer(filename, {})

    data = (1, 2, 3)
    writer.writerow(data)
    writer._writer.writerow.assert_called_once_with(data)


@patch("csv.writer")
@patch("csvy.writers.write_header")
def test_writer_writerows(mock_write_header, mock_csv_writer, tmpdir):
    from csvy.writers import Writer

    filename = tmpdir / "some_file.csv"
    writer = Writer(filename, {})

    data = ((1, 2, 3),)
    writer.writerows(data)
    writer._writer.writerows.assert_called_once_with(data)


def test_writer_close(tmpdir):
    from csvy.writers import Writer

    filename = tmpdir / "some_file.csv"
    writer = Writer(filename, {})
    writer._file = MagicMock()
    writer.close()
    writer._file.close.assert_called_once()


def test_writer_context(tmpdir):
    from csvy.writers import Writer

    filename = tmpdir / "some_file.csv"
    writer = Writer(filename, {})
    writer._file = MagicMock()

    # Test the context manager
    with writer:
        pass

    # The file should be closed on leaving the with-block
    writer._file.close.assert_called_once()


@patch("csvy.writers.write_header")
@patch("csvy.writers.write_data")
def test_write(mock_write_data, mock_write_header):
    from csvy.writers import write

    filename = "here.csv"
    data = [[1, 2], [3, 4]]
    header = {"name": "HAL"}
    comment = "# "
    csv_options = {"delimiter": ","}
    yaml_options = {"sort_keys": False}

    write(
        filename,
        data,
        header,
        comment,
        csv_options=csv_options,
        yaml_options=yaml_options,
    )

    mock_write_header.assert_called_once_with(filename, header, comment, **yaml_options)
    mock_write_data.assert_called_once_with(filename, data, comment, **csv_options)


@patch("csvy.writers.write_csv")
def test_write_data(mock_write_csv):
    from csvy.writers import KNOWN_WRITERS, write_data

    filename = "here.csv"
    data = [[1, 2], [3, 4]]
    comment = "# "
    csv_options = {"delimiter": ","}

    KNOWN_WRITERS.clear()
    KNOWN_WRITERS.append(MagicMock(return_value=True))
    write_data(filename, data, comment, **csv_options)
    KNOWN_WRITERS[0].assert_called_once_with(filename, data, comment, **csv_options)
    mock_write_csv.assert_not_called()

    KNOWN_WRITERS.clear()
    KNOWN_WRITERS.append(MagicMock(return_value=False))
    write_data(filename, data, comment, **csv_options)
    KNOWN_WRITERS[0].assert_called_once_with(filename, data, comment, **csv_options)
    mock_write_csv.assert_called_once_with(filename, data, comment, **csv_options)
