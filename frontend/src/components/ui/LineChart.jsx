import { useId, useState } from "react";
import { chartGeometry } from "../../lib/chartGeometry.js";
import { date, money } from "../../lib/formatters.js";

const compact = new Intl.NumberFormat("pt-BR", {
  notation: "compact",
  maximumFractionDigits: 1,
});

function ChartAxes({ ticks, referenceY, referenceLabel }) {
  return (
    <g className="chart-axis">
      {ticks.map((tick, index) => (
        <g key={index}>
          <line x1="80" x2="736" y1={tick.y} y2={tick.y} />
          <text x="66" y={tick.y + 4} textAnchor="end">
            {compact.format(tick.value)}
          </text>
        </g>
      ))}
      {referenceY !== null && (
        <g className="chart-reference">
          <line x1="80" x2="736" y1={referenceY} y2={referenceY} />
          <title>{referenceLabel}</title>
        </g>
      )}
    </g>
  );
}

export default function LineChart({
  rows,
  label,
  reference,
  referenceLabel,
  negative = false,
  formatValue = money,
}) {
  const gradient = useId();
  const [selected, setSelected] = useState(null);
  const chart = chartGeometry(rows, reference);
  const index = Math.min(selected ?? rows.length - 1, rows.length - 1);
  const active = chart.points[index];
  const color = negative ? "#b45d50" : "#356b50";

  function inspect(event) {
    const box = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - box.left) / box.width) * 760;
    let nearest = 0;
    chart.points.forEach((point, i) => {
      if (Math.abs(point.x - x) < Math.abs(chart.points[nearest].x - x))
        nearest = i;
    });
    setSelected(nearest);
  }

  return (
    <div className="line-chart">
      <div className="chart-inspector">
        <span>{date(active.date)}</span>
        <strong>{formatValue(active.value)}</strong>
      </div>
      <svg
        viewBox="0 0 760 228"
        role="img"
        aria-label={label}
        onPointerMove={inspect}
      >
        <defs>
          <linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity=".2" />
            <stop offset="100%" stopColor={color} stopOpacity="0.01" />
          </linearGradient>
        </defs>
        <ChartAxes
          ticks={chart.ticks}
          referenceY={chart.referenceY}
          referenceLabel={referenceLabel}
        />
        <polygon
          points={`80,200 ${chart.line} 736,200`}
          fill={`url(#${gradient})`}
        />
        <polyline
          points={chart.line}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
        <line
          x1={active.x}
          x2={active.x}
          y1="20"
          y2="200"
          className="chart-crosshair"
        />
        <circle
          cx={active.x}
          cy={active.y}
          r="5"
          fill={color}
          stroke="white"
          strokeWidth="3"
        />
        <text x="80" y="224" className="chart-date">
          {date(rows[0].date)}
        </text>
        <text x="736" y="224" textAnchor="end" className="chart-date">
          {date(rows.at(-1).date)}
        </text>
      </svg>
      <input
        type="range"
        min="0"
        max={rows.length - 1}
        value={index}
        onChange={(event) => setSelected(Number(event.target.value))}
        aria-label={`Explorar ${label.toLowerCase()}`}
        aria-valuetext={`${date(active.date)}: ${formatValue(active.value)}`}
      />
      {Number.isFinite(reference) && (
        <div className="chart-key">
          <i />
          {referenceLabel}: {formatValue(reference)}
        </div>
      )}
    </div>
  );
}
