import {
  Bell,
  Clock3,
  FileText,
  LayoutDashboard,
  Sparkles,
  Wallet,
  Landmark,
} from "lucide-react";

export const CLASSES = {
  acao: "Ação",
  fii: "FII",
  etf: "ETF",
  bdr: "BDR",
  indice: "Índice",
  cripto: "Cripto",
  moeda: "Moeda",
};
export const RULES = {
  price_above: "Preço acima de",
  price_below: "Preço abaixo de",
  change_up: "Alta no dia acima de",
  change_down: "Queda no dia acima de",
  high_52w: "Máxima de 52 semanas",
  low_52w: "Mínima de 52 semanas",
  abnormal: "Oscilação absoluta no dia",
};
export const STATUS = {
  pending: "Na fila",
  sent: "Enviado",
  retry: "Nova tentativa",
  failed: "Falhou",
  uncertain: "Entrega incerta",
  sending: "Enviando",
  demo: "Exemplo",
  expired: "Expirado",
};
export const NAV = [
  ["overview", "Visão geral", LayoutDashboard],
  ["assets", "Meus ativos", Wallet],
  ["alerts", "Meus alertas", Bell],
  ["events", "Proventos", Landmark],
  ["documents", "Documentos e IA", Sparkles],
  ["reports", "Relatórios", FileText],
  ["history", "Histórico de alertas", Clock3],
];
