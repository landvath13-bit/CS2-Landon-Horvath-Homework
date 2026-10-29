# Landon Horvath
# CS 1350 - Homework 7: File Processing

import json
import pickle
import os
import shutil


# Problem 1: Security Log Splitter and Status Report

def split_logs(machines):
    """Split machine logs by level and return each machine's counts."""
    counts = {}

    with open("info.log", "w") as info_file, open("warning.log", "w") as warning_file, open("error.log", "w") as error_file:
        for machine, filename in machines.items():
            counts[machine] = {"INFO": 0, "WARNING": 0, "ERROR": 0}

            with open(filename, "r") as log_file:
                for line in log_file:
                    if not line.strip():
                        continue

                    line = line.rstrip("\n")
                    level = line.split("[")[1].split("]")[0]
                    entry = machine + " | " + line + "\n"
                    counts[machine][level] += 1

                    if level == "INFO":
                        info_file.write(entry)
                    elif level == "WARNING":
                        warning_file.write(entry)
                    elif level == "ERROR":
                        error_file.write(entry)

    return counts


def print_report(counts, error_file="error.log"):
    """Print the security status report."""
    print("SECURITY LOG REPORT")
    print("=" * 40)

    total_info = 0
    total_warning = 0
    total_error = 0

    for machine, levels in counts.items():
        info = levels["INFO"]
        warning = levels["WARNING"]
        error = levels["ERROR"]
        total = info + warning + error

        if error >= 2:
            status = "CRITICAL"
        elif error > 0 or warning > 0:
            status = "NEEDS ATTENTION"
        else:
            status = "OK"

        print(f"{machine}: {total} entries | INFO {info} | WARNING {warning} | ERROR {error} | Status: {status}")
        total_info += info
        total_warning += warning
        total_error += error

    total_entries = total_info + total_warning + total_error
    print("-" * 40)
    print(f"Total: {total_entries} entries | INFO {total_info} | WARNING {total_warning} | ERROR {total_error}")
    print(f"Errors (see {error_file}):")

    with open(error_file, "r") as file:
        for line in file:
            print("  " + line.rstrip("\n"))


# Problem 2: Incident Tracker

def load_incidents(csv_file):
    """Return a list of incident dictionaries read from the CSV file."""
    incidents = []

    with open(csv_file, "r") as file:
        file.readline()  # Skip the header.

        for line in file:
            if not line.strip():
                continue

            fields = line.rstrip("\n").split(",")
            incident = {
                "id": int(fields[0]),
                "machine": fields[1],
                "severity": fields[2],
                "description": fields[3]
            }
            incidents.append(incident)

    return incidents


def save_summary(incidents, json_file):
    """Save a summary as JSON and return the summary dictionary."""
    summary = {
        "total": len(incidents),
        "by_machine": {},
        "by_severity": {},
        "high_ids": []
    }

    for incident in incidents:
        machine = incident["machine"]
        severity = incident["severity"]

        if machine not in summary["by_machine"]:
            summary["by_machine"][machine] = 0
        summary["by_machine"][machine] += 1

        if severity not in summary["by_severity"]:
            summary["by_severity"][severity] = 0
        summary["by_severity"][severity] += 1

        if severity == "high":
            summary["high_ids"].append(incident["id"])

    with open(json_file, "w") as file:
        json.dump(summary, file, indent=2)

    return summary


def archive(incidents, folder):
    """Pickle all incidents and save one JSON file for each machine."""
    os.makedirs(folder, exist_ok=True)

    pickle_file = os.path.join(folder, "incidents.pkl")
    with open(pickle_file, "wb") as file:
        pickle.dump(incidents, file)

    by_machine = {}
    for incident in incidents:
        machine = incident["machine"]
        if machine not in by_machine:
            by_machine[machine] = []
        by_machine[machine].append(incident)

    for machine, machine_incidents in by_machine.items():
        json_file = os.path.join(folder, machine + ".json")
        with open(json_file, "w") as file:
            json.dump(machine_incidents, file, indent=2)

    filenames = []
    for name in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, name)):
            filenames.append(name)

    return sorted(filenames)


def load_archive(folder):
    """Return the incident list stored in folder/incidents.pkl."""
    pickle_file = os.path.join(folder, "incidents.pkl")
    with open(pickle_file, "rb") as file:
        return pickle.load(file)


# Problem 3 (Bonus): Workspace Organizer and Backup System

def organize(folder):
    """Move files into subfolders based on their extensions."""
    moved = {"logs": [], "data": [], "pickles": [], "other": []}

    for name in os.listdir(folder):
        source = os.path.join(folder, name)
        if not os.path.isfile(source):
            continue

        extension = os.path.splitext(name)[1]
        if extension == ".log":
            subfolder = "logs"
        elif extension == ".csv" or extension == ".json":
            subfolder = "data"
        elif extension == ".pkl":
            subfolder = "pickles"
        else:
            subfolder = "other"

        destination_folder = os.path.join(folder, subfolder)
        os.makedirs(destination_folder, exist_ok=True)
        destination = os.path.join(destination_folder, name)
        shutil.move(source, destination)
        moved[subfolder].append(name)

    for subfolder in moved:
        moved[subfolder].sort()

    return moved


def create_backup(source_dir, backup_root, label):
    """Copy the entire source folder into a new labeled backup folder."""
    os.makedirs(backup_root, exist_ok=True)
    backup_dir = os.path.join(backup_root, "backup_" + label)
    shutil.copytree(source_dir, backup_dir)
    return backup_dir


def verify_backup(source_dir, backup_dir):
    """Check that all source files exist in the backup with matching sizes."""
    for current_folder, subfolders, filenames in os.walk(source_dir):
        for name in filenames:
            source_file = os.path.join(current_folder, name)
            relative_path = os.path.relpath(source_file, source_dir)
            backup_file = os.path.join(backup_dir, relative_path)

            if not os.path.isfile(backup_file):
                return False
            if os.path.getsize(source_file) != os.path.getsize(backup_file):
                return False

    return True


def cleanup_old_backups(backup_root, keep):
    """Keep the newest backups and return the names of deleted backups."""
    backups = []
    for name in os.listdir(backup_root):
        path = os.path.join(backup_root, name)
        if name.startswith("backup_") and os.path.isdir(path):
            backups.append(name)

    backups.sort()
    deleted = []

    while len(backups) > keep:
        oldest = backups.pop(0)
        shutil.rmtree(os.path.join(backup_root, oldest))
        deleted.append(oldest)

    return deleted


# Assignment sample tests.
if __name__ == "__main__":
    # Keep generated sample files together in their own folder.
    os.makedirs("CS1350_HW7_demo", exist_ok=True)
    os.chdir("CS1350_HW7_demo")

    # Problem 1
    with open("server_a.log", "w") as f:
        f.write("2026-10-05 08:01:12 [INFO] User alice logged in\n")
        f.write("2026-10-05 08:03:45 [WARNING] Failed login attempt for user root\n")
        f.write("2026-10-05 08:03:59 [WARNING] Failed login attempt for user root\n")
        f.write("2026-10-05 08:04:10 [ERROR] Account root locked after repeated failures\n")
        f.write("2026-10-05 08:15:30 [INFO] Firewall rules reloaded\n")
        f.write("2026-10-05 09:02:11 [INFO] User alice logged out\n")

    with open("server_b.log", "w") as f:
        f.write("2026-10-05 08:00:05 [INFO] System boot complete\n")
        f.write("2026-10-05 08:20:41 [ERROR] Disk encryption service failed to start\n")
        f.write("2026-10-05 08:21:02 [WARNING] Unencrypted volume mounted\n")
        f.write("2026-10-05 08:45:19 [INFO] User bob logged in\n")
        f.write("2026-10-05 09:10:33 [ERROR] Unauthorized access attempt on port 22\n")
        f.write("\n")
        f.write("2026-10-05 09:30:00 [INFO] Backup completed\n")

    counts = split_logs({"server_a": "server_a.log", "server_b": "server_b.log"})
    print(counts)

    with open("warning.log", "r") as f:
        print(f.read())

    print_report(counts)

    # Problem 2
    with open("incidents.csv", "w") as f:
        f.write("id,machine,severity,description\n")
        f.write("1,server_a,high,Account root locked\n")
        f.write("2,server_b,high,Disk encryption failed\n")
        f.write("3,server_b,low,Unencrypted volume mounted\n")
        f.write("4,server_a,medium,Repeated failed logins\n")
        f.write("5,server_b,high,Unauthorized access on port 22\n")

    incidents = load_incidents("incidents.csv")
    print(len(incidents))
    print(incidents[0])

    summary = save_summary(incidents, "summary.json")
    print(summary)

    with open("summary.json", "r") as f:
        print(json.load(f) == summary)

    print(archive(incidents, "archive"))
    with open(os.path.join("archive", "server_a.json"), "r") as f:
        print([item["id"] for item in json.load(f)])

    restored = load_archive("archive")
    print(restored == incidents)

    # Problem 3: These sample folders are inside CS1350_HW7_demo.
    for old in ["workspace", "backups"]:
        if os.path.exists(old):
            shutil.rmtree(old)

    os.mkdir("workspace")
    for name in ["a.log", "b.log", "incidents.csv", "summary.json", "incidents.pkl", "notes.txt"]:
        with open(os.path.join("workspace", name), "w") as f:
            f.write(f"Test file: {name}\n")

    print(organize("workspace"))
    print(sorted(os.listdir("workspace")))

    for label in ["2026-10-01", "2026-10-02", "2026-10-03"]:
        path = create_backup("workspace", "backups", label)
        print(os.path.basename(path), verify_backup("workspace", path))

    os.remove(os.path.join("backups", "backup_2026-10-03", "logs", "a.log"))
    print(verify_backup("workspace", os.path.join("backups", "backup_2026-10-03")))
    print(cleanup_old_backups("backups", 2))
    print(sorted(os.listdir("backups")))
