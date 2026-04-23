import subprocess
import sys


def main():
    args = sys.argv[1:]
    subprocess.check_call([sys.executable, "generate_daily_report.py", *args])
    subprocess.check_call([sys.executable, "push_to_notion.py", *args])


if __name__ == "__main__":
    main()
