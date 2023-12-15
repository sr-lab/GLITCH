import subprocess

class STrace():
    def __init__(self, pid: str):
        proc = subprocess.Popen(
            ["sudo", "strace", "-e", "trace=file,write", "-f", "-p", pid], 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        for line in proc.stdout:
            if "test234" in line:
                print(line)

STrace("41373")