export default function Field({ label, children, note }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {note && <small>{note}</small>}
    </label>
  );
}
