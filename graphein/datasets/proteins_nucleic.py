"""Class for working with the PROTEINS_NUCLEIC dataset"""


# License: MIT
# Code Repository: https://github.com/a-r-j/graphein
from functools import lru_cache
# Graphein
# Author: Arian Jamasb <arian@jamasb.io>
from pathlib import Path

import pandas as pd

from graphein.datasets.base import AbstractClassificationDataset


class PROTEINS_NUCLEIC(AbstractClassificationDataset):
    @lru_cache
    def _load_dataset(self=None) -> pd.DataFrame:
        file_path = (
            Path(__file__).parent.parent.parent.resolve()
            / "datasets"
            / "proteins_nucleic"
            / "PROTEINS_NUCLEIC.csv"
        )
        return pd.read_csv(file_path)

    def split_data(
        self,
        strategy: str = "random",
        training_size: float = 0.7,
        validation_size: float = 0.2,
        test_size: float = 0.1,
        shuffle: bool = True,
    ):
        train_df, val_df, test_df = self._split_data(
            strategy, training_size, validation_size, test_size, shuffle
        )

        self.train: PROTEINS_NUCLEIC = PROTEINS_NUCLEIC(train_df)
        self.validation: PROTEINS_NUCLEIC = PROTEINS_NUCLEIC(val_df)
        self.test: PROTEINS_NUCLEIC = PROTEINS_NUCLEIC(test_df)


if __name__ == "__main__":
    c = PROTEINS_NUCLEIC()