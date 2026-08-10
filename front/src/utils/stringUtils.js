export function cleanHtml(text) {
  if (!text) return '';

  let clean = text.replace(/<br\s*\/?>/gi, '\n');
  
  clean = clean.replace(/<[^>]*>/g, '');
  
  clean = clean.replace(/\s+/g, ' ').trim();
  
  return clean;
}