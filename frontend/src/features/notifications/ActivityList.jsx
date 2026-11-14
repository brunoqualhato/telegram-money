import { Bell, Sparkles, Landmark } from "lucide-react";
import Badge from "../../components/ui/Badge.jsx";
import Empty from "../../components/ui/Empty.jsx";
import Button from "../../components/ui/Button.jsx";
import { date } from "../../lib/formatters.js";
import { STATUS } from "../../lib/constants.js";

export default function ActivityList({ items, all = false, retry }) {
  return items.length ? (
    <div className="activity-list">
      {items.map((item) => (
        <div className="activity-item" key={item.id}>
          <span className={`activity-icon ${item.category}`}>
            {item.category === "event" ? (
              <Landmark size={17} />
            ) : item.category === "ai" ? (
              <Sparkles size={17} />
            ) : (
              <Bell size={17} />
            )}
          </span>
          <div className="activity-text">
            <div className="activity-title">
              <strong>{item.title}</strong>
              <Badge
                tone={
                  { sent: "green", failed: "red", uncertain: "red" }[
                    item.status
                  ] || ""
                }
              >
                {STATUS[item.status] || item.status}
              </Badge>
            </div>
            <small>
              {item.ticker || "Sua carteira"} · {date(item.created_at)}
            </small>
            {all && (
              <>
                <p className="pre-wrap">{item.body}</p>
                {item.error && <div className="inline-error">{item.error}</div>}
                {["failed", "uncertain"].includes(item.status) && (
                  <Button secondary small onClick={() => retry(item)}>
                    Reenviar manualmente
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  ) : (
    <Empty icon={Bell} title="Tudo tranquilo por aqui">
      Os eventos detectados e as entregas aparecerão neste histórico.
    </Empty>
  );
}
