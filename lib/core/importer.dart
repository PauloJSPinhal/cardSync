import 'naming.dart';

const rawExts = {'cr2', 'cr3', 'dng'};
const jpgExts = {'jpg', 'jpeg'};

String extOf(String path) => path.split('.').last.toLowerCase();

String? classify(String path, {bool treated = false}) {
  final e = extOf(path);
  if (rawExts.contains(e)) return '01_RAW';
  if (jpgExts.contains(e)) return treated ? '03_Tratadas' : '02_JPG_Original';
  return null;
}

Map<String, Map<String, List<String>>> groupFiles(
  List<String> paths,
  String event,
  String location, {
  DateTime? targetDate,
  bool treated = false,
}) {
  final result = <String, Map<String, List<String>>>{};
  for (final p in paths) {
    final sub = classify(p, treated: treated);
    if (sub == null) continue;
    final d = targetDate ?? DateTime.now();
    final root = folderName(d, event, location);
    result.putIfAbsent(root, () => {});
    result[root]!.putIfAbsent(sub, () => []);
    result[root]![sub]!.add(p);
  }
  return result;
}