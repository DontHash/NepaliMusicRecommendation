import os
import pandas as pd

def merge_csv_files(input_dir, output_file, log_file):
    all_dataframes = []

    for file in os.listdir(input_dir):
        if file.endswith(".csv"):
            file_path = os.path.join(input_dir, file)
            try:
                df = pd.read_csv(
                    file_path,
                    encoding="utf-8-sig",
                    on_bad_lines="skip",
                    header=None,
                    names=["transliteration","devanagari"]
                )
                df["source_file"] = file  # keep track of origin
                all_dataframes.append(df)
            except Exception as e:
                print(f"⚠️ Skipped {file} due to error: {e}")

    merged_df = pd.concat(all_dataframes, ignore_index=True)

    # Find duplicates based on transliteration
    duplicates = merged_df[merged_df.duplicated(subset=["transliteration"], keep="first")]

    
    duplicates.to_csv(log_file, index=False, encoding="utf-8-sig")

    
    clean_df = merged_df.drop_duplicates(subset=["transliteration"], keep="first")
    clean_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"Merged dataset saved to {output_file}")
    print(f"Duplicate entries logged to {log_file}")
    print(f"Total rows after cleaning: {len(clean_df)}")

if __name__ == "__main__":
    merge_csv_files("./Transliteral_Data", "merged_dataset.csv", "duplicates_log.csv")
