import { Bell } from "lucide-react";
import Button from "../../components/ui/Button.jsx";
import Field from "../../components/ui/Field.jsx";
import ErrorBox from "../../components/ui/ErrorBox.jsx";
import ProfileForm from "./ProfileForm.jsx";

export default function PreferencesSettings({
  me,
  error,
  save,
  busy,
  reload,
  toast,
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Do seu jeito</h3>
          <p>Controle o ritmo das suas notificações.</p>
        </div>
        <Bell size={20} />
      </div>
      <div className="panel-body">
        <form onSubmit={save}>
          {[
            ["notifications_enabled", "Receber notificações automáticas"],
            ["event_alerts", "Proventos, eventos e lembretes de datas"],
            ["daily_report", "Fechamento diário · após 18h em dias úteis"],
            ["weekly_report", "Resumo semanal · sexta-feira após 18h"],
            ["monthly_report", "Resumo mensal · primeiro dia útil após 18h"],
          ].map(([key, label]) => (
            <label className="check-field" key={key}>
              <input name={key} type="checkbox" defaultChecked={me?.[key]} />
              <span>{label}</span>
            </label>
          ))}
          <div className="form-grid">
            <Field label="Silêncio a partir de (hora)">
              <input
                name="quiet_start"
                type="number"
                min="0"
                max="23"
                defaultValue={me?.quiet_start}
              />
            </Field>
            <Field label="Retomar a partir de (hora)">
              <input
                name="quiet_end"
                type="number"
                min="0"
                max="23"
                defaultValue={me?.quiet_end}
              />
            </Field>
          </div>
          <Field label="Fuso horário">
            <input name="timezone" defaultValue={me?.timezone} />
          </Field>
          <Field label="Máximo de alertas automáticos por hora">
            <input
              name="max_per_hour"
              type="number"
              min="1"
              max="100"
              defaultValue={me?.max_per_hour}
            />
          </Field>
          <p className="form-note">
            Horários iguais desativam o silêncio. Mensagens ficam na fila
            durante a pausa. Dias úteis consideram segunda a sexta, sem
            calendário de feriados da B3.
          </p>
          <ErrorBox error={error} />
          <Button disabled={busy}>
            {busy ? "Salvando…" : "Salvar preferências"}
          </Button>
        </form>
        <ProfileForm me={me} reload={reload} toast={toast} />
      </div>
    </section>
  );
}
