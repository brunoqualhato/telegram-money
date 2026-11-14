import { money } from "../../lib/formatters.js";

function ResultBar({ item, maximum }) {
  const width = (Math.abs(item.value) / maximum) * 50;
  const tone = item.value < 0 ? "negative" : "positive";
  return (
    <li>
      <span className="bar-ticker">{item.label}</span>
      <div className="diverging-track" aria-hidden="true">
        <span
          className={tone}
          style={{
            width: `${width}%`,
            left: `${item.value < 0 ? 50 - width : 50}%`,
          }}
        />
      </div>
      <span className="bar-result">
        <strong className={item.value === 0 ? "muted" : tone}>
          {money(item.value)}
        </strong>
        <small>{item.detail}</small>
      </span>
    </li>
  );
}

export default function DivergingBars({ items }) {
  const maximum = Math.max(...items.map((item) => Math.abs(item.value)), 1);
  return (
    <ul className="diverging-bars">
      {items.map((item) => (
        <ResultBar key={item.id} item={item} maximum={maximum} />
      ))}
    </ul>
  );
}
