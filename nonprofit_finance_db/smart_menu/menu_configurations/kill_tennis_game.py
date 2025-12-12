import pexpect

def find_and_kill_process(process_name):
    try:
        # Run ps -ef to get all processes
        child = pexpect.spawn('ps -ef')
        child.expect(pexpect.EOF)
        output = child.before.decode('utf-8')

        pids_to_kill = []

        # Parse the output to find all matching PIDs
        for line in output.splitlines():
            if process_name in line and 'grep' not in line:
                parts = line.split()
                pid = parts[1]  # PID is in the second column
                pids_to_kill.append(pid)

        if not pids_to_kill:
            print(f"No process found matching: {process_name}")
            return

        # Kill all found processes
        for pid in pids_to_kill:
            print(f"Killing process {process_name} with PID: {pid}")
            kill_cmd = f"sudo kill -9 {pid}"
            child_kill = pexpect.spawn(kill_cmd)
            child_kill.expect(pexpect.EOF)

        print("All matching processes killed.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_and_kill_process("./run_remote_listener")
    find_and_kill_process("./blink_round_robin_demo")
    find_and_kill_process("./pickle_digi")
    find_and_kill_process("./test_pickle_battery")
    find_and_kill_process("./run_pickle_listener")
    find_and_kill_process("./pickle_cpp_remote")
    find_and_kill_process("./tennis-game")

