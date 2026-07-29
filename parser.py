"""
Parser   
[Functions]
- print_(*values:object, cond:bool=True) -> None
    > Conditional print function with boolean argument
- default_arg(arg, default='')
- path_ls(folder:str|Path, glob_str:str='') -> Iterator[Path]
    > Yield file path objects in a folder as an iterator
- pdf_extract(pdf:Path, layout_text:bool=False) -> dict[str, object]
    > Collect information extracted from PDF as a dictionary object
- collect_pdfs(pdf_ls:Iterator[Path]) -> dict[str, dict]
    > Convert a series of pdf path objects to entries in a dictionary
- process_WCC_Paycheck(folder:str) -> pd.DataFrame
    > Parse & sort data as WCC_Paycheck class object
- organize(df:pd.DataFrame, get_cols:list[str], sort_col:str, show:bool=False) -> pd.DataFrame
    > Sort data frame for some column, then select desired columns
- filter_dataframe(df:pd.DataFrame, column:str, search:str, mode:str, show:bool=False) -> pd.DataFrame
    > Filter data frame rows by column

[Classes]
- WCC_Paycheck(pdf_text:str)
    > advice_num, pay_begin_date, pay_end_date,
      pay_rate, hours, gross_earnings, ytd_hours,
      ytd_earnings, net_pay, ytd_net_pay        
    - spill() -> list[object]
    - header() -> list[str]
    - to_float(amount:str) -> float
- Interface_Block(source:str, data:pd.DataFrame)
    > source, start, end, hours, pay, rate, year
    - report(as_csv:bool=False) -> None
"""
import pandas as pd       # https://pandas.pydata.org/docs/
import pdfplumber as pdfp   # https://github.com/jsvine/pdfplumber
import pathlib
import re
from datetime import datetime 
from collections.abc import Iterator
from pathlib import Path

def print_(*values:object, cond:bool=True) -> None:
    """Conditional print function with boolean argument"""
    if cond: print(*values)

def default_arg(arg, default=''):
    out = default if arg is None else arg
    return out

def path_ls(folder:str|Path, glob_str:str='') -> Iterator[Path]:
    """Yield file path objects in a folder as an iterator

    [Args]
    folder: str = Folder name of directory to list.
    glob_str: str = Optional glob pattern (e.g. "*.pdf"). If empty, lists
            all entries non-recursively.

    [Returns]
    Iterator with matching path objects
    """
    f_path = Path(folder)
    iterative = f_path.iterdir() if glob_str == '' else f_path.glob(glob_str)
    
    return iterative

def pdf_extract(pdf:Path, layout_text:bool=False) -> dict[str, object]:
    """Collect information extracted from PDF as a dictionary object
    [Args]
    pdf: Path = path object to be parsed and extracted from
    layout_text: bool = argument passed to extract_text function

    [Returns]
    pdf_file: dict[str, object] = A file dictionary of nested page dictionaries
    > 'name'    - The pdf file name
    > '#'       - Nested page dictionary
        > 'num'     - Page number
        > 'text'    - Extracted text
        > 'tables'  - Extracted tables
    """
    file_name:str = pdf.name
    pdf_file:dict[str, object] = {'name' : file_name}
    print_(f"Attempting to open {pdf.name}", cond=False)

    with pdfp.open(pdf) as f:
            for i, page in enumerate(f.pages):
                page_dict = {'num'      : i + 1,
                            'text'     : page.extract_text(layout=layout_text),
                            'tables'   : page.extract_tables()}
                pdf_file[str(i+1)] = page_dict
    return pdf_file    

def collect_pdfs(pdf_ls:Iterator[Path]) -> dict[str, dict]:
    """
    Convert a series of pdf path objects to entries in a dictionary
    [Args]
    pdf_ls:Iterator[Path] = pdf_ls(folder:str|Path, glob_str:str)
    
    [Returns]
    pdfs_dict:dict[str, dict] = dictionary collection of individual pdf file dictionaries.
    > Dictionary key and values are of the form; "file_name.pdf" : pdf_dict
    """
    pdfs_dict = {}
    for pdf_file in pdf_ls:
        pdf_dict = pdf_extract(pdf_file)
        pdfs_dict[pdf_dict['name']] = pdf_dict
    return pdfs_dict

def organize(df:pd.DataFrame, get_cols:list[str], sort_col:str, show:bool=False) -> pd.DataFrame:
    """Filter sort data frame for some column, then select desired columns"""
    df = df.sort_values(sort_col)
    out = df[get_cols]
    print_(out, cond=show)
    return out

class WCC_Paycheck():
     def __init__(self, pdf_text:str) -> None:
          pdf_lines = pdf_text.splitlines()
          self.advice_num =         int(pdf_lines[1].split(sep=" ")[10])
          self.pay_begin_date =     str(pdf_lines[1].split(sep=" ")[7])
          self.pay_end_date =       str(pdf_lines[2].split(sep=" ")[6])
          self.pay_rate =           self.to_float(pdf_lines[9].split(sep=" ")[2][1:])
          self.hours =              self.to_float(pdf_lines[13].split(sep=" ")[4])
          self.gross_earnings =     self.to_float(pdf_lines[23].split(sep=" ")[1])
          self.ytd_hours =          self.to_float(pdf_lines[13].split(sep=" ")[6])
          self.ytd_earnings =       self.to_float(pdf_lines[24].split(sep=" ")[1])
          self.net_pay =            self.to_float(pdf_lines[23].split(sep=" ")[-1])
          self.ytd_net_pay =        self.to_float(pdf_lines[24].split(sep=" ")[-1])

     def spill(self) -> list[object]:
          return [value for value in self.__dict__.values()]
     
     def header(self) -> list[str]:
          return [header for header in self.__dict__.keys()]
     
     def to_float(self, amount:str) -> float:
        out = amount.replace(',','').replace('$','')
        return float(out)     

def process_WCC_Paycheck(folder:str) -> pd.DataFrame:
    """Parse & sort data as WCC_Paycheck class objects"""
    stub_names = [stub_name.name for stub_name in path_ls(folder, '*.pdf')]
    stub_collection = collect_pdfs(path_ls(folder, '*.pdf'))
    stub_texts = [stub_collection[stub_name]['1']['text'] for stub_name in stub_names]
    paychecks = [WCC_Paycheck(text) for text in stub_texts]
    df_dict:dict[str|float|int, list|None] = {}
    for i, header in enumerate(paychecks[0].header()):
        df_dict[header] = [check.spill()[i] for check in paychecks]
    return pd.DataFrame(df_dict).sort_values("advice_num")

def filter_dataframe(df:pd.DataFrame, column:str, search:str, mode:str, show:bool=False) -> pd.DataFrame:
    """ Filter data frame rows by column  
    [Args]  
    df: DataFrame = the dataframe object to extract and filter data from  
    column: str = the column for which to apply filter  
    search: str = value used in filter protocol to select entries  
    mode: str = protocol for filtering  
    > "year_value" = get year value with matching search value (m/d/yy) 
    show: bool = show final output dataframe in terminal 

    [Returns]  
    copy: DataFrame = new dataframe object that is a filtered copy of the original
    """
    copy = df.copy()
    scope = copy[column]

    if mode == "year_value":
        scope = pd.to_datetime(scope, format="%m/%d/%Y")
        copy = copy[scope.dt.year == int(search)]
    #Room to expand to other filter modes

    print_(copy, cond=show)
    return pd.DataFrame(copy)

class Interface_Block():
    def __init__(self, source:str, data:pd.DataFrame) -> None:
        self.source = default_arg(source, 'untitled')
        first_entry, last_entry = data.loc[data['pay_begin_date'].idxmin()], data.loc[data['pay_end_date'].idxmax()]
        self.start:str = str(first_entry['pay_begin_date'])
        self.end:str = str(last_entry['pay_end_date'])
        print_(f"start {self.start}\n end {self.end}", cond=False)
        self.hours = sum([float(hour) for hour in data['hours']])
        self.pay = sum([float(pay) for pay in data['net_pay']])
        self.rate = list(set(data['pay_rate']))
        self.year = datetime.strptime(self.end, "%m/%d/%Y").year
        print_(f"year {self.year}", cond=False)

    def report(self, as_csv:bool=False) -> None:
        if not as_csv:
            period = f"{self.start} - {self.end}"
            print_block = [f"\n\n{self.source}",
                        f"Period: {period}",
                        f"Hours Worked: {self.hours}",
                        f"Hourly Rate: ${self.rate[0]}",
                        f"Total Pay: ${self.pay}"]
        if as_csv:
            print_block = [f"SOURCE,{self.source},",
                           "YEAR,START,END",
                           f"{self.year},{self.start},{self.end}",
                           "RATE,HOURS,TOTAL PAY",
                           f"{self.rate[0]},{self.hours},{self.pay}"]
        print("\n")
        for line in print_block:
            print(line)

class NFCU_Transactions():
    """
    Instance Attributes
    > folder:       Path|str        ""
    > accounts:     list[str]       ["Checking", "Savings"]

    """
    def __init__(self, folder:Path|str, show:bool=True) -> None:
        if Path(folder).is_dir():
            self.folder = folder
        else: raise NotADirectoryError(folder)
        self.accounts:list[str] = ["Checking", "Savings"]

        self.extract_settings:dict = {
            "column_x" : [72.6, 116.4, 175.9, 238.9, 367.9, 438.9, 485.3, 522.6],
            "columns" : ["posting_date", "transaction_date", "type",
                         "description", "category", "amount", "ending_card"],
            "header_bottom" : 174.0
        }

        self.acc_data:dict[str, pd.DataFrame] = {}
        for acc in self.accounts:
            acc_path:Path = self.get_latest(paths=folder, glob_str=f"*{acc}.pdf", show=False)
            acc_df = self.extract(pdf_path=acc_path)
            self.acc_data[acc] = acc_df

        self.frame:pd.DataFrame = self.present(cols=self.extract_settings["columns"],
                                               account="all")
        
        self.print_block:list[str] = [
            "\nNFCU Transactions",
            f"Folder:\t{self.folder}",
            f"Accounts:\t{self.accounts}",
        ]
        for line in self.print_block:
            print_(line, cond=show)
        print_(self.frame, cond=show)

    def get_latest(self, paths:str|Path|Iterator[Path], glob_str:str="*.pdf",
                show:bool=False) -> Path:
        if isinstance(paths, (str, Path)):
            ls:list[Path|str] = [path for path in path_ls(paths, glob_str=glob_str)]
        else: ls:list[Path|str] = [path for path in paths]
        file_dates:list[datetime] = []
        for f in ls:
            trim = re.search(r"(\d{4}-\d{2}-\d{2})",str(f))
            date_str = trim.group(1) if trim else 'null'
            date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
            file_dates.append(date_obj)
        latest = max(file_dates)
        latest_index = file_dates.index(latest)
        out = Path(ls[latest_index])
        print_(out, cond=show)
        return out
    
    def extract(self, pdf_path: Path) -> pd.DataFrame:
        """Parse an NFCU transaction PDF into a DataFrame.

        [Args]
        pdf_path: Path = the NFCU transactions PDF to parse.

        [Returns]
        pd.DataFrame with columns = NFCU_columns, dates as datetime64 and amount as
        float, indexed 0..n.
        """
        frames: list[pd.DataFrame] = []

        with pdfp.open(pdf_path) as pdf:
            for page in pdf.pages:
                row_lines = sorted({round(r["top"], 1)
                                    for r in page.rects if r["height"] < 1})
                if not row_lines:
                    print_(f"no ruling lines on page {page.page_number}", cond=False)
                    continue

                settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": self.extract_settings["column_x"],
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": row_lines,
                }

                table = page.extract_table(settings)
                if not table:
                    continue
                frames.append(pd.DataFrame(table))

        # Stack every page's rows into one frame, then apply the real column names.
        df = pd.concat(frames, axis=0, ignore_index=True)
        df.columns = [col for col in self.extract_settings["columns"]]

        # extract_table() joins text that wraps within a single cell using "\n"
        # (long descriptions especially). Collapse those newlines to single spaces
        # and trim surrounding whitespace so each cell is one clean line.
        df = df.apply(lambda col: col.str.replace(r"\s*\n\s*", " ", regex=True)
                                    .str.strip())

        # Keep only genuine transaction rows: the posting_date column must look like
        # a date (m/d/yy). This drops any blank spacer rows and stray non-data text
        is_transaction = df["posting_date"].str.match(r"\d{1,2}/\d{1,2}/\d{2,4}",
                                                    na=False)
        df = df[is_transaction].copy()

        # Cast money to float: strip "$" and thousands separators; a leading "-"
        # (e.g. "-$21.84") survives and yields a negative number.
        df["amount"] = (df["amount"].str.replace(r"[$,]", "", regex=True)
                                    .astype(float))

        # Cast both date columns to real datetimes (two-digit year, e.g. "7/1/26").
        for date_col in ("posting_date", "transaction_date"):
            df[date_col] = pd.to_datetime(df[date_col], format="%m/%d/%y")

        # Re-index cleanly now that spacer/header rows have been removed.
        return df.reset_index(drop=True)

    def present(self, account:str|list[str]="all", cols:list[str]|None=None) -> pd.DataFrame:
        cols = self.extract_settings["columns"] if cols is None else cols
        df_stack:list[pd.DataFrame] = []
        account = self.accounts if account == "all" else account
        if type(account) == str:
            account = [account]
        for acc in account:
            if acc in self.accounts:
                df_stack.append(self.acc_data[acc])
        df = pd.concat(df_stack, axis=0, ignore_index=True)
        return organize(df=df, get_cols=cols, sort_col="transaction_date")

    def clip(self, account:str|list[str]="all") -> None:
        account = self.accounts if account == "all" else account
        catch = self.present(account=account)
        catch.to_clipboard()
    
class Paystubs():
    def __init__(self, format:str, folder:str) -> None:
        formats:list[str] = ["WCC","ACFL"] #Room for more

        if format not in formats:
            raise ValueError(f"invalid format. '{format}' is not in {formats}")
        if not Path(folder).is_dir():
            raise NotADirectoryError(f"{folder} is not a directory")

        if format == "WCC":
            pass
        if format == "ACFL":
            pass