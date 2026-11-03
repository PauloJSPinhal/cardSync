String sanitize(String text) {
  text = text.trim();
  text = text.replaceAll(RegExp(r'[^\w\s\-]', unicode: true), '');
  text = text.replaceAll(RegExp(r'\s+'), '-');
  text = text.replaceAll(RegExp(r'-+'), '-');
  text = text.replaceAll(RegExp(r'^[-_]+|[-_]+$'), '');
  return text;
}

String formatDateYyyymmdd(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}${d.month.toString().padLeft(2, '0')}${d.day.toString().padLeft(2, '0')}';

String folderName(DateTime date, String event, String location) {
  return '${formatDateYyyymmdd(date)}_${sanitize(event)}_${sanitize(location)}';
}

String displayTitle(DateTime date, String event, String location) {
  return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year} — ${event.trim()}, ${location.trim()}';
}

String projectId(DateTime date, String event) {
  final d = formatDateYyyymmdd(date);
  final ev = sanitize(event).toLowerCase().replaceAll('-', '_');
  return 'proj_${d}_$ev';
}