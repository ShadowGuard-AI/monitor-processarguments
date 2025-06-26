import argparse
import logging
import psutil
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Monitors command-line arguments used when starting new processes.")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Interval in seconds to check for new processes. Defaults to 5.")
    parser.add_argument("-l", "--logfile", type=str, default="process_monitor.log", help="Path to the log file. Defaults to process_monitor.log.")
    parser.add_argument("-e", "--exclude", type=str, nargs='*', default=[], help="List of process names to exclude from monitoring. Example: -e process1 process2")
    return parser.parse_args()

def is_excluded(process_name, exclude_list):
    """
    Checks if a process name is in the exclude list.  Case-insensitive comparison.
    """
    for excluded_process in exclude_list:
        if process_name.lower() == excluded_process.lower():
            return True
    return False

def monitor_processes(interval, logfile, exclude_list):
    """
    Monitors newly created processes and logs their command-line arguments.

    Args:
        interval (int): The interval (in seconds) to check for new processes.
        logfile (str): The path to the log file.
        exclude_list (list): List of process names to exclude.
    """
    logging.info(f"Starting process monitor with interval: {interval} seconds, logfile: {logfile}, excludes: {exclude_list}")

    # Store already known process ids to avoid duplicates
    known_pids = set()

    while True:
        try:
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                pid = process.info['pid']
                name = process.info['name']
                cmdline = process.info['cmdline']

                if pid not in known_pids:
                    if not is_excluded(name, exclude_list):
                        try:
                            # Sanitize the command line arguments for security.  Specifically, prevent shell injection.
                            sanitized_cmdline = ' '.join(map(repr, cmdline)) # Quote arguments to prevent interpretation
                            logging.info(f"New process detected: PID={pid}, Name={name}, Command Line={sanitized_cmdline}")

                            # Log to file (append)
                            with open(logfile, "a") as f:
                                f.write(f"PID: {pid}, Name: {name}, Command Line: {sanitized_cmdline}\n")

                        except Exception as e:
                            logging.error(f"Error processing process {pid}: {e}")
                    else:
                        logging.debug(f"Process {name} (PID {pid}) excluded from monitoring.")
                    known_pids.add(pid)
            time.sleep(interval)

        except psutil.Error as e:
            logging.error(f"psutil error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            break # Exit the loop if an unrecoverable error occurs

def main():
    """
    Main function to parse arguments and start the process monitor.
    """
    args = setup_argparse()

    # Validate inputs (example: interval must be positive)
    if args.interval <= 0:
        logging.error("Interval must be a positive integer.")
        print("Error: Interval must be a positive integer.") # Also print to stdout for immediate feedback
        return  # Exit program

    try:
        monitor_processes(args.interval, args.logfile, args.exclude)
    except KeyboardInterrupt:
        logging.info("Process monitor stopped by user.")

if __name__ == "__main__":
    # Example Usage 1:  Run with default settings
    # python main.py
    #
    # Example Usage 2: Run with 10-second interval, custom log file, and exclude 'chrome'
    # python main.py -i 10 -l my_process_log.txt -e chrome
    #
    # Example Usage 3:  Exclude multiple processes
    # python main.py -e chrome firefox
    main()