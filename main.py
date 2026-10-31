import argparse
import logging
import psutil
import sys
import time
import os

MAX_CONSECUTIVE_FAILURES = 5
MASKED = "<masked>"

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
    if not process_name:
        return False
    for excluded_process in exclude_list:
        if process_name.lower() == excluded_process.lower():
            return True
    return False

def mask_cmdline(cmdline):
    """
    Builds the loggable form of a command line. The executable name and the
    argument names (flags, option names, and the name half of a name=value
    pair) are kept, and every argument value is replaced with a masked
    placeholder, so no argument value is ever logged in clear.
    """
    if not cmdline:
        return ""
    parts = [str(cmdline[0])]
    for arg in cmdline[1:]:
        arg = str(arg)
        if arg.startswith("-") and "=" in arg:
            parts.append(arg.split("=", 1)[0] + "=" + MASKED)
        elif arg.startswith("-") and len(arg) > 1:
            parts.append(arg)
        else:
            parts.append(MASKED)
    return ' '.join(parts)

def process_key(process):
    """
    Returns the identity key for a process: its PID plus its create time,
    so a new process reusing an exited process's PID is still distinct.
    """
    pid = process.info['pid']
    create_time = process.info.get('create_time') if isinstance(process.info, dict) else None
    if create_time is None:
        try:
            create_time = process.create_time()
        except Exception:
            create_time = None
    return (pid, create_time)

def monitor_processes(interval, logfile, exclude_list):
    """
    Monitors newly created processes and logs their command-line arguments.

    Args:
        interval (int): The interval (in seconds) to check for new processes.
        logfile (str): The path to the log file.
        exclude_list (list): List of process names to exclude.
    """
    logging.info(f"Starting process monitor with interval: {interval} seconds, logfile: {logfile}, excludes: {exclude_list}")

    # Prime the known set with a silent baseline pass, so only processes
    # that start after the monitor does are reported as new.
    known_processes = set()
    try:
        for process in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                known_processes.add(process_key(process))
            except Exception:
                continue
    except psutil.Error as e:
        logging.error(f"psutil error during baseline pass: {e}")

    consecutive_failures = 0

    while True:
        cycle_failed = False
        try:
            current_processes = set()
            for process in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    pid = process.info['pid']
                    name = process.info['name']
                    cmdline = process.info['cmdline'] or []
                    key = process_key(process)
                    current_processes.add(key)

                    if key not in known_processes:
                        if not is_excluded(name, exclude_list):
                            masked_cmdline = mask_cmdline(cmdline)
                            argument_count = len(cmdline)
                            logging.info(f"New process detected: PID={pid}, Name={name}, Argument Count={argument_count}, Command Line={masked_cmdline}")

                            # Log to file (append)
                            with open(logfile, "a") as f:
                                f.write(f"PID: {pid}, Name: {name}, Argument Count={argument_count}, Command Line={masked_cmdline}\n")
                        else:
                            logging.debug(f"Process {name} (PID {pid}) excluded from monitoring.")
                        known_processes.add(key)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logging.error(f"Error processing a process, skipping it: {e}")
                    continue
            # Prune processes that are no longer present, so the known set
            # tracks live processes and a reused PID is seen as new.
            known_processes.intersection_update(current_processes)
            consecutive_failures = 0

        except psutil.Error as e:
            logging.error(f"psutil error: {e}")
            consecutive_failures += 1
            cycle_failed = True
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            break # Exit the loop if an unrecoverable error occurs
        finally:
            time.sleep(interval)

        if cycle_failed and consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logging.error(f"Exiting after {MAX_CONSECUTIVE_FAILURES} consecutive monitoring failures.")
            print(f"Error: Exiting after {MAX_CONSECUTIVE_FAILURES} consecutive monitoring failures.")
            sys.exit(1)

def main():
    """
    Main function to parse arguments and start the process monitor.
    """
    args = setup_argparse()

    # Validate inputs (example: interval must be positive)
    if args.interval <= 0:
        logging.error("Interval must be a positive integer.")
        print("Error: Interval must be a positive integer.") # Also print to stdout for immediate feedback
        sys.exit(1)

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