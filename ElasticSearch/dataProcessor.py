import pandas as pd

def process_metadata(pew_metadata_path, statista_metadata_path):
    # Ensure the entire text in each cell is displayed without truncation
    pd.set_option('display.max_colwidth', None)

    # Load Pew dataset and update image paths
    pew = pd.read_csv(pew_metadata_path)
    pew['imgPath'] = pew['imgPath'].str.replace('imgs', '../dataset/pew_dataset/pew_imgs')

    # Load Statista dataset and update image paths
    statista = pd.read_csv(statista_metadata_path)
    statista['imgPath'] = statista['imgPath'].str.replace('out/two_col/imgs', '../dataset/statista_dataset/statista_imgs')

    # Specify columns to keep
    columns = ['title', 'caption', 'imgPath']

    # Filter DataFrames to include only the specified columns
    pew_df = pew[columns]
    statista_df = statista[columns]

    # Combine DataFrames
    combined_df = pd.concat([pew_df, statista_df], ignore_index=True)

    # Add a new column 'ID' to the DataFrame at the first position
    combined_df.insert(0, 'id', combined_df.reset_index().index + 1)

    return combined_df

# Usage
pew_metadata_path = '../dataset/pew_dataset/metadata.csv'
statista_metadata_path = '../dataset/statista_dataset/metadata.csv'