export default function DocumentSummary({ summary }) {
  return (
    <div className="summary">
      <h4>Fatos extraídos</h4>
      {summary.facts.map((fact, i) => (
        <div key={i}>
          <p>{fact.fact}</p>
          <blockquote>{fact.evidence}</blockquote>
        </div>
      ))}
      {summary.risks?.length > 0 && (
        <>
          <h4>Riscos mencionados</h4>
          {summary.risks.map((item, i) => (
            <div key={i}>
              <p>{item.fact}</p>
              <blockquote>{item.evidence}</blockquote>
            </div>
          ))}
        </>
      )}
      {summary.interpretations?.length > 0 && (
        <>
          <h4>Interpretações da IA</h4>
          {summary.interpretations.map((item, i) => (
            <p key={i}>{item}</p>
          ))}
        </>
      )}
      {summary.missing?.length > 0 && (
        <>
          <h4>Informações ausentes</h4>
          <p>{summary.missing.join(" · ")}</p>
        </>
      )}
      {summary.incomplete && (
        <div className="notice">
          Documento ou contexto incompleto. A análise pode omitir informações.
        </div>
      )}
      <p className="muted">
        Texto gerado por IA. Trechos são verificados literalmente; isso não
        garante que a interpretação esteja correta.
      </p>
    </div>
  );
}
