import 'dart:convert';

const subfolders = ['01_RAW', '02_JPG_Original', '03_Tratadas', '04_Docs'];

Map<String, dynamic> newManifest(String projectId, String folderName, String displayTitle) {
  final now = DateTime.now().toUtc().toIso8601String();
  return {
    'schema_version': '1.0',
    'project_id': projectId,
    'folder_name': folderName,
    'display_title': displayTitle,
    'status': 'active',
    'created_at': now,
    'updated_at': now,
    'drive_ids': {
      'root_folder_id': null,
      'raw_folder_id': null,
      'jpg_folder_id': null,
      'treated_folder_id': null,
      'docs_folder_id': null,
    },
    'shared_with': <Map<String, dynamic>>[],
    'files_manifest': <Map<String, dynamic>>[],
  };
}

void addFileEntry(Map<String, dynamic> manifest, String filename, String type,
    int sizeBytes, String md5, String? shotDate) {
  final list = manifest['files_manifest'] as List;
  for (final e in list) {
    if (e['filename'] == filename && e['md5'] == md5) return;
  }
  list.add({
    'filename': filename,
    'type': type,
    'size_bytes': sizeBytes,
    'md5': md5,
    'shot_date': shotDate,
    'uploaded_at': DateTime.now().toUtc().toIso8601String(),
  });
}

void setManifestStatus(Map<String, dynamic> manifest, String status) {
  manifest['status'] = status;
  manifest['updated_at'] = DateTime.now().toUtc().toIso8601String();
}

String manifestToJson(Map<String, dynamic> m) => const JsonEncoder.withIndent('  ').convert(m);
Map<String, dynamic> manifestFromJson(String s) => jsonDecode(s) as Map<String, dynamic>;