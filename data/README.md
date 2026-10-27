# IKN research data

Source files retain their original names and contents so they can be traced back to the research notebooks.

| Directory | Contents | Used for |
| --- | --- | --- |
| `raw/` | Labelled train, validation, and test CSVs | Exploration and sentiment distribution |
| `processed/` | Preprocessed TSVs | IndoBERT training and evaluation |
| `external/` | Indonesian slang and stopword dictionaries | Preprocessing new sentences |
| `predictions/` | Saved notebook prediction CSVs | Historical evaluation and Top2Vec input |

Application-generated outputs are saved in `backend/reports/`, separately from source data. Checkpoints are stored in `backend/models/`.

Set `IKN_DATA_DIR` to use another data directory with the same structure. Flat directories from older integrations are also supported. Notebook locations are configured separately through `IKN_NOTEBOOKS_DIR`.
