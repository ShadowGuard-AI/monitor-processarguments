# monitor-processarguments
Monitors command-line arguments used when starting new processes. Logs these arguments for later analysis of potential malicious activity. - Focused on System monitoring and alerts

## Install
`git clone https://github.com/ShadowGuardAI/monitor-processarguments`

## Usage
`./monitor-processarguments [params]`

## Parameters
- `-h`: Show help message and exit
- `-i`: Interval in seconds to check for new processes. Defaults to 5.
- `-l`: Path to the log file. Defaults to process_monitor.log.
- `-e`: List of process names to exclude from monitoring. Example: -e process1 process2

## License
Copyright (c) ShadowGuardAI
