import pandas


def column_group_size(df, col):
    return df.groupby(col).size()


# returns a panda.Series object containing percentages of each column group
def column_group_percentage(df, col):
    return df.groupby(col).size().apply(lambda x: len(df))


# returns a float value, uniqueness of the column
def column_uniqueness(df, col):
    return df[col].nunique() / len(df)


# returns a panda.Series object containing adjusted uniqueness for selected columns
def adjusted_column_uniqueness(df, selected_cols):
    t = df[selected_cols].nunique() / len(df)
    return t.apply(lambda x: x / t.sum())


# returns a string of the largest group in the column
def column_largest_group(df, col):
    return df.groupby(col).size().idxmax()


# returns a string of the smallest group in the column
def column_smallest_group(df, col):
    return df.groupby(col).size().idxmin()


# returns row index of blank cells of a column
def get_blank_index(df, column):
    blank_candidates = pandas.isnull(df[column])
    df_blank = df[blank_candidates]
    return [str(index + 2) for index in df_blank.index]


# returns duplicates data in a column
def get_dupe_index(df, column):
    duplicate_candidates = df[column].duplicated(keep=False)
    df_dupe = df[duplicate_candidates].dropna(subset=[column])
    duplicate_values = df_dupe[column].values.tolist()

    if not duplicate_values:
        return []

    prev = duplicate_values[0]
    curr = []
    dupes = []
    i = 0

    for val in duplicate_values:
        if val == prev:
            curr.append(df_dupe.index[i] + 2)
        else:
            dupes.append(str(curr)[1:-1])
            curr = [df_dupe.index[i] + 2]

        prev = val
        i += 1

    dupes.append(str(curr)[1:-1])

    return dupes
