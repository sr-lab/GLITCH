import subprocess

from glitch.repair.interactive.tracer_parser import parse_tracer_output

class STrace():
    def __init__(self, pid: str):
        proc = subprocess.Popen(
            ["sudo", "strace", "-v", "-s", "65536", "-e", "trace=file,write", "-f", "-p", pid], 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        for line in proc.stdout:
            if line.startswith("strace: Process"):
                continue
            print(line)
            print(parse_tracer_output(line))

STrace("42646")