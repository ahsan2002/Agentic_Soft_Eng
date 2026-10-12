
import json
import urllib.request
import urllib.error
from datetime import datetime

REQUIREMENTS_FILE = "requirements.txt"
PYPI_URL = "https://pypi.org/pypi/{}/json"


def get_pypi_data(package, version=None):
    if version:
        url = f"https://pypi.org/pypi/{package}/{version}/json"
    else:
        url = PYPI_URL.format(package)

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PyPI-Dependency-Checker/1.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    except urllib.error.URLError as error:
        print(f"Network error checking {package}: {error}")
        return None


def main():
    with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as file:
        lines = [
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        ]

    checked = len(lines)
    packages_not_found = 0
    versions_not_found = 0
    valid_releases = []

    for line in lines:
        # Handle package==version entries
        if "==" not in line:
            print(f"Skipping unsupported requirement format: {line}")
            continue

        package, version = map(str.strip, line.split("==", 1))

        # Check whether the package exists on PyPI
        package_data = get_pypi_data(package)

        if package_data is None:
            packages_not_found += 1
            print(f"Package not on PyPI: {package}")
            continue

        # Check whether the pinned version exists
        version_data = get_pypi_data(package, version)

        if version_data is None:
            versions_not_found += 1
            print(f"Version not on PyPI: {package}=={version}")
            continue

        # Find the first file's upload time for this release
        urls = version_data.get("urls", [])

        if urls and urls[0].get("upload_time"):
            upload_time = urls[0]["upload_time"]
            release_date = datetime.fromisoformat(
                upload_time.replace("Z", "+00:00")
            )
            valid_releases.append(
                (release_date, package, version)
            )

    print(f"\ndependencies checked: {checked}")
    print(f"packages not on pypi: {packages_not_found}")
    print(f"versions not on pypi: {versions_not_found}")

    if valid_releases:
        oldest = min(valid_releases, key=lambda item: item[0])
        print(
            f"oldest pinned release: "
            f"{oldest[1]}=={oldest[2]} ({oldest[0].year})"
        )
    else:
        print("oldest pinned release: None")


if __name__ == "__main__":
    main()
