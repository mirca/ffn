import ffn.utils as utils
import pandas as pd
import pandas.io.data as pdata


@utils.memoize
def get(tickers, provider=None, common_dates=True, forward_fill=True,
        clean_tickers=True, column_names=None, ticker_field_sep=':',
        mrefresh=False, existing=None, **kwargs):

    if provider is None:
        provider = DEFAULT_PROVIDER

    tickers = utils.parse_arg(tickers)

    data = {}
    for ticker in tickers:
        t = ticker
        f = None

        # check for field
        bits = ticker.split(ticker_field_sep, 1)
        if len(bits) == 2:
            t = bits[0]
            f = bits[1]

        # call provider - check if supports memoization
        if hasattr(provider, 'mcache'):
            data[ticker] = provider(ticker=t, field=f, mrefresh=mrefresh, **kwargs)
        else:
            data[ticker] = provider(ticker=t, field=f, **kwargs)

    df = pd.DataFrame(data)
    # ensure same order as provided
    df = df[tickers]

    if existing:
        df = pd.merge(df, existing, how='outer',
                      left_index=True, right_index=True)

    if common_dates:
        df = df.dropna()

    if forward_fill:
        df = df.fillna(method='ffill')

    if column_names:
        cnames = utils.parse_arg(column_names)
        if len(cnames) != len(df.columns):
            raise ValueError(
                'column_names must be of same length as tickers')
        df.columns = cnames
    elif clean_tickers:
        df.columns = map(utils.clean_ticker, df.columns)

    return df


@utils.memoize
def web(ticker, field=None, start=None, end=None,
        mrefresh=False, source='yahoo'):
    if field is None:
        field = 'Adj Close'

    tmp = pdata.DataReader(ticker, data_source=source,
                           start=start, end=end)

    if tmp is None:
        raise ValueError('failed to retrieve data for %s:%s' % (ticker, field))

    return tmp[field]


@utils.memoize
def csv(ticker, path='data.csv', field='', mrefresh=False, **kwargs):
    # set defaults if not specified
    if 'index_col' not in kwargs:
        kwargs['index_col'] = 0
    if 'parse_dates' not in kwargs:
        kwargs['parse_dates'] = True

    # read in dataframe from csv file
    df = pd.read_csv(path, **kwargs)

    tf = ticker
    if field is not '':
        tf = '%s:%s' % (tf, field)

    # check that required column exists
    if tf not in df:
        raise ValueError('Ticker(field) not present in csv file!')

    return df[tf]


DEFAULT_PROVIDER = web