![Banner](banner.png)

# monitor-processarguments
Monitors command-line arguments used when starting new processes. Logs the shape of these arguments for later analysis of potential malicious activity. - Focused on System monitoring and alerts

Argument values are never logged in clear, in the console stream or in the log file. Each new process is recorded with its executable name, its argument names (flags, option names, and the name half of a name=value pair), and its argument count, with every argument value replaced by a masked placeholder. Processes already running when the monitor starts are taken as a silent baseline and are not reported; only processes that start afterwards are reported as new. A process is identified by its PID plus its process create time, so a new process reusing an exited process's PID is still reported. An interval that is not positive exits 1 at startup, and the monitor exits 1 after 5 consecutive monitoring failures.

## Install
`git clone https://github.com/ShadowGuardAI/monitor-processarguments`

## Usage
`python main.py [params]`

## Parameters
- `-h`: Show help message and exit
- `-i`: Interval in seconds to check for new processes. Defaults to 5.
- `-l`: Path to the log file. Defaults to process_monitor.log.
- `-e`: List of process names to exclude from monitoring. Example: -e process1 process2

## License
Copyright (c) ShadowGuardAI
