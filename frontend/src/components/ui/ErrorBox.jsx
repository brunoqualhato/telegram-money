import { AlertCircle } from "lucide-react";

export default function ErrorBox({ error }) {
  return error ? (
    <div className="error-box" role="alert">
      <AlertCircle size={17} />
      {error}
    </div>
  ) : null;
}
