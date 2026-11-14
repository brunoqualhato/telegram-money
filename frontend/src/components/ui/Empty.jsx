import { Layers } from "lucide-react";

export default function Empty({
  icon: Icon = Layers,
  title,
  children,
  action,
}) {
  return (
    <div className="empty">
      <span>
        <Icon size={25} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}
