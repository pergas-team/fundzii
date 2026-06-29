export function resolveFileUrl(url?: string | null) {
  if (!url) return "#";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/backend/")) return url;
  return `/backend${url.startsWith("/") ? url : `/${url}`}`;
}
