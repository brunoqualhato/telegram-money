export async function api(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
    body: options.body && !isForm ? JSON.stringify(options.body) : options.body,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((x) => `${x.loc?.at(-1)}: ${x.msg}`).join("; ")
      : body.detail;
    const error = new Error(detail || "Não foi possível completar a operação.");
    error.status = response.status;
    throw error;
  }
  return body;
}
