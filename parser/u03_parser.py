# u03_parser.py
# 픽업 / 에러 / 부품 단위 요약

def parse_pickup_error_summary(lines: list[str]) -> dict:
    result = {}

    for line in lines:
        line = line.strip()

        if line.startswith("Total Pickup Count"):
            result["total_pickup_count"] = int(line.split()[-1])
        elif line.startswith("Total Error Count"):
            result["total_error_count"] = int(line.split()[-1])
        elif line.startswith("Pickup Error Count"):
            result["pickup_error_count"] = int(line.split()[-1])
        elif line.startswith("Recognition Error Count"):
            result["recognition_error_count"] = int(line.split()[-1])

    return result
