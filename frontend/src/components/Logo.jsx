import { TrendingUp } from "lucide-react";

export default function Logo() {
  return (
    <div className="logo">
      <span className="logo-mark">
        <TrendingUp size={22} />
      </span>
      <span>
        telegram<span className="logo-light">money</span>
        <small>SEU RADAR DE INVESTIMENTOS</small>
      </span>
    </div>
  );
}
