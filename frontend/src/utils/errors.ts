/**
 * Safely extracts a human-readable error message from an API error response.
 *
 * FastAPI/Pydantic request validation errors return `detail` as an ARRAY of
 * objects shaped like:
 *   { type, loc, msg, input, ctx }
 *
 * Other backend errors (e.g. `raise HTTPException(detail="Farmer not found")`)
 * return `detail` as a plain string.
 *
 * Rendering `detail` directly in JSX (e.g. `<div>{error}</div>`) works for the
 * string case but crashes React ("Objects are not valid as a React child")
 * when `detail` is an array/object, which is exactly what happens on a 422.
 * This helper normalizes both shapes into a single safe string so it is
 * always safe to render.
 */
export function getApiErrorMessage(err: any, fallback = 'Something went wrong'): string {
  const detail = err?.response?.data?.detail;

  if (!detail) {
    return (typeof err?.message === 'string' && err.message) || fallback;
  }

  // Simple case: raise HTTPException(status_code=..., detail="some string")
  if (typeof detail === 'string') {
    return detail;
  }

  // FastAPI/Pydantic validation errors: array of { type, loc, msg, input, ctx }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && typeof item.msg === 'string') {
          const loc = Array.isArray(item.loc) ? item.loc : [];
          // Last non-"body" segment of loc is usually the field name.
          const field = [...loc].reverse().find((segment) => segment !== 'body');
          return field !== undefined ? `${field}: ${item.msg}` : item.msg;
        }
        return null;
      })
      .filter((msg): msg is string => Boolean(msg));

    return messages.length > 0 ? messages.join(', ') : fallback;
  }

  // Rare case: a single validation-error-shaped object, not wrapped in an array.
  if (typeof detail === 'object' && typeof detail.msg === 'string') {
    return detail.msg;
  }

  return fallback;
}