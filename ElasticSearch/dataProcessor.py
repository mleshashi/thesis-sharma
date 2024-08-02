import pandas as pd

def process_metadata(pew_metadata_path, statista_metadata_path, llava_description_path):
    # Ensure the entire text in each cell is displayed without truncation
    #pd.set_option('display.max_colwidth', None)

    # Load Pew dataset and update image paths
    pew = pd.read_csv(pew_metadata_path)
    pew['imgPath'] = pew['imgPath'].str.replace('imgs', '../dataset/pew_dataset/pew_imgs')

    # Load Statista dataset and update image paths
    statista = pd.read_csv(statista_metadata_path)
    statista['imgPath'] = statista['imgPath'].str.replace('out/two_col/imgs', '../dataset/statista_dataset/statista_imgs')

    # Load llava description dataset
    llava = pd.read_csv(llava_description_path)

    # Specify columns to keep
    columns = ['title', 'caption', 'imgPath']

    # Filter DataFrames to include only the specified columns
    pew_df = pew[columns]
    statista_df = statista[columns]

    # Combine DataFrames
    combined_df = pd.concat([pew_df, statista_df], ignore_index=True)

    # Add a new column 'ID' to the DataFrame at the first position
    combined_df.insert(0, 'id', combined_df.reset_index().index + 1)

    # Add a new column llava_description to the DataFrame from the content column of the llava description dataset
    combined_df['llava_description'] = llava['Content']

    return combined_df


def clean_text(text):
    """Cleans the text by handling newline characters and stripping spaces."""
    if pd.isna(text):
        return text
    text = text.replace('\r', ' ').replace('\n', ' ')  # Replace newline characters with a space
    return text.strip()

def correct_misinterpreted_characters(text):
    """Corrects specific misinterpreted characters in the text."""
    if pd.isna(text):
        return text
    
    # Dictionary of replacements for known misinterpretations, with `â€` placed last
    replacements = {
        'â€œ': '“',        # Left double quotation mark
        'â€“': '-',        # En dash
        'â€”': '—',        # Em dash
        'â€¦': '...',      # Ellipsis
        'â€˜': '‘',        # Left single quotation mark
        'â€™': '’',        # Right single quotation mark
        'Â ': ' ',         # Non-breaking space
        'â€?': '...',        # Question mark or corrupted text
        '”': '"',          # Right double quotation mark
        '“': '"',          # Left double quotation mark
        '”¦': '...',       # Misinterpreted ellipsis
        'â€¢': '•',        # Bullet point
        'â„¢': '™',        # Trademark symbol
        'Â©': '©',         # Copyright symbol
        'Â®': '®',         # Registered trademark symbol
        'â€': '"',         # Double quotation mark or part of ellipsis (checked last)
        '**': '',          # Remove double asterisks
    }
    
    # Perform replacements
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    
    return text.strip()


# Usage
pew_metadata_path = '../dataset/pew_dataset/metadata.csv'
statista_metadata_path = '../dataset/statista_dataset/metadata.csv'
llava_description_path = '../dataset/llava-description.csv'