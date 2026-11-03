import 'dart:io';
import 'package:googleapis/drive/v3.dart' as drive;
import 'auth_service.dart';

class DriveService {
  static final DriveService instance = DriveService._();
  DriveService._();

  drive.DriveApi? _api;

  Future<bool> init() async {
    final client = await AuthService.instance.authenticatedClient();
    if (client == null) return false;
    _api = drive.DriveApi(client);
    return true;
  }

  drive.DriveApi get api {
    if (_api == null) throw StateError('Drive não inicializado');
    return _api!;
  }

  bool get isReady => _api != null;

  Future<Map<String, dynamic>?> about() async {
    try {
      final a = await api.about.get($fields: 'storageQuota');
      final q = a.storageQuota;
      return {
        'used': int.tryParse(q?.usage ?? '0') ?? 0,
        'total': int.tryParse(q?.limit ?? '0') ?? 0,
      };
    } catch (_) {
      return null;
    }
  }

  Future<String?> findFolder(String name, {String? parentId}) async {
    try {
      final q = parentId == null
          ? "name = '$name' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
          : "'$parentId' in parents and name = '$name' and mimeType = 'application/vnd.google-apps.folder' and trashed = false";
      final res = await api.files.list(q: q, $fields: 'files(id,name)');
      final files = res.files;
      if (files != null && files.isNotEmpty) return files.first.id;
    } catch (_) {}
    return null;
  }

  Future<String> createFolder(String name, {String? parentId}) async {
    final meta = drive.File()
      ..name = name
      ..mimeType = 'application/vnd.google-apps.folder';
    if (parentId != null) meta.parents = [parentId];
    final res = await api.files.create(meta, $fields: 'id');
    return res.id!;
  }

  Future<Map<String, String>> ensureStructure(String rootName, {String? parentId}) async {
    String? root = await findFolder(rootName, parentId: parentId);
    root ??= await createFolder(rootName, parentId: parentId);
    final ids = <String, String>{'root': root};
    for (final sub in ['01_RAW', '02_JPG_Original', '03_Tratadas', '04_Docs']) {
      String? sid = await findFolder(sub, parentId: root);
      sid ??= await createFolder(sub, parentId: root);
      ids[sub] = sid;
    }
    return ids;
  }

  Future<List<drive.File>> listFiles(String folderId) async {
    final out = <drive.File>[];
    String? pageToken;
    do {
      final res = await api.files.list(
        q: "'$folderId' in parents and trashed = false and mimeType != 'application/vnd.google-apps.folder'",
        $fields: 'nextPageToken, files(id,name,size,md5Checksum)',
        pageToken: pageToken,
      );
      if (res.files != null) out.addAll(res.files!);
      pageToken = res.nextPageToken;
    } while (pageToken != null);
    return out;
  }

  Future<String> uploadFile(String localPath, String folderId, {String? filename}) async {
    final name = filename ?? localPath.split(Platform.pathSeparator).last;
    final file = File(localPath);
    final media = drive.Media(file.openRead(), await file.length());
    final meta = drive.File()..name = name..parents = [folderId];
    final res = await api.files.create(meta, uploadMedia: media, $fields: 'id');
    return res.id!;
  }

  Future<void> createPermission(String fileId, String email) async {
    final perm = drive.Permission()
      ..type = 'user'
      ..role = 'reader'
      ..emailAddress = email;
    await api.permissions.create(perm, fileId);
  }

  String folderUrl(String id) => 'https://drive.google.com/drive/folders/$id';
}