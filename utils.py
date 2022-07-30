from icecream import ic, colorizedStderrPrint

LOG_FILE = "log.txt"
def writeToLog(s):
    # write to log file
    # colorizedStderrPrint(s)
    with open(LOG_FILE, "a") as f:
        f.write(s)
        f.write("\n")
        f.close()

ic.configureOutput(outputFunction=writeToLog)