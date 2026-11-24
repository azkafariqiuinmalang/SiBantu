"""Perhitungan deterministik untuk satu ronde penilaian."""

from fractions import Fraction
from math import isfinite, sqrt

CR_LIMIT = 0.10
TOLERANCE = 1e-12
VERSION = "2.0"
SUPPORTED_VERSIONS = ("1.0", VERSION)
CRITERIA = (
    ("C1", "Jumlah pengungsi", "orang", "benefit"),
    ("C2", "Kerusakan hunian", "skor 1–5", "benefit"),
    ("C3", "Pengungsi kelompok rentan", "%", "benefit"),
    ("C4", "Gangguan layanan dasar", "skor 1–5", "benefit"),
    ("C5", "Kecukupan logistik lokal", "%", "cost"),
    ("C6", "Jarak posko induk ke titik gempa", "km", "benefit"),
)
LEGACY_CRITERIA = CRITERIA[:5] + (("C6", "Waktu sejak bantuan terakhir", "jam", "benefit"),)


def criteria_for_version(version):
    return CRITERIA if version == VERSION else LEGACY_CRITERIA
PAIRS = [(i, j) for i in range(6) for j in range(i + 1, 6)]
SCALE = [str(Fraction(1, n)) for n in range(9, 1, -1)] + [str(n) for n in range(1, 10)]


def ahp(comparisons):
    if len(comparisons) != len(PAIRS) or any(value not in SCALE for value in comparisons):
        raise ValueError("Lengkapi 15 perbandingan menggunakan skala Saaty.")
    n = len(CRITERIA)
    matrix = [[1.0] * n for _ in range(n)]
    for (i, j), choice in zip(PAIRS, comparisons):
        matrix[i][j] = float(Fraction(choice))
        matrix[j][i] = 1 / matrix[i][j]

    def multiply(weights):
        return [sum(value * weight for value, weight in zip(row, weights)) for row in matrix]

    weights = [1 / n] * n
    for _ in range(1000):
        product = multiply(weights)
        updated = [value / sum(product) for value in product]
        delta = max(abs(a - b) for a, b in zip(updated, weights))
        weights = updated
        if delta < TOLERANCE:
            break
    else:
        raise ValueError("Perhitungan AHP belum konvergen. Periksa kembali perbandingan.")
    lambda_max = sum(value / weight for value, weight in zip(multiply(weights), weights)) / n
    ci = max(0.0, (lambda_max - n) / (n - 1))
    cr = ci / 1.24
    return dict(matrix=matrix, weights=weights, lambda_max=lambda_max, ci=ci,
                cr=cr, valid=cr <= CR_LIMIT + TOLERANCE)


def field_criterion_values(total, vulnerable, housing, services, stock, required, distance):
    return [total, housing, vulnerable / total * 100 if total else 0,
            services, 100 if stock >= required else stock / required * 100, distance]


def demo_snapshot(seed):
    if not seed.get("districts"):
        raise ValueError("Ronde memerlukan minimal dua kecamatan.")
    version = seed.get("criteria_version", VERSION if "distance_to_epicenter_km" in seed["districts"][0] else "1.0")
    districts = []
    for item in seed["districts"]:
        total = item["evacuees"]
        vulnerable = item["vulnerable_people"]
        housing = item["housing_damage_score"]
        services = item["essential_services_disruption_score"]
        stock = item["available_package_equivalents"]
        required = item["required_package_equivalents"]
        distance = item["distance_to_epicenter_km"] if version == VERSION else item["hours_since_last_delivery"]
        if not (isinstance(total, int) and isinstance(vulnerable, int) and 0 <= vulnerable <= total
                and housing in range(1, 6) and services in range(1, 6)
                and all(isfinite(value) for value in (stock, required, distance))
                and stock >= 0 and required > 0 and distance >= 0):
            raise ValueError(f"Data simulasi {item['code']} tidak valid.")
        values = field_criterion_values(total, vulnerable, housing, services, stock, required, distance)
        districts.append(dict(code=item["code"], name=item["name"], values=values))
    if len(districts) < 2 or len({item["code"] for item in districts}) != len(districts):
        raise ValueError("Ronde memerlukan minimal dua kode kecamatan unik.")
    return dict(name=seed["name"], source=seed["information_source"],criteria_version=version,
                criteria=list(criteria_for_version(version)),
                incident_at=seed["incident_at"], districts=districts)


def topsis(districts, weights):
    columns = list(zip(*(item["values"] for item in districts)))
    norms = [sqrt(sum(value ** 2 for value in column)) for column in columns]
    normalized = [[value / norm if norm else 0.0 for value, norm in zip(item["values"], norms)]
                  for item in districts]
    weighted = [[value * weight for value, weight in zip(row, weights)] for row in normalized]
    best, worst = [], []
    for criterion, column in zip(CRITERIA, zip(*weighted)):
        low, high = min(column), max(column)
        if criterion[3] == "cost":
            best.append(low)
            worst.append(high)
        else:
            best.append(high)
            worst.append(low)
    rows = []
    for item, row, normal in zip(districts, weighted, normalized):
        positive = sqrt(sum((a - b) ** 2 for a, b in zip(row, best)))
        negative = sqrt(sum((a - b) ** 2 for a, b in zip(row, worst)))
        score = negative / (positive + negative) if positive + negative else 0.5
        rows.append(dict(code=item["code"], name=item["name"], positive=positive,
                         negative=negative, score=score, normalized=normal, weighted=row))
    rows.sort(key=lambda row: -row["score"])
    ordered = []
    while rows:
        end = 1
        while end < len(rows) and rows[0]["score"] - rows[end]["score"] <= TOLERANCE:
            end += 1
        for row in sorted(rows[:end], key=lambda row: row["code"]):
            ordered.append(dict(row, tied=end > 1, rank=len(ordered) + 1))
        rows = rows[end:]
    return dict(rows=ordered, best=best, worst=worst, norms=norms,
                zero_columns=[criterion[0] for criterion, norm in zip(CRITERIA, norms) if not norm],
                identical=best == worst)


def borda(districts, rankings):
    codes = {item["code"] for item in districts}
    if len(rankings) != 3 or any(len(order) != len(codes) or set(order) != codes for order in rankings):
        raise ValueError("Borda membutuhkan tiga ranking lengkap dari ronde yang sama.")
    positions = [{code: rank for rank, code in enumerate(order, 1)} for order in rankings]
    rows = []
    for item in districts:
        code = item["code"]
        points = [len(codes) - position[code] + 1 for position in positions]
        rows.append(dict(code=code, name=item["name"], points=points,
                         total=sum(points), head_rank=positions[0][code]))
    rows.sort(key=lambda row: (-row["total"], row["head_rank"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        row["tied"] = sum(other["total"] == row["total"] for other in rows) > 1
    return rows
