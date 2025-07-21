import os
import pandas as pd


output_dir = "markdown"
data_dir_path = "data"
source_files = ["07_YY_BR_US_STR_WOW_MOM_Summary.csv"]
output_dir_path = os.path.join(data_dir_path, output_dir)

# Ensure output directory exists
if not os.path.exists(output_dir_path):
    os.makedirs(output_dir_path)

# Prefix the data directory path to each file
source_files = [os.path.join(data_dir_path, curr_file) for curr_file in source_files]

# Store the uploaded file IDs to be used later when enabling File Search
markdown_file_paths = []

for curr_file in source_files:
    try:
        # Check if the file exists
        if not os.path.exists(curr_file):
            raise FileNotFoundError(f"The file '{curr_file}' does not exist.")
        df = pd.read_excel(curr_file)
        print(f"Workbook '{curr_file}' successfully loaded.")
        base_name = os.path.splitext(os.path.basename(curr_file))[0]
        md_tbl_str = df.to_markdown(index=False, tablefmt="pipe")
        output_file = os.path.join(output_dir_path, f"{base_name}.md")
        markdown_file_paths.append(output_file)
        with open(output_file, "w") as f:
            f.write(md_tbl_str)
        print(f"Markdown file '{output_file}' successfully written.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred while processing the Excel file '{curr_file}': {e}")
