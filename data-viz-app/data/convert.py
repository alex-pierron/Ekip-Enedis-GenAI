import pandas as pd
import os

def xlsx_to_csv(input_file, output_file=None):
    """
    Converts an Excel file (.xlsx) to a CSV file.

    :param input_file: Path to the input Excel file.
    :param output_file: Path to the output CSV file. If not provided, 
                        the CSV will be saved in the same directory as the input file.
    """
    try:
        # Check if the input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

        # Read the Excel file
        df = pd.read_excel(input_file)

        # Set the output file name if not provided
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = base_name + ".csv"

        # Save as CSV
        df.to_csv(output_file, index=False)
        print(f"File converted successfully: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    input_path = input("Enter the path to the Excel file (.xlsx): ").strip()
    output_path = input("Enter the path to save the CSV file (leave blank for default): ").strip()
    
    # Pass None if the output path is blank
    output_path = output_path if output_path else None

    xlsx_to_csv(input_path, output_path)

