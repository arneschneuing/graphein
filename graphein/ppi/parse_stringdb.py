"""Functions for making and parsing API calls to STRINGdb"""
# %%
# Graphein
# Author: Ramon Vinas, Arian Jamasb <arian@jamasb.io>
# License: MIT
# Project Website: https://github.com/a-r-j/graphein
# Code Repository: https://github.com/a-r-j/graphein
import logging
from typing import Any, Dict, List, Union

import pandas as pd
import requests

log = logging.getLogger(__name__)


def params_STRING(
    params: Dict[str, Union[str, int, List[str], List[int]]], **kwargs
) -> Dict[str, Union[str, int]]:
    """
    Updates default parameters with user parameters for the method "network" of the STRING API REST.
    See also https://string-db.org/help/api/

    :param params: Dictionary of default parameters
    :type params: Dict[str, Union[str, int, List[str], List[int]]]
    :param kwargs: User parameters for the method "network" of the STRING API REST. The key must start with "STRING"
    :return: Dictionary of parameters
    :rtype: Dict[str, Union[str, int]]
    """
    # TODO: Might be possible to generalise this function for all sources
    fields = [
        "species",  # NCBI taxon identifiers
        "required_score",  # threshold of significance to include a interaction, a number between 0 and 1000
        # (default depends on the network)
        "network_type",  # network type: functional (default), physical
        "add_nodes",  # adds a number of proteins to the network based on their confidence score,
        # e.g., extends the interaction neighborhood of selected proteins to desired value
        "show_query_node_labels"  # when available use submitted names in the preferredName column when
        # (0 or 1) (default:0)
    ]
    for p in fields:
        kwarg_name = "STRING_" + p
        if kwarg_name in kwargs:
            value = kwargs[kwarg_name]
            if type(value) is list:
                value = "%0d".join(value)
            params[p] = value
    return params


def parse_STRING(
    protein_list: List[str],
    ncbi_taxon_id: Union[int, str, List[int], List[str]],
    **kwargs,
) -> pd.DataFrame:
    """
    Makes STRING API call and returns a source specific Pandas dataframe.
    See also [1] STRING: https://string-db.org/help/api/

    :param protein_list: Proteins to include in the graph
    :type protein_list: List[str]
    :param ncbi_taxon_id: NCBI taxonomy identifiers for the organism. Default is 9606 (Homo Sapiens)
    :type ncbi_taxon_id: int
    :param kwargs: Parameters of the "network" method of the STRING API REST, used to select the results. The
                   parameter names are of the form STRING_<param>, where <param> is the name of the parameter.
                   Information about these parameters can be found at [1].
    :return: Source specific Pandas dataframe.
    :rtype: pd.DataFrame
    """
    # Prepare call to STRING API
    string_api_url = "https://string-db.org/api"
    output_format = "json"  # "tsv-no-header"
    method = "network"
    request_url = "/".join([string_api_url, output_format, method])
    if type(ncbi_taxon_id) is list:
        ncbi_taxon_id = "%0d".join(ncbi_taxon_id)
    params = {
        "identifiers": "%0d".join(protein_list),
        "species": ncbi_taxon_id,  # 9606 is human
        "caller_identity": "graphein",
    }
    params = params_STRING(params, **kwargs)

    # Call STRING
    response = requests.post(request_url, data=params)
    df = pd.read_json(response.text.strip())

    return df


def filter_STRING(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Filters results of the STRING API call according to user kwargs, keeping rows where the input parameters are
    greater or equal than the input thresholds

    :param df: Source specific Pandas dataframe (STRING) with results of the API call
    :type df: pd.DataFrame
    :param kwargs: User thresholds used to filter the results. The parameter names are of the form STRING_<param>,
                   where <param> is the name of the parameter. All the parameters are numerical values.
    :return: Source specific Pandas dataframe with filtered results
    :rtype: pd.DataFrame
    """
    scores = [
        "score",  # combined score
        "nscore",  # gene neighborhood score
        "fscore",  # gene fusion score
        "pscore",  # phylogenetic profile score
        "ascore",  # coexpression score
        "escore",  # experimental score
        "dscore",  # database score
        "tscore",
    ]  # textmining score]
    for s in scores:
        kwarg_name = "STRING_" + s
        if kwarg_name in kwargs:
            threshold = kwargs[kwarg_name]
            df = df[df[s] >= threshold]
    return df


def standardise_STRING(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardises STRING dataframe, e.g. puts everything into a common format

    :param df: Source specific Pandas dataframe
    :type df: pd.DataFrame
    :return: Standardised dataframe
    :rtype: pd.DataFrame
    """
    if df.empty:
        return pd.DataFrame({"p1": [], "p2": [], "source": []})

    # Rename & delete columns
    df = df.rename(columns={"preferredName_A": "p1", "preferredName_B": "p2"})
    df = df[["p1", "p2"]]

    # Add source column
    df["source"] = "STRING"

    return df


def STRING_df(
    protein_list: List[str],
    ncbi_taxon_id: Union[int, str, List[int], List[str]],
    **kwargs,
) -> pd.DataFrame:
    """
    Generates standardised dataframe with STRING protein-protein interactions, filtered according to user's input

    :param protein_list: List of proteins (official symbol) that will be included in the PPI graph
    :type protein_list: List[str]
    :param ncbi_taxon_id: NCBI taxonomy identifiers for the organism. 9606 corresponds to Homo Sapiens
    :type ncbi_taxon_id: int
    :param kwargs:  Additional parameters to pass to STRING API calls
    :return: Standardised dataframe with STRING interactions
    :rtype: pd.DataFrame
    """
    df = parse_STRING(
        protein_list=protein_list, ncbi_taxon_id=ncbi_taxon_id, **kwargs
    )
    df = filter_STRING(df, **kwargs)
    df = standardise_STRING(df)

    return df


if __name__ == "__main__":
    protein_list = [
        "CDC42",
        "CDK1",
        "KIF23",
        "PLK1",
        "RAC2",
        "RACGAP1",
        "RHOA",
        "RHOB",
    ]
    sources = ["STRING", "BIOGRID"]
    kwargs = {
        "STRING_escore": 0.2,  # Keeps STRING interactions with an experimental score >= 0.2
        "BIOGRID_throughputTag": "high",  # Keeps high throughput BIOGRID interactions
    }

    df = STRING_df(
        protein_list=protein_list, ncbi_taxon_id=9606, kwargs=kwargs
    )

    print(df)
