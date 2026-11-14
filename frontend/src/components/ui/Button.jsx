export default function Button({
  children,
  icon: Icon,
  secondary,
  small,
  ...props
}) {
  return (
    <button
      className={`${secondary ? "button-secondary" : "button"} ${small ? "small" : ""}`}
      {...props}
    >
      {Icon && <Icon size={16} />} {children}
    </button>
  );
}
