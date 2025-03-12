import os
import re
from datetime import datetime

def parse_solution_file(filepath):
    """
    Parse a solution file and extract performance metrics
    
    Args:
        filepath (str): Path to the solution file
    
    Returns:
        dict: Extracted performance metrics
    """
    metrics = {
        'time_taken': 0,
        'peak_memory': 0,
        'states_explored': 0,
        'states_generated': 0,
        'states_per_second': 0,
        'solution_length': 0
    }
    
    try:
        with open(filepath, 'r') as file:
            content = file.read()
            
            # Extract metrics using regex
            time_match = re.search(r'Time taken: ([\d.]+) seconds', content)
            if time_match:
                metrics['time_taken'] = float(time_match.group(1))
            
            peak_memory_match = re.search(r'Peak memory usage: ([\d.]+) MB', content)
            if peak_memory_match:
                metrics['peak_memory'] = float(peak_memory_match.group(1))
            
            states_explored_match = re.search(r'States explored: (\d+)', content)
            if states_explored_match:
                metrics['states_explored'] = int(states_explored_match.group(1))
            
            states_generated_match = re.search(r'States generated: (\d+)', content)
            if states_generated_match:
                metrics['states_generated'] = int(states_generated_match.group(1))
            
            states_per_second_match = re.search(r'States per second: ([\d.]+)', content)
            if states_per_second_match:
                metrics['states_per_second'] = float(states_per_second_match.group(1))
            
            solution_length_match = re.search(r'Solution length: (\d+)', content)
            if solution_length_match:
                metrics['solution_length'] = int(solution_length_match.group(1))
    
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return metrics

def analyze_solution_files(file_list, true_solution_lengths, heuristic, difficulty):
    """
    Analyze multiple solution files and calculate metrics
    
    Args:
        file_list (list): List of solution file paths
        true_solution_lengths (list): List of true solution lengths for each game
        heuristic (str): Heuristic used in the search
        difficulty (str): Difficulty level or description
    
    Returns:
        dict: Metrics for each file and overall statistics
    """
    all_metrics = []
    solution_length_diffs = []
    
    for filepath, true_length in zip(file_list, true_solution_lengths):
        metrics = parse_solution_file(filepath)
        
        # Calculate solution length difference
        metrics['solution_length_diff'] = metrics['solution_length'] - true_length
        solution_length_diffs.append(metrics['solution_length_diff'])
        
        all_metrics.append(metrics)
    
    # Calculate overall statistics
    stats = {
        'heuristic': heuristic,
        'difficulty': difficulty,
        'time_taken': {
            'values': [m['time_taken'] for m in all_metrics],
            'average': sum(m['time_taken'] for m in all_metrics) / len(all_metrics)
        },
        'peak_memory': {
            'values': [m['peak_memory'] for m in all_metrics],
            'average': sum(m['peak_memory'] for m in all_metrics) / len(all_metrics)
        },
        'states_explored': {
            'values': [m['states_explored'] for m in all_metrics],
            'average': sum(m['states_explored'] for m in all_metrics) / len(all_metrics)
        },
        'states_generated': {
            'values': [m['states_generated'] for m in all_metrics],
            'average': sum(m['states_generated'] for m in all_metrics) / len(all_metrics)
        },
        'states_per_second': {
            'values': [m['states_per_second'] for m in all_metrics],
            'average': sum(m['states_per_second'] for m in all_metrics) / len(all_metrics)
        },
        'solution_length_diff': {
            'values': solution_length_diffs,
            'average': sum(solution_length_diffs) / len(solution_length_diffs)
        }
    }
    
    return stats

def print_and_save_results(results, output_file=None):
    """
    Print results to console and optionally save to a file
    
    Args:
        results (dict): Analysis results
        output_file (str, optional): Path to output file
    """
    # Prepare output string
    output = []
    output.append(f"Heuristic: {results['heuristic']}")
    output.append(f"Difficulty: {results['difficulty']}")
    output.append("-" * 40)
    
    # Add each metric to output
    metrics_to_display = [
        'time_taken', 
        'peak_memory', 
        'states_explored', 
        'states_generated', 
        'states_per_second', 
        'solution_length_diff'
    ]
    
    for metric in metrics_to_display:
        output.append(f"{metric.replace('_', ' ').title()}:")
        output.append(f"  Values: {results[metric]['values']}")
        output.append(f"  Average: {results[metric]['average']:.2f}")
        output.append("")
    
    # Print to console
    print("\n".join(output))
    
    # Save to file if output_file is provided
    if output_file:
        with open(output_file, 'w') as f:
            f.write("\n".join(output))
        print(f"\nResults saved to {output_file}")

# Example usage for multiple heuristics
def main():
    # Heuristic 1
    solution_files_heu1 = [
        "solutions/solution_game_32483_Meta2.txt",
        "solutions/solution_game_20810_Meta2.txt",
    ]
    true_solution_lengths_1 = [94, 89, 86, 78]
    

    
    # Create output directory if it doesn't exist
    os.makedirs('analysis_results', exist_ok=True)
    
    # Analyze and save results for Heuristic 1
    results_heu1 = analyze_solution_files(
        solution_files_heu1, 
        true_solution_lengths_1, 
        heuristic="Meta2", 
        difficulty="Hard"
    )
    print_and_save_results(
        results_heu1, 
        output_file='analysis_results/Meta2_Hard.txt'
    )
    
    print("\n" + "="*50 + "\n")
    


if __name__ == "__main__":
    main()