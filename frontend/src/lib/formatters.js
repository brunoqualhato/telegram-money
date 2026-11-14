const BRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});
export const money = (value) => BRL.format(Number(value || 0));
export const percentage = (value) =>
  `${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
export const pct = (value) =>
  `${Number(value) >= 0 ? "+" : ""}${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 2, minimumFractionDigits: 2 })}%`;
export const date = (value) =>
  value
    ? new Date(
        value.length === 10
          ? `${value}T12:00:00`
          : /Z$|[+-]\d\d:\d\d$/.test(value)
            ? value
            : `${value}Z`,
      ).toLocaleString("pt-BR", {
        day: "2-digit",
        month: "short",
        hour: value.length === 10 ? undefined : "2-digit",
        minute: value.length === 10 ? undefined : "2-digit",
      })
    : "Não informado";
