export default function IconButton({ label, children, ...props }) {
  return (
    <button title={label} aria-label={label} className="icon-button" {...props}>
      {children}
    </button>
  );
}
