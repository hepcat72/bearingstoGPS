import pathlib
from zipfile import BadZipFile
from typing import Optional

import pandas as pd
import yaml
from openpyxl.utils.exceptions import InvalidFileException


def read_from_file(
    filepath,
    sheet=0,
    filetype=None,
    dtype=None,
    keep_default_na=False,
    dropna=True,
    na_values=None,
    expected_headers=None,
):
    """Converts either an excel or tab delimited file into a dataframe.

    Args:
        filepath (str): Path to infile
        sheet (str): Name of excel sheet
        filetype (str): Enumeration ["csv", "tsv", "excel", "yaml"]
        dtype (Dict(str)): header: type
        keep_default_na (bool): The keep_default_na arg to pandas
        dropna (bool): Whether to drop na
        na_values (bool): The na_values arg to pandas
        expected_headers (List(str)): List of all expected header names

    Raises:
        ValueError

    Returns:
        Pandas dataframe of parsed and processed infile data.
        Or, if the filetype is yaml, returns a python object.
    """
    filetype = _get_file_type(filepath, filetype=filetype)
    retval = None

    if filetype == "excel":
        retval = _read_from_xlsx(
            filepath,
            sheet=sheet,
            keep_default_na=keep_default_na,
            dropna=dropna,
            na_values=na_values,
            dtype=dtype,
            expected_headers=expected_headers,
        )
    elif filetype == "tsv":
        retval = _read_from_tsv(
            filepath,
            dtype=dtype,
            keep_default_na=keep_default_na,
            dropna=dropna,
            na_values=na_values,
            expected_headers=expected_headers,
        )
    elif filetype == "csv":
        retval = _read_from_csv(
            filepath,
            dtype=dtype,
            keep_default_na=keep_default_na,
            dropna=dropna,
            na_values=na_values,
            expected_headers=expected_headers,
        )
    elif filetype == "yaml":
        retval = _read_from_yaml(filepath)

    return retval


def _check_dtype_arg(
    filepath,
    result,
    sheet=0,
    dtype=None,
):
    # Error-check the dtype argument supplied
    if dtype is not None and len(dtype.keys()) > 0 and result is not None:
        # This assumes the retval is a dataframe
        missing = []
        for dtk in dtype.keys():
            if dtk not in result.columns:
                missing.append(dtk)
        if len(missing) == len(dtype.keys()):
            # None of the keys are present in the dataframe
            # Raise programming errors immediately
            raise InvalidDtypeDict(
                dtype,
                file=filepath,
                sheet=sheet,
                columns=list(result.columns),
            )
        elif len(missing) > 0:
            idk = InvalidDtypeKeys(
                missing,
                file=filepath,
                sheet=sheet,
                columns=list(result.columns),
            )
            # Some columns may be optional, so if at least 1 is correct, just issue a warning.
            print(f"WARNING: {type(idk).__name__}: {idk}")


def read_headers_from_file(
    filepath,
    sheet=0,
    filetype=None,
):
    """Converts either an excel or tab delimited file into a dataframe.

    Args:
        filepath (str): Path to infile
        sheet (str): Name of excel sheet
        filetype (str): Enumeration ["csv", "tsv", "excel", "yaml"]
        expected_headers (List(str)): List of all expected header names

    Raises:
        ValueError

    Returns:
        headers (list of string)
    """
    filetype = _get_file_type(filepath, filetype=filetype)
    retval = None

    if filetype == "excel":
        retval = _read_headers_from_xlsx(filepath, sheet=sheet)
    elif filetype == "tsv":
        retval = _read_headers_from_tsv(filepath)
    elif filetype == "csv":
        retval = _read_headers_from_csv(filepath)
    elif filetype == "yaml":
        raise ValueError(
            'Invalid file type: "%s", yaml files do not have headers', filetype
        )

    return retval


def _get_file_type(filepath, filetype=None):
    filetypes = ["csv", "tsv", "excel", "yaml"]
    extensions = {
        "csv": "csv",
        "tsv": "tsv",
        "xlsx": "excel",
        "yaml": "yaml",
        "yml": "yaml",
    }

    if filetype is None:
        ext = pathlib.Path(filepath).suffix.strip(".")

        if ext in extensions.keys():
            filetype = extensions[ext]
        else:
            try:
                pd.ExcelFile(filepath, engine="openpyxl")
                filetype = "excel"
            except (InvalidFileException, ValueError, BadZipFile):  # type: ignore
                raise ValueError(
                    'Invalid file extension: "%s", expected one of %s',
                    ext,
                    extensions.keys(),
                )
    elif filetype not in filetypes:
        raise ValueError(
            'Invalid file type: "%s", expected one of %s',
            filetype,
            filetypes,
        )

    return filetype


def _read_from_yaml(filepath):
    with open(filepath) as headers_file:
        return yaml.safe_load(headers_file)


def _read_from_xlsx(
    filepath,
    sheet=0,
    dtype=None,
    keep_default_na=False,
    dropna=True,
    expected_headers=None,
    na_values=None,
):
    sheet_name = sheet
    sheets = get_sheet_names(filepath)

    if sheet is None:
        sheet_name = sheets

    # If more than 1 sheet is being read, make recursive calls to get dataframes using the intended dtype dict
    if isinstance(sheet_name, list):
        if expected_headers is not None:
            raise NotImplementedError(
                "expected_headers not supported with multiple sheets."
            )

        # dtype is assumed to be a 2D dict by sheet and column
        df_dict = {}
        for sheet_n in sheet_name:
            dtype_n = None
            if isinstance(dtype, dict):
                dtype_n = dtype.get(sheet_n, None)

            # Recursive calls
            df_dict[sheet_n] = read_from_file(
                filepath,
                sheet=sheet_n,
                dtype=dtype_n,
                keep_default_na=keep_default_na,
                dropna=dropna,
                # TODO: Add support for expected headers
                # expected_headers=None,
                na_values=na_values,
            )

        return df_dict

    if (
        sheet_name is not None
        and not isinstance(sheet_name, int)
        and sheet_name not in sheets
        and (expected_headers is not None or len(sheets) == 1)
    ):
        # If we know the expected headers or there's only 1 sheet, let's take a chance that the first sheet is correct,
        # despite a name mismatch.  If this isn't true, there will either be an IndexError or a downstream error.
        sheet_name = 0

    try:
        validate_headers(
            filepath,
            _read_headers_from_xlsx(filepath, sheet=sheet_name),
            expected_headers,
        )
    except IndexError as ie:
        if (
            sheet_name is not None
            and not isinstance(sheet_name, int)
            and sheet_name not in sheets
        ):
            raise ExcelSheetNotFound(sheet=sheet_name, file=filepath, all_sheets=sheets)
        raise ie

    kwargs = {
        "sheet_name": sheet_name,
        "engine": "openpyxl",
        "keep_default_na": keep_default_na,
    }
    if dtype is not None:
        kwargs["dtype"] = dtype
    if na_values is not None:
        kwargs["na_values"] = na_values

    df = pd.read_excel(filepath, **kwargs, comment="#")

    if dtype is not None:
        # astype() requires the keys be present in the columns (as opposed to dtype)
        astype = {}
        for k, v in dtype.items():
            if k in df.columns:
                astype[k] = v
        if len(astype.keys()) > 0:
            df = df.astype(astype)

    if keep_default_na or na_values is not None:
        dropna = False

    if dropna:
        df = df.dropna(axis=0, how="all")

    _check_dtype_arg(
        filepath,
        df,
        sheet=sheet,
        dtype=dtype,
    )

    return df


def _read_from_tsv(
    filepath,
    dtype=None,
    keep_default_na=False,
    dropna=True,
    expected_headers=None,
    na_values=None,
):
    kwargs = _collect_kwargs(
        keep_default_na=keep_default_na, na_values=na_values, dtype=dtype
    )

    df = pd.read_table(filepath, **kwargs, comment="#")

    validate_headers(
        filepath,
        _read_headers_from_tsv(filepath),
        expected_headers,
    )

    if keep_default_na or na_values is not None:
        dropna = False

    if dropna:
        df = df.dropna(axis=0, how="all")

    _check_dtype_arg(
        filepath,
        df,
        dtype=dtype,
    )

    return df


def _read_from_csv(
    filepath,
    dtype=None,
    keep_default_na=False,
    dropna=True,
    expected_headers=None,
    na_values=None,
):
    kwargs = _collect_kwargs(
        keep_default_na=keep_default_na, na_values=na_values, dtype=dtype
    )

    df = pd.read_csv(filepath, **kwargs, comment="#")

    validate_headers(
        filepath,
        _read_headers_from_csv(filepath),
        expected_headers,
    )

    if keep_default_na or na_values is not None:
        dropna = False

    if dropna:
        df = df.dropna(axis=0, how="all")

    _check_dtype_arg(
        filepath,
        df,
        dtype=dtype,
    )

    return df


def _collect_kwargs(dtype=None, keep_default_na=False, na_values=None):
    """
    Compiles a dict with keep_default_na and only the remaining keyword arguments that have values.

    Note, this function was created solely to avoid a JSCPD error.
    """
    kwargs = {"keep_default_na": keep_default_na}
    if na_values is not None:
        kwargs["na_values"] = na_values
    if dtype is not None:
        kwargs["dtype"] = dtype
    return kwargs


def validate_headers(filepath, headers, expected_headers=None):
    """Checks that all headers are the expected headers.

    Args:
        filepath (str): Path to infile
        headers (List(str)): List of present header names
        expected_headers (List(str)): List of all expected header names

    Raises:
        DuplicateHeaders
        InvalidHeaders

    Returns:
        Nothing
    """
    not_unique, nuniqs, nall = _headers_are_not_unique(headers)

    if not_unique:
        raise DuplicateFileHeaders(filepath, nall, nuniqs, headers)

    if expected_headers is not None and not headers_are_as_expected(
        expected_headers, headers
    ):
        raise InvalidHeaders(headers, expected_headers, filepath)


def _read_headers_from_xlsx(filepath, sheet=0):
    sheet_name = sheet
    sheets = get_sheet_names(filepath)
    if str(sheet_name) not in sheets:
        sheet_name = 0

    # Note, setting `mangle_dupe_cols=False` would overwrite duplicates instead of raise an exception, so we're
    # checking for duplicate headers manually here.
    raw_headers = (
        pd.read_excel(
            filepath,
            nrows=1,  # Read only the first row
            header=None,
            sheet_name=sheet_name,
            engine="openpyxl",
            comment="#",
        )
        .squeeze("columns")
        .iloc[0]
    )
    # Apparently, if there's only 1 header, .iloc[0] returns a string, otherwise a series
    if isinstance(raw_headers, str):
        return [raw_headers]
    return raw_headers.to_list()


def _read_headers_from_tsv(filepath):
    # Note, setting `mangle_dupe_cols=False` would overwrite duplicates instead of raise an exception, so we're
    # checking for duplicate headers manually here.
    raw_headers = (
        pd.read_table(
            filepath,
            nrows=1,
            header=None,
            comment="#",
        )
        .squeeze("columns")
        .iloc[0]
    )
    # Apparently, if there's only 1 header, .iloc[0] returns a string, otherwise a series
    if isinstance(raw_headers, str):
        return [raw_headers]
    return raw_headers.to_list()


def _read_headers_from_csv(filepath):
    # Note, setting `mangle_dupe_cols=False` would overwrite duplicates instead of raise an exception, so we're
    # checking for duplicate headers manually here.
    raw_headers = (
        pd.read_csv(
            filepath,
            nrows=1,
            header=None,
            comment="#",
        )
        .squeeze("columns")
        .iloc[0]
    )
    # Apparently, if there's only 1 header, .iloc[0] returns a string, otherwise a series
    if isinstance(raw_headers, str):
        return [raw_headers]
    return raw_headers.to_list()


def headers_are_as_expected(expected, headers):
    """Confirms all headers are present, irrespective of case and order.

    Args:
        expected (List(str)): List of all expected header names
        headers (List(str)): List of present header names

    Raises:
        Nothing

    Returns:
        bool: Whether headers are valid or not
    """
    return sorted([s.lower() for s in headers]) == sorted([s.lower() for s in expected])


def get_sheet_names(filepath):
    """Returns a list of sheet names in an excel file.

    Args:
        filepath (str): Path to infile

    Raises:
        InvalidFileException
        ValueError
        BadZipFile

    Returns:
        List(str): Sheet names
    """
    return pd.ExcelFile(filepath, engine="openpyxl").sheet_names


def is_excel(filepath):
    """Determines whether a file is an excel file or not.

    Args:
        filepath (str): Path to infile

    Raises:
        Nothing

    Returns:
        bool: Whether the file is an excel file or not
    """
    try:
        return filepath is not None and _get_file_type(filepath) == "excel"
    except (InvalidFileException, ValueError, BadZipFile):  # type: ignore
        return False


def merge_dataframes(left, right, on):
    """Merges 2 sheets using a common column.

    Args:
        left (str): Name of excel sheet
        right (str): Name of excel sheet
        on (str): Name of column in both the left and right sheets

    Raises:
        Nothing

    Returns:
        Pandas dataframe of merged sheet data
    """
    return pd.merge(left=left, right=right, on=on)


def _headers_are_not_unique(headers: list):
    num_uniq_heads = len(list(dict.fromkeys(headers)))
    num_heads = len(headers)
    if num_uniq_heads != num_heads:
        return True, num_uniq_heads, num_heads
    return False, num_uniq_heads, num_heads


def get_row_val(row, header, strip=True, all_headers=None):
    """Returns value from the row (presumably from df) and column (identified by header).

    Converts empty strings and "nan"s to None.  Strips leading/trailing spaces.

    Args:
        row (row of a dataframe): Row of data.
        header (str): Column header name.
        strip (boolean) [True]: Whether to strip leading and trailing spaces.

    Raises:
        ValueError

    Returns:
        val (object): Data from the row at the column (header)
    """
    none_vals = ["", "nan"]
    val = None

    if header in row:
        val = row[header]
        if isinstance(val, str) and strip is True:
            val = val.strip()
        if val in none_vals:
            val = None
    else:
        # Missing headers are addressed way before this. If we get here, it's a programming issue, so raise instead
        # of buffer
        ahs = f"  Must be one of: {all_headers}." if all_headers is not None else ""
        raise ValueError(
            f"Invalid data header [{header}].{ahs}"
        )

    return val



class DuplicateFileHeaders(Exception):
    def __init__(self, filepath, nall, nuniqs, headers):
        message = (
            f"Column headers are not unique in {filepath}. There are {nall} columns and {nuniqs} unique values: "
            f"{headers}"
        )
        super().__init__(message)
        self.filepath = filepath
        self.nall = nall
        self.nuniqs = nuniqs
        self.headers = headers


class InfileError(Exception):
    def __init__(
        self,
        message,
        rownum: Optional[int] = None,
        sheet=None,
        file=None,
        column=None,
        order=None,
    ):
        self.rownum = rownum
        self.sheet = sheet
        self.file = file
        self.column = column
        loc = generate_file_location_string(
            rownum=rownum, sheet=sheet, file=file, column=column
        )
        if "%s" not in message:
            message += "  Location: %s."
        if order is not None:
            if "loc" not in order and len(order) != 4:
                if message.count("%s") != len(order) + 1:
                    raise ValueError(
                        "You must either provide all location arguments in your order list: [rownum, column, file, "
                        "sheet] or provide an extra '%s' in your message for the leftover location information."
                    )
                order.append("loc")
            # Save the arguments in a dict
            vdict = {
                "file": file,
                "sheet": sheet,
                "column": column,
                "rownum": rownum,
            }
            # Set the argument value to None, so the ones included in order will not be included in loc
            if "file" in order:
                file = None
            if "sheet" in order:
                sheet = None
            if "column" in order:
                column = None
            if "rownum" in order:
                rownum = None
            loc = generate_file_location_string(
                rownum=rownum, sheet=sheet, file=file, column=column
            )
            insertions = [vdict[k] if k != "loc" else loc for k in order]
            if "loc" not in order and len(order) != 4:
                insertions.append(loc)
            message = message % tuple(insertions)
        else:
            message = message % loc
        super().__init__(message)
        self.loc = loc


def generate_file_location_string(column=None, rownum=None, sheet=None, file=None):
    loc_str = ""
    if column is not None:
        loc_str += f"column [{column}] "
    if loc_str != "" and rownum is not None:
        loc_str += "on "
    if rownum is not None:
        loc_str += f"row [{rownum}] "
    if loc_str != "" and sheet is not None:
        loc_str += "of "
    if sheet is not None:
        loc_str += f"sheet [{sheet}] "
    if loc_str != "":
        loc_str += "in "
    if file is not None:
        loc_str += f"file [{file}]"
    else:
        loc_str += "the load file data"
    return loc_str


class InvalidDtypeDict(InfileError):
    def __init__(
        self,
        dtype,
        columns=None,
        message=None,
        **kwargs,
    ):
        if message is None:
            message = (
                f"Invalid dtype dict supplied for parsing %s.  None of its keys {list(dtype.keys())} are present "
                f"in the dataframe, whose columns are {columns}."
            )
        super().__init__(message, **kwargs)
        self.dtype = dtype
        self.columns = columns


class InvalidDtypeKeys(InfileError):
    def __init__(
        self,
        missing,
        columns=None,
        message=None,
        **kwargs,
    ):
        if message is None:
            message = (
                f"Missing dtype dict keys supplied for parsing %s.  These keys {missing} are not present "
                f"in the resulting dataframe, whose available columns are {columns}."
            )
        super().__init__(message, **kwargs)
        self.missing = missing
        self.columns = columns


class InvalidHeaders(InfileError):
    def __init__(self, headers, expected_headers=None, fileformat=None, **kwargs):
        if expected_headers is None:
            expected_headers = expected_headers
        message = ""
        file = kwargs.get("file", None)
        if file is not None:
            if fileformat is not None:
                filedesc = f"{fileformat} file "
            else:
                filedesc = "File "
            kwargs["file"] = f"{filedesc} [{file}] "
            message += "%s "
        missing = [i for i in expected_headers if i not in headers]
        unexpected = [i for i in headers if i not in expected_headers]
        if len(missing) > 0:
            message += f"is missing headers {missing}"
        if len(missing) > 0 and len(unexpected) > 0:
            message += " and "
        if len(unexpected) > 0:
            message += f" has unexpected headers: {unexpected}"
        super().__init__(message, **kwargs)
        self.headers = headers
        self.expected_headers = expected_headers
        self.missing = missing
        self.unexpected = unexpected


class ExcelSheetNotFound(InfileError):
    def __init__(self, sheet, file, all_sheets=None):
        avail_msg = "" if all_sheets is None else f"  Available sheets: {all_sheets}."
        message = f"Excel sheet [{sheet}] not found in %s.{avail_msg}"
        super().__init__(message, file=file)
        self.sheet = sheet
