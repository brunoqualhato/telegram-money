export function chartGeometry(rows, reference) {
  const values = rows.map((row) => row.value);
  const bounds = Number.isFinite(reference) ? [...values, reference] : values;
  const low = Math.min(...bounds);
  const high = Math.max(...bounds);
  const padding = (high - low || Math.abs(high) || 1) * 0.15;
  const min = low - padding;
  const max = high + padding;
  const y = (value) => 20 + ((max - value) / (max - min)) * 180;
  const first = new Date(rows[0].date).getTime();
  const span = new Date(rows.at(-1).date).getTime() - first || 1;
  const points = rows.map((row) => ({
    ...row,
    x: 80 + ((new Date(row.date).getTime() - first) / span) * 656,
    y: y(row.value),
  }));
  return {
    points,
    line: points.map((point) => `${point.x},${point.y}`).join(" "),
    ticks: [max, (min + max) / 2, min].map((value) => ({ value, y: y(value) })),
    referenceY: Number.isFinite(reference) ? y(reference) : null,
  };
}
