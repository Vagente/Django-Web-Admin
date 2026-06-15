import argparse
import os

# Run the login_tty on the slave fd, as os.fork() and preexec_fn are not safe when used in multi-thread apps.

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--slave_fd", required=True)
    args = parser.parse_args()
    os.login_tty(int(args.slave_fd))
    term = os.environ["TERM"] if "TERM" in os.environ else "xterm-256color"
    term_env: dict = {"TERM": term}
    os.execve("/usr/bin/su", ("django_su", "--login", args.username), env=term_env)

if __name__ == "__main__":
    main()