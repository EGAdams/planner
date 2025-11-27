import subprocess

# Get the list of all modified and deleted files
result = subprocess.run([git, status, --porcelain], capture_output=True, text=True)

# Extract file paths from git status output
files_to_restore = []
for line in result.stdout.splitlines():
    status, file = line[:2], line[3:]  # Extract status and file path
    if status in ( D,  M):  # 'D' means deleted, 'M' means modified
        files_to_restore.append(file)

# Restore all files
if files_to_restore:
    subprocess.run([git, restore] + files_to_restore, check=True)
    print(Restored the following files:)
    for file in files_to_restore:
        print(f - {file})
else:
    print(No modified or deleted files to restore.)