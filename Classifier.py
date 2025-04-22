#!/usr/bin/env python3
"""
Treaty Mention Classifier - Combined CLI Interface and Classifier
This script provides a command-line interface for the treaty classifier without requiring any GUI libraries.
The Google API key has been removed for security purposes.
"""
import os
import sys
import time
import pandas as pd
import argparse
from datetime import datetime
import csv
import io

# Placeholder for the API configuration
# You'll need to add your API key when using this code
# Configure with: genai.configure(api_key="YOUR_API_KEY_HERE")

def classify_treaty(text, max_attempts=5):
    """
    Categorize the treaty mention into predefined categories.
    
    Note: This is a placeholder implementation. To use with Gemini API:
    1. Install the google-generativeai package
    2. Import the library: import google.generativeai as genai
    3. Configure with your API key
    4. Uncomment and modify the implementation below
    """
    # IMPORTANT: Replace this placeholder with actual implementation when using
    print(f"  Classification request for text ({len(text)} chars)...")
    print("  NOTE: Using placeholder classification - API key required for real classification")
    
    # Placeholder implementation - in production, replace with:
    """
    prompt = f'''
    Categorize the following treaty mention into ONLY one of these categories:
    1. Support
    2. Against
    3. Implementation
    4. Reversal
    5. Other/Factual
    Mention:
    '''{text}'''
    Respond ONLY with the category name.
    '''
    
    # Make the text shorter if it's too long
    if len(text) > 1000:
        print(f"Text is quite long ({len(text)} chars), truncating to 1000 chars...")
        text = text[:997] + "..."
    
    for attempt in range(max_attempts):
        try:
            print(f"  API call attempt {attempt+1}/{max_attempts}...")
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            result = response.text.strip()
            print(f"  Classification result: {result}")
            return result
        except Exception as e:
            # Error handling code...
    """
    
    # Return a random category for demonstration
    import random
    categories = ["Support", "Against", "Implementation", "Reversal", "Other/Factual"]
    result = random.choice(categories)
    print(f"  Classification result (PLACEHOLDER): {result}")
    return result

def process_file(file_path, search_term, batch_size=10, check_running=None):
    """
    Process a file to find and classify mentions of a search term.
    
    Args:
        file_path: Path to the file to process
        search_term: Term to search for in the file
        batch_size: Number of speeches to process before taking a break
        check_running: Optional callback function that returns False if processing should stop
    
    Returns:
        DataFrame containing the speeches and classifications
    """
    try:
        start_time = datetime.now()
        print(f"Started processing at {start_time}")
        
        # Define a default check_running function if none provided
        if check_running is None:
            check_running = lambda: True
            
        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"File size: {file_size:.2f} MB")
        
        # This will store the speeches containing our search term
        matching_speeches = []
        speech_ids = []
        
        # Try reading with different encodings
        for encoding in encodings:
            try:
                print(f"Attempting to read with {encoding} encoding...")
                speeches_found = 0
                
                # Read the file as CSV with pipe delimiter
                with open(file_path, 'r', encoding=encoding) as f:
                    # Skip the header row
                    header = f.readline()
                    
                    # Process each line (speech)
                    for line_num, line in enumerate(f, 2):  # Start at 2 because we skipped header
                        # Check if we should stop processing
                        if not check_running():
                            print("Processing stopped by user.")
                            if matching_speeches:
                                break
                            else:
                                return None
                            
                        try:
                            # Split the line by pipe delimiter
                            parts = line.strip().split('|', 1)
                            if len(parts) >= 2:
                                speech_id = parts[0]
                                speech_text = parts[1]
                                
                                # Check if this speech contains our search term
                                if search_term.lower() in speech_text.lower():
                                    matching_speeches.append(speech_text)
                                    speech_ids.append(speech_id)
                                    speeches_found += 1
                                
                                # Print progress every 100,000 lines
                                if line_num % 100000 == 0:
                                    print(f"Processed {line_num} lines, found {speeches_found} matches so far...")
                        except Exception as e:
                            print(f"Warning: Error processing line {line_num}: {e}")
                            continue
                
                print(f"Successfully read file with {encoding} encoding.")
                print(f"Found {speeches_found} speeches containing '{search_term}'.")
                break
                
            except UnicodeDecodeError:
                print(f"Failed to read with {encoding} encoding.")
                continue
        
        if not matching_speeches:
            print(f"No speeches found containing '{search_term}'.")
            return None
        
        # Display sample of first match if available
        if matching_speeches:
            sample = matching_speeches[0][:100] + "..." if len(matching_speeches[0]) > 100 else matching_speeches[0]
            print(f"First match sample (Speech ID {speech_ids[0]}): {sample}")
        
        # Process speeches in batches to better handle rate limits
        results = []
        total_speeches = len(matching_speeches)
        
        print(f"\nProcessing {total_speeches} speeches in batches of {batch_size}...")
        
        for batch_start in range(0, total_speeches, batch_size):
            # Check if processing should stop
            if not check_running():
                print("Processing stopped by user.")
                break
                
            batch_end = min(batch_start + batch_size, total_speeches)
            print(f"\nStarting batch {batch_start//batch_size + 1}/{(total_speeches + batch_size - 1)//batch_size}")
            
            # Process each speech in the current batch
            for i in range(batch_start, batch_end):
                # Check if processing should stop
                if not check_running():
                    print("Processing stopped by user.")
                    break
                    
                speech_id = speech_ids[i]
                speech_text = matching_speeches[i]
                
                print(f"Classifying speech {i+1}/{total_speeches} (ID: {speech_id})...")
                category = classify_treaty(speech_text)
                
                results.append({
                    "Speech_ID": speech_id,
                    "Mention": speech_text, 
                    "Category": category
                })
                
                # Add a small delay between speeches within a batch
                if i < batch_end - 1 and check_running():
                    print("Waiting 2 seconds before next classification...")
                    time.sleep(2)
            
            # After each batch, save interim results
            interim_df = pd.DataFrame(results)
            interim_file = f"interim_results_{search_term}_{batch_end}.csv"
            interim_df.to_csv(interim_file, index=False)
            print(f"Saved interim results to {interim_file}")
            
            # If there are more batches remaining, take a longer break to avoid rate limits
            if batch_end < total_speeches and check_running():
                wait_time = 60  # Wait 60 seconds between batches
                print(f"Completed batch {batch_start//batch_size + 1}. Waiting {wait_time} seconds before next batch...")
                
                # Wait in smaller intervals so we can check if we should stop
                for _ in range(wait_time):
                    if not check_running():
                        print("Processing stopped by user during batch wait.")
                        break
                    time.sleep(1)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"Processing completed at {end_time}")
        print(f"Total processing time: {duration:.2f} seconds")
        
        return pd.DataFrame(results)
    
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header."""
    print("=" * 70)
    print("Treaty Mention Classifier".center(70))
    print("=" * 70)
    print()

def get_file_path():
    """Get the file path from the user."""
    while True:
        file_path = input("Enter the path to the speeches file (or 'q' to quit): ")
        if file_path.lower() == 'q':
            return None
            
        # Check if the file exists
        if os.path.isfile(file_path):
            return file_path
        else:
            print(f"Error: File '{file_path}' not found. Please try again.")

def get_search_term():
    """Get the search term from the user."""
    while True:
        search_term = input("Enter the search term (treaty name or keyword, or 'q' to quit): ")
        if search_term.lower() == 'q':
            return None
        if search_term:
            return search_term
        print("Error: Search term cannot be empty. Please try again.")

def get_batch_size():
    """Get the batch size from the user."""
    while True:
        try:
            batch_size = input("Enter the batch size (1-10, default is 3, or 'q' to quit): ")
            if batch_size.lower() == 'q':
                return None
            if not batch_size:
                return 3
            batch_size = int(batch_size)
            if 1 <= batch_size <= 10:
                return batch_size
            print("Error: Batch size must be between 1 and 10.")
        except ValueError:
            print("Error: Please enter a valid number.")

def run_analysis(file_path, search_term, batch_size):
    """Run the treaty analysis."""
    print("\nStarting analysis...")
    print(f"File: {file_path}")
    print(f"Search term: '{search_term}'")
    print(f"Batch size: {batch_size}")
    print("-" * 70)
    
    try:
        start_time = datetime.now()
        results_df = process_file(file_path, search_term, batch_size)
        
        if results_df is not None and not results_df.empty:
            # Save results
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = f"{base_name}_{search_term}_classified.csv"
            results_df.to_csv(output_file, index=False)
            
            # Display statistics
            print("\n" + "=" * 70)
            print("Analysis Results".center(70))
            print("=" * 70)
            print(f"Total speeches analyzed: {len(results_df)}")
            
            print("\nCategory counts:")
            for category, count in results_df['Category'].value_counts().items():
                print(f"  - {category}: {count}")
                
            print(f"\nResults saved to: {output_file}")
            
            # Display the first few results
            print("\nSample Results (first 5 speeches):")
            print("-" * 70)
            for i, (_, row) in enumerate(results_df.head(5).iterrows()):
                print(f"Speech {i+1} (ID: {row['Speech_ID']})")
                print(f"Category: {row['Category']}")
                snippet = row['Mention'][:100] + "..." if len(row['Mention']) > 100 else row['Mention']
                print(f"Snippet: {snippet}")
                print("-" * 70)
        else:
            print("\nNo mentions found or analysis was interrupted.")
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to return to the main menu...")

def cli_main():
    """Main application loop for the CLI interface."""
    try:
        while True:
            clear_screen()
            print_header()
            
            print("Options:")
            print("1. Run Treaty Analysis")
            print("2. Quit")
            
            choice = input("\nEnter your choice (1-2): ")
            
            if choice == '1':
                clear_screen()
                print_header()
                
                file_path = get_file_path()
                if file_path is None:
                    continue
                    
                search_term = get_search_term()
                if search_term is None:
                    continue
                    
                batch_size = get_batch_size()
                if batch_size is None:
                    continue
                
                run_analysis(file_path, search_term, batch_size)
                
            elif choice == '2':
                print("\nGoodbye!")
                break
                
            else:
                print("\nInvalid choice. Please try again.")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nGoodbye!")

def command_line_main():
    """Main function for command-line arguments."""
    parser = argparse.ArgumentParser(description='Classify treaty mentions in a text file.')
    parser.add_argument('file', nargs='?', help='Path to the text file')
    parser.add_argument('search_term', nargs='?', help='Treaty name or keyword to search for')
    parser.add_argument('--output', '-o', help='Output CSV file path (optional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--limit', '-l', type=int, default=0, 
                        help='Limit the number of speeches to process (0 for no limit)')
    parser.add_argument('--batch-size', '-b', type=int, default=5,
                        help='Number of speeches to process before taking a longer break (default: 5)')
    
    args = parser.parse_args()
    
    # If no arguments provided, run the interactive CLI
    if args.file is None:
        cli_main()
        return
    
    if args.verbose:
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        return
    
    if args.search_term is None:
        print("Error: Search term is required.")
        parser.print_help()
        return
    
    print(f"Processing file: {args.file}")
    print(f"Searching for: {args.search_term}")
    print(f"Using batch size: {args.batch_size}")
    
    results_df = process_file(args.file, args.search_term, batch_size=args.batch_size)
    
    if results_df is not None and not results_df.empty:
        # Determine output file path
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(os.path.basename(args.file))[0]
            output_file = f"{base_name}_{args.search_term}_classified.csv"
        
        # Save results to CSV
        results_df.to_csv(output_file, index=False)
        print(f"Results saved to: {output_file}")
        
        # Display sample results
        print("\nSample classifications:")
        pd.set_option('display.max_colwidth', 100)  # Set width for better display
        print(results_df.head(5))
        
        # Print counts by category
        if not results_df.empty:
            print("\nCategory counts:")
            print(results_df['Category'].value_counts())
    else:
        print("No results to save.")

if __name__ == "__main__":
    command_line_main()
