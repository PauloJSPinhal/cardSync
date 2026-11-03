import 'dart:io';
import 'package:crypto/crypto.dart';

String md5File(String path) {
  final bytes = File(path).readAsBytesSync();
  return md5.convert(bytes).toString();
}

String md5Bytes(List<int> bytes) => md5.convert(bytes).toString();

int fileSize(String path) => File(path).lengthSync();